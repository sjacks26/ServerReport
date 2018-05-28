"""
This script monitors a number of core system attributes and checks the status of given processes.
System attributes monitored:
    CPU usage (%)
    RAM usage (%)
    Hard drive usage (amount free and % used)
    Boot drive usage (%)
    Mongo server

The script sends this information in an email to specified users.

"""

import psutil as p
import datetime
import subprocess
from email.message import EmailMessage
import os
import pandas as pd
import time
import smtplib
import numpy as np
import pymongo

import config as cfg

warning_flags = {
    'CPU': 0,
    'RAM': 0,
    'Hard drive space': 0,
    'Boot drive space': 0,
    'Mongo': 0
}
process_flags = {}
for process_to_watch in cfg.processes_to_monitor:
    process_flags[process_to_watch] = 0


def convert_byte_to( n , from_unit, to , block_size=1024 ):
    """
    This function converts filesize between different units. By default, it assumes that 1MB = 1024KB.
    Modified from https://github.com/mlibre/byte_to_humanity/blob/master/byte_to_humanity/bth.py.
        The mods let this transform units of any type into specified units.
	"""
    table = {'b': 1, 'k': 2 , 'm': 3 , 'g': 4 , 't': 5 , 'p': 6}
    number = float(n)
    change_factor = table[to] - table[from_unit]
    number /= (block_size ** change_factor)
    return number


def check_cpu():
    """
    This function checks the CPU usage, returning a percentage (rounded to two decimal points) of CPU used.
    That percentage is calculated by subtracting the idle percentage from 100.
    """
    usage = p.cpu_times_percent()
    time.sleep(3)                               # Something weird is happening here. The first time cpu_times_percent runs
    usage = p.cpu_times_percent()               # it uses 100% of the cpu. Running the second time, it uses a trivial amount
    CPU_usage = str(round(100 - usage.idle, 2)) # of cpu. So we want the results from the second run.
    return CPU_usage


def check_ram():
    """
    This function checks the RAM usage, returning a percentage (rounded to two decimal points) of RAM used.
    That percentage is calculated by subtracting the available percentage from 100.
    """
    usage = p.virtual_memory()
    RAM_usage = str(round(100 - usage.percent, 2))
    return RAM_usage


def check_hard_drive(start_dir=cfg.root_dir):
    """
    This function checks the hard drive usage.
    It returns a dictionary containing the amount of free space (in human readable form) and the percentage of the disk
     used.

    By default, the function checks the disk usage of the main partition of the drive.
    """
    usage = p.disk_usage(start_dir)
    hard_drive_free_space = round(convert_byte_to(usage.free, from_unit='b', to='g'),2)
    hard_drive_usage_percent = round(usage.percent, 2)
    hard_drive_stats = {'free_space': str(hard_drive_free_space) + "G", 'percent_used': str(hard_drive_usage_percent)}
    return hard_drive_stats


def check_boot_drive(boot_drive=cfg.boot_drive):
    """
    This function checks the boot drive usage, returning a percentage of the boot drive space used.
    """
    boot_drive_usage = str(p.disk_usage(boot_drive).percent)
    return boot_drive_usage


