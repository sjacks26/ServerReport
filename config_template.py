"""
This file contains parameters used by ServerReport.py
"""

server_name = 'SERVER NAME'
minutes_between_stats_check = 15
daily_email_desired = True
charts_in_status_email = True
daily_report_hour = 2
script_log_file = './script.log'
print_output_to_terminal = False

# The next var is a list containing the processes you want to monitor. The script will use each item in the list as a
#  grep phrase to identify running processes
processes_to_monitor = ["PROCESS1", "Process 2"]
check_mongo = True
delete_daily_process_stats_after_summary = False

warning_email_recipients = ["SAMPLE@EMAIL"]
daily_status_email_recipients = ["SAMPLE@EMAIL"]
account_to_send_emails = 'SAMPLE'         # must be a gmail account. Don't include "@gmail.com"
password_to_send_emails = 'PASSWRD'
email_server = ("smtp.gmail.com", 587)     # This should always work for gmail

critical_parameters = {
    "CPU": "90",
    "RAM": "80",
    "hard_drive_space": "100GB",
    "boot_partition": "90"
}
warning_parameters = {
    "CPU": "80",
    "RAM": "70",
    "hard_drive_space": "180GB",
    "boot_partition": "85"
}

stats_archive_dir = './log/'

root_dir = '/'
boot_drive = '/boot'
