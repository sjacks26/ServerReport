"""
This script is used to pull plots based on information generated by ServerReport. It is written to be highly interactive, so even folks who don't know enough python to use ServerReport can use this code to generate plots.
"""

import matplotlib
matplotlib.use('Agg')
import smtplib
from email.message import EmailMessage
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
import os
import numpy as np
import datetime
from dateutil.parser import parse
import pandas as pd

import config as cfg


def build_process_list():
    processes_dir = os.path.join(cfg.stats_archive_dir, 'processes')
    processes1 = os.listdir(processes_dir)
    processes = {}
    process_count = 0
    for f in processes1:
        if os.path.isdir(os.path.join(processes_dir, f)):
            process_count += 1
            processes[process_count] = f
    return processes


def ask_for_info():
    valid_input = False
    while valid_input == False:
        to_email_addresses = input("What email addresses should the plots be sent to? \nIf more than one, separate them with commas\n")
        to_email_addresses = [f.strip() for f in to_email_addresses.split(",")]
        for em in to_email_addresses:
            if not "@" in em:
                print("\n\tYou provided an invalid email address! Try again.\n")
                break
            valid_input = True

    valid_input = False
    while valid_input == False:
        processes_or_computer = input("Do you want plots for processes or the computer?\n")
        if not processes_or_computer in {"processes", "computer"}:
            print("Input not recognized. Enter \"processes\" or \"computer\"")
        elif processes_or_computer == "computer":
            valid_input = True
        elif processes_or_computer == "processes":
            processes = build_process_list()
            print("Found {} processes that I can generate plots for.".format(len(processes)))
            for f in processes:
                print('{0}: {1}'.format(f, processes[f]))
            choose_processes_or_computer = False
            while choose_processes_or_computer == False:
                processes_or_computer = input("Which of these processes do you want plots for? Or do you want plots for all?\nIf you want only some of the processes,\n\t use the number of that process as shown above\n")
                if "all" in processes_or_computer.split():
                    processes_or_computer = list(processes.values())
                    choose_processes_or_computer = True
                elif type(processes_or_computer) is str:
                    if processes_or_computer.isdigit():
                        if "," in processes_or_computer:
                            processes_or_computer = [f.strip() for f in processes_or_computer.split(",")]
                        elif not "," in processes_or_computer:
                            processes_or_computer = [f for f in processes_or_computer]
                        processes_or_computer = [processes[int(f)] for f in processes_or_computer]
                    elif not processes_or_computer.isdigit():
                        processes_or_computer = [f.strip() for f in processes_or_computer.split(",")]
                    if np.setdiff1d(processes_or_computer, list(processes.values())).size > 0:
                        print("One of the processes you asked for isn't valid. Try again.")
                    else:
                        choose_processes_or_computer = True
            valid_input = True

    valid_input = False
    while valid_input == False:
        start_date = input("Please specify a start date for the plot, or enter \"None\" if you want plots for all data with no date restriction.\n")
        if start_date == "None":
            start_date = False
            valid_input = True
        else:
            try:
                start_date = parse(start_date)
                valid_input = True
            except ValueError:
                print("Couldn't parse your start date. Try again.")

    return to_email_addresses, processes_or_computer, start_date


to_email_addresses, processes_or_computer, start_date = ask_for_info()

'''
Modify the printed process list to give numbers to each process. Then the prompt for which processes you want can be a comma separated list of process numbers rather than process names 
'''