def check_process_status(process_list=cfg.processes_to_monitor):
    """
    This function checks to see if a process (or processes) is running.
    When running the function, you can give it a list of processes to check or a single process.

    For each process provided, this function gets lines from "ps -ef" that match the process.

    It returns a dictionary structured as process: ps -ef | grep process.

    If a process isn't running, it triggers a function to send a warning email.
    """
    if type(process_list) is str:
        process_list = [process_list]
    processes_info = {}
    broken_processes = []
    processes_to_email = []
    for process in process_list:
        time = str(datetime.datetime.now().replace(microsecond=0).isoformat().split('T')[1])
        process_info = ''
        process_status = subprocess.getoutput('ps -ef | grep "{}"'.format(process)).split('\n')
        process_status = [x for x in process_status if not "grep" in x]
        process_status = [x.split() for x in process_status]
        process_pids = [int(x[1]) for x in process_status]
        if process_status:
            if len(process_pids) > 1:
                process_info = 'Ambiguous process name: {}'.format(process)
            else:
                pid = process_pids[0]
                info = p.Process(pid).as_dict(attrs=['create_time','memory_info','memory_percent','username','cpu_percent'])
                info['create_time'] = datetime.datetime.utcfromtimestamp(info['create_time']).replace(microsecond=0).isoformat()
                info['memory_info'] = str(round(convert_byte_to(info['memory_info'].rss, from_unit='b', to='g'), 2)) + "G"
                info['memory_percent'] = str(round(info['memory_percent'], 2))
                info['cpu_percent'] = str(round(info['cpu_percent'], 2))
                info['report_time'] = time
                process_info = info
                process_flags[process] = 0
        else:
            if process_flags[process] == 0:
                processes_to_email.append(process)
                process_flags[process] = 1
            broken_processes.append(process)
            process_info = [time, 'Process not running','','','','','']
        processes_info[process] = process_info
    if broken_processes:
        log('BROKEN PROCESS(ES): {}'.format(broken_processes))
        if processes_to_email:
            trigger_process_warning(processes_to_email)
    return processes_info, process_flags


def trigger_process_warning(broken_processes, email_recipients=cfg.warning_email_recipients):
    """
    This function immediately sends a warning email if a process in process_list=cfg.processes_to_monitor is not running.
    """
    if not type(email_recipients) is list:
        raise Exception("Email recipients must be in a list")
    email = EmailMessage()
    email_text = "PROCESSES NOT RUNNING \n\n" + '\n'.join(broken_processes)
    email.set_content(email_text)
    time = str(datetime.datetime.now().replace(microsecond=0).isoformat().split('T')[1])
    email['Subject'] = "{0}: Critical - broken process(es)".format(cfg.server_name, time)
    email['From'] = cfg.account_to_send_emails + '@gmail.com'
    email['To'] = ", ".join(email_recipients)

    server = smtplib.SMTP(cfg.email_server[0], cfg.email_server[1])
    server.starttls()
    server.login(cfg.account_to_send_emails, cfg.password_to_send_emails)
    server.sendmail(email['From'], email_recipients, email.as_string())
    server.quit()


def log_stats(cpu, ram, hard_drive, boot_drive, processes, log_dir=cfg.stats_archive_dir):
    """
    This function writes the server stats (not including process information) to a logfile.
    """
    now = datetime.datetime.now().replace(microsecond=0)
    date = str(now.date())
    time = str(now.isoformat().split('T')[1])
    log(time)
    os.makedirs(log_dir, exist_ok=True)
    log_file = log_dir + '/stats_log.csv'

    stats_file_header = "time,% CPU use,% RAM used,% hard drive used,free hard drive space,% boot drive used"
    if os.path.isfile(log_file):
        f = open(log_file, 'a')
        f.write('\n')
    elif not os.path.isfile(log_file):
        f = open(log_file, 'w')
        f.write(stats_file_header)
        f.write('\n')
    write_info = [now.isoformat(), cpu, ram, hard_drive['percent_used'], hard_drive['free_space'], boot_drive]
    write_info = ','.join(write_info)
    f.write(write_info)
    f.close()

    write_info = ''
    for process in processes:
        process_log_dir = log_dir + '/processes/' + process
        os.makedirs(process_log_dir, exist_ok=True)
        log_file = process_log_dir + '/' + date + '.csv'
        log_file_header = 'report_time,status,create_time,memory_info,memory_percent,username,cpu_percent'
        if os.path.isfile(log_file):
            f = open(log_file, 'a')
            f.write('\n')
        elif not os.path.isfile(log_file):
            f = open(log_file, 'w')
            f.write(log_file_header)
            f.write('\n')
        process_info = processes[process]
        if type(process_info) is dict:
            write_info = [process_info['report_time'],"OK",process_info['create_time'], process_info['memory_info'], process_info['memory_percent'], process_info['username'], process_info['cpu_percent']]
        elif type(process_info) is list:
            write_info = process_info
        write_info = ','.join(write_info)
        f.write(write_info)
        f.close()

    trigger_warning_email(cpu, ram, hard_drive['free_space'], boot_drive)


def trigger_warning_email(cpu, ram, hard_drive, boot_drive, warn_thresholds=cfg.warning_parameters, crit_thresholds=cfg.critical_parameters):
    """
    This function triggers the sending of a warning email if any of the parameters reach a warning threshold.
    Those parameters are set in the warning_parameters and critical_parameters objects in the config file.
    This function also checks to see if mongo is running, triggering a warning if it isn't.
    """
    warning = False
    warning_contents = []
    stats_to_email = []
    warning_level = ''
    if int(float(cpu)) >= int(warn_thresholds["CPU"]):
        warning = True
        warning_contents.append("CPU usage is at {}%".format(cpu))
        if int(float(cpu)) >= int(crit_thresholds["CPU"]):
            warning_level = "Critical"
        if warning_flags['CPU'] == 0:
            stats_to_email.append("CPU usage is at {}%".format(cpu))
            warning_flags['CPU'] = 1
    elif int(float(cpu)) < int(warn_thresholds["CPU"]):
        warning_flags['CPU'] = 0

    if int(float(ram)) >= int(warn_thresholds["RAM"]):
        warning = True
        warning_contents.append("RAM usage is at {}%".format(ram))
        if int(float(ram)) >= int(crit_thresholds["RAM"]):
            warning_level = "Critical"
        if warning_flags['RAM'] == 0:
            stats_to_email.append("RAM usage is at {}%".format(ram))
            warning_flags['RAM'] = 1
    elif int(float(ram)) < int(warn_thresholds["RAM"]):
        warning_flags['RAM'] = 0

    if round(float(hard_drive[:-1])) <= int(warn_thresholds["hard_drive_space"].replace("B","")[:-1]):
        warning = True
        warning_contents.append("Hard drive free space is down to {}".format(hard_drive))
        if round(float(hard_drive[:-1])) <= int(crit_thresholds["hard_drive_space"].replace("B","")[:-1]):
            warning_level = "Critical"
        if warning_flags['Hard drive space'] == 0:
            stats_to_email.append("Hard drive free space is down to {}".format(hard_drive))
            warning_flags['Hard drive space'] = 1
    elif round(float(hard_drive[:-1])) > int(warn_thresholds["hard_drive_space"].replace("B", "")[:-1]):
        warning_flags['Hard drive space'] = 0

    if int(float(boot_drive)) >= int(warn_thresholds["boot_partition"]):
        warning = True
        warning_contents.append("Boot drive usage is at {}%".format(boot_drive))
        if int(float(boot_drive)) >= int(crit_thresholds["boot_partition"]):
            warning_level = "Critical"
        if warning_flags['Boot drive space'] == 0:
            stats_to_email.append("Boot drive usage is at {}%".format(boot_drive))
            warning_flags['Boot drive space'] = 1
    elif int(float(boot_drive)) < int(warn_thresholds["boot_partition"]):
        warning_flags['Boot drive space'] = 0

    if cfg.check_mongo:
        try:
            pymongo.MongoClient()
            warning_flags['Mongo'] = 0
        except pymongo.errors.ConnectionFailure:
            warning = True
            warning_level = "Critical"
            warning_contents.append("MongoDB not running!")
            if warning_flags['Mongo'] == 0:
                stats_to_email.append("MongoDB not running!")
                warning_flags['Mongo'] = 1

    warning_contents = '{0}: \n\t\t'.format(warning_level) + '\n'.join(warning_contents)

    if warning:
        if not warning_level:
            warning_level = "Warning"
        log(warning_contents)
        if stats_to_email:
            send_warning_email((stats_to_email, warning_level))
    else:
        log("No warning")


def send_warning_email(warning_stats, email_recipients=cfg.warning_email_recipients):
    """
    This function sends an email with critical information. It is triggered based on trigger_warning_email.
    """
    if not type(email_recipients) is list:
        raise Exception("Email recipients must be in a list")
    email = EmailMessage()
    email_text = '\n'.join(warning_stats[0])
    email.set_content(email_text)
    email['Subject'] = "{0}: {1} computer resources".format(cfg.server_name, warning_stats[1])
    email['From'] = cfg.account_to_send_emails + '@gmail.com'
    email['To'] = ", ".join(email_recipients)

    server = smtplib.SMTP(cfg.email_server[0], cfg.email_server[1])
    server.starttls()
    server.login(cfg.account_to_send_emails, cfg.password_to_send_emails)
    server.sendmail(email['From'], email_recipients, email.as_string())
    server.quit()