def build_stats_dfs():
    stats_dict = {}
    if processes_or_computer == "computer":
        stats = pd.read_csv(cfg.stats_archive_dir + '/stats_log.csv', parse_dates=['time'])
        stats.rename(columns={'% CPU use': 'cpu_percent','% RAM used': 'memory_percent', 'time': 'report_time'}, inplace=True)
        if start_date:
            stats = stats[stats['report_time'] >= start_date]
        stats_dict[processes_or_computer] = stats
    elif type(processes_or_computer) is str:
        daily_stats_files = os.listdir(os.path.join(cfg.stats_archive_dir, 'processes', processes_or_computer))
        daily_stats_files = [os.path.join(cfg.stats_archive_dir, 'processes', processes_or_computer,f) for f in daily_stats_files if '-' in f]
        stats = pd.DataFrame()
        for file in daily_stats_files:
            daily_stats = pd.read_csv(file)
            daily_stats['report_time'] = pd.to_datetime(os.path.basename(file).replace('.csv','T') + daily_stats['report_time'])
            stats = pd.concat([stats, daily_stats],ignore_index=True)
        if start_date:
            stats = stats[stats['report_time'] >= start_date]
        stats_dict[processes_or_computer] = stats
    elif type(processes_or_computer) is list:
        for process in processes_or_computer:
            stats = pd.DataFrame()
            daily_stats_files = os.listdir(os.path.join(cfg.stats_archive_dir, 'processes', process))
            daily_stats_files = [os.path.join(cfg.stats_archive_dir, 'processes', process, f) for f in daily_stats_files if '-' in f]
            for file in daily_stats_files:
                daily_stats = pd.read_csv(file)
                daily_stats['report_time'] = pd.to_datetime(os.path.basename(file).replace('.csv', 'T') + daily_stats['report_time'])
                stats = pd.concat([stats, daily_stats], ignore_index=True)
            if start_date:
                stats = stats[stats['report_time'] >= start_date]
            stats_dict[process] = stats

    return stats_dict


def make_plots():
    stats_dict = build_stats_dfs()
    plot = plt.figure(figsize=(15,6))
    plot1 = plot.add_subplot(121)
    plot_line_types = ['solid', 'dashed']
    plot_colors = ["#208eb7", "#9e4f84", "#51825d", "#ce6552", "#7363e7", "#b825af", "#90705e", "#e91451", "#1c9820", "#8138fc", "#ab7b05"]
    while len(plot_colors) < len(stats_dict):
        plot_colors.extend(plot_colors)

    processes = list(stats_dict.keys())
    for f in range(len(stats_dict)):
        stats = stats_dict[processes[f]]
        stats.sort_values('report_time', inplace=True)
        plot1.plot_date(stats['report_time'], stats['cpu_percent'], color=plot_colors[f], ls=plot_line_types[0], label=processes[f] ,marker=None)
        plot1.plot_date(stats['report_time'], stats['memory_percent'], color=plot_colors[f], ls=plot_line_types[1], label='_nolegend_', marker=None)

    plot.autofmt_xdate()
    plot.legend(loc='right')
    plot1.set_ylabel("solid line is CPU\n\ndashed line is RAM", labelpad=50).set_rotation(0)
    fig_name = 'temp.png'
    plot.savefig(fig_name)
    plt.close('all')

    return fig_name


def email_plots():
    fig_name = make_plots()
    email_text = 'Requested plots for {}'.format(cfg.server_name)

    msg = MIMEMultipart('related')
    msg['Subject'] = 'Requested plots'
    msg['From'] = cfg.account_to_send_emails + '@gmail.com'
    msg['To'] = ", ".join(to_email_addresses)
    msg.attach(MIMEText(email_text))

    email_alternative = MIMEMultipart('alternative')
    msg.attach(email_alternative)
    msgText = MIMEText('\n\n\nThis message is meant to contain an image.\n')
    email_alternative.attach(msgText)

    with open(fig_name, 'rb') as plot:
        img = MIMEImage(plot.read())
    img.add_header('Content-ID', '<image{}>'.format(1))
    img.add_header('Content-Disposition', 'attachment', filename='Requested plot from {}'.format(cfg.server_name))
    email_alternative.attach(img)

    server = smtplib.SMTP(cfg.email_server[0], cfg.email_server[1])
    server.starttls()
    server.login(cfg.account_to_send_emails, cfg.password_to_send_emails)
    server.sendmail(msg['From'], to_email_addresses, msg.as_string())
    server.quit()

    os.remove(fig_name)

    print('Email sent at {}'.format(datetime.datetime.now().isoformat()))

run = email_plots()