def prepare_process_summary(processes=cfg.processes_to_monitor):
    """
    For each process, this function reads in the previous day's log files, then generates a single summary line from that
     information. It writes that summary line to a summary log file, then deletes the previous day's log.
    """
    today = datetime.date.today()
    yesterday = today.replace(day=(today.day - 1)).isoformat()
    process_dir = cfg.stats_archive_dir + 'processes/'
    process_report_info = {}
    for process in processes:
        stats_to_report = {}
        folder = process_dir + process
        log_from_yesterday = folder + '/' + yesterday + '.csv'
        if not os.path.isfile(log_from_yesterday):
            stats_to_report = '**No log file for {}**'.format(yesterday)
            log(process + ': ' + stats_to_report)
        else:
            with open(log_from_yesterday, 'r') as f:
                log_contents = pd.read_csv(f)
            metrics = ['memory_info', 'memory_percent', 'cpu_percent']
            for m in metrics:
                size = ''
                data_points = log_contents[m]
                if not type(data_points[0]) is np.float64:
                    size = data_points.str.slice(start=-1)[0]
                    data_points = data_points.str.slice(stop=-1)
                    data_points = pd.to_numeric(data_points)
                data_average = str(round(np.mean(data_points), 2))
                if ('%' or 'percent') in m:
                    data_average = data_average + '%'
                if size:
                    data_average = data_average + size
                stats_to_report[m] = data_average

            summary_log = folder + '/summary.csv'
            summary_header = list(log_contents.rename(columns={'report_time': 'report_date'}))
            if os.path.isfile(summary_log):
                f = open(summary_log, 'a')
                f.write('\n')
            elif not os.path.isfile(summary_log):
                f = open(summary_log, 'w')
                f.write(','.join(summary_header))
                f.write('\n')
            write_info = [yesterday, log_contents['status'].iloc[-1], log_contents['create_time'].iloc[-1], stats_to_report['memory_info'], stats_to_report['memory_percent'], stats_to_report['cpu_percent']]
            write_info = ','.join(write_info)
            f.write(write_info)
            if cfg.delete_daily_process_stats_after_summary:
                os.remove(log_from_yesterday)

        process_report_info[process] = stats_to_report
    return process_report_info


def daily_email_contents(log_dir=cfg.stats_archive_dir):
    """
    This function compiles the information to be included in the daily email
    """
    today = datetime.date.today()
    yesterday = today.replace(day=(today.day-1))
    log = log_dir + '/stats_log.csv'
    stats_to_report = {}
    if not os.path.isfile(log):
        stats_to_report = '**No stats log file for {}**'.format(yesterday)
        log(stats_to_report)
    else:
        with open(log, 'r') as f:
            log_contents = pd.read_csv(f,parse_dates=[0])
            log_contents['date'] = [datetime.datetime.date(d) for d in log_contents['time']]
            log_from_yesterday = log_contents[log_contents['date'] == yesterday]
            metrics = list(log_from_yesterday.columns)
            averaged_metrics = ['% CPU use','% RAM used']
            for m in metrics[1:]:
                if m in averaged_metrics:
                    size = ''
                    data_points = log_from_yesterday[m]
                    if not type(data_points[0]) is np.float64:
                        size = data_points.str.slice(start=-1)[0]
                        data_points = data_points.str.slice(stop=-1)
                        data_points = pd.to_numeric(data_points)
                    data_to_report = str(round(np.mean(data_points), 2))
                    if '%' in m:
                        data_to_report = data_to_report + '%'
                    if size:
                        data_to_report = data_to_report + size
                elif m not in averaged_metrics:
                    data_to_report = str(log_from_yesterday[m].iloc[-1])
                stats_to_report[m] = data_to_report
    cpu = stats_to_report['% CPU use'][:-1]
    ram = stats_to_report['% RAM used'][:-1]
    hard_drive = stats_to_report['free hard drive space'][:-1]
    boot_drive = stats_to_report['% boot drive used'][1]
    warning = trigger_warning_email(cpu, ram, hard_drive, boot_drive)
    if warning:
        return stats_to_report, warning[1]
    else:
        return stats_to_report


def send_daily_email(computer_stats, process_stats, email_recipients=cfg.daily_status_email_recipients):
    """
    email_recipients should be a list.
    This assumes that the email will be sent using a gmail account
    """
    if not type(email_recipients) is list:
        raise Exception("Email recipients must be in a list")
    status = 'OK'
    today = datetime.date.today()
    yesterday = today.replace(day=(today.day - 1)).isoformat()

    email_text = cfg.server_name + ' status report for ' + yesterday + '\n '
    if type(computer_stats) is tuple:
        status = computer_stats[1]
        computer_stats = computer_stats[0]

    if type(computer_stats) is str:
        email_text += computer_stats
    elif type(computer_stats) is dict:
        for f in computer_stats:
            email_text += '\n '
            email_text += f + ': ' + computer_stats[f]

    if process_stats:
        email_text += '\n'
        if type(process_stats) is dict:
            for f in process_stats:
                email_text += '\n '
                email_text += f + ': \n\t\t\t' + str(process_stats[f])
        else:
            email_text += process_stats

    email = EmailMessage()
    email.set_content(email_text)
    email['Subject'] = '{0}: Status {1}'.format(cfg.server_name, status)
    email['From'] = cfg.account_to_send_emails + '@gmail.com'
    email['To'] = ", ".join(email_recipients)

    server = smtplib.SMTP(cfg.email_server[0], cfg.email_server[1])
    server.starttls()
    server.login(cfg.account_to_send_emails, cfg.password_to_send_emails)
    server.sendmail(email['From'], email_recipients, email.as_string())
    server.quit()

    log(today.isoformat() + ':  {0}: Status {1}'.format(cfg.server_name, status))


def log(log_contents):
    """
    This function writes to a log file.
    """
    if cfg.script_log_file:
        with open(cfg.script_log_file, 'a+') as l:
            l.write(log_contents)
            l.write('\n')
    if cfg.print_output_to_terminal:
        print(log_contents)
        print('\n')


def script_error_email(error, email_recipients=cfg.warning_email_recipients):
    """
    This function immediately sends a warning email if the server watch code raises an exception.
    """
    if not type(email_recipients) is list:
        raise Exception("Email recipients must be in a list")
    email = EmailMessage()
    email_text = "Server watch script error: \n\n {}".format(error)
    email.set_content(email_text)
    email['Subject'] = "{0}: Critical - server watch error".format(cfg.server_name)
    email['From'] = cfg.account_to_send_emails + '@gmail.com'
    email['To'] = ", ".join(email_recipients)

    server = smtplib.SMTP(cfg.email_server[0], cfg.email_server[1])
    server.starttls()
    server.login(cfg.account_to_send_emails, cfg.password_to_send_emails)
    server.sendmail(email['From'], email_recipients, email.as_string())
    server.quit()


def run():
    monitoring = True
    while monitoring:
        try:
            CPU_usage = check_cpu()
            RAM_usage = check_ram()
            hard_drive_stats = check_hard_drive()
            boot_drive_usage = check_boot_drive()
            processes_info, process_flags = check_process_status()
            log_stats(CPU_usage, RAM_usage, hard_drive_stats, boot_drive_usage, processes_info)
            now = datetime.datetime.now()
            gap = ((now.hour + (now.minute/60)) - cfg.daily_report_hour) * 60
            if cfg.daily_email_desired:
                if (gap > 0) and (gap <= cfg.minutes_between_stats_check):
                    if cfg.processes_to_monitor:
                        send_daily_email(computer_stats=daily_email_contents(), process_stats=prepare_process_summary())
                    elif not cfg.processes_to_monitor:
                        send_daily_email(computer_stats=daily_email_contents(), process_stats=False)
        except Exception as e:
            log(str(e))
            script_error_email(e)
        log("Sleeping for {} minutes \n".format(cfg.minutes_between_stats_check))
        time.sleep(60*(cfg.minutes_between_stats_check))


run()
