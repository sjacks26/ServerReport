"""
This file contains parameters used by main.py
"""

server_name = 'SERVER_NAME'
minutes_between_stats_check = 15
daily_email_desired = True
daily_report_hour = 2
script_log_file = './script.log'
print_output_to_terminal = False

# The next var is a list containing the processes you want to monitor. The script will use each item in the list as a
#  grep phrase to identify running processes
processes_to_monitor = ["PROCESS1", "Process 2"]
check_mongo = True
delete_daily_process_stats_after_summary = False

warning_email_recipients = ["SAMPLE@EMAIL"]
daily_status_email_recipients = ["SAMPLE@EMAIL", "SAMPLE@EMAIL"]
account_to_send_emails = 'USERNAME'         # must be a gmail account. Don't include "@gmail.com"
password_to_send_emails = 'PASSWORD'
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

# MongoDB info for rate limits checker
mongo_account = {
    "address": "MONGODB_SERVER",
    "auth": True,
    "username": "MONGODB_USERNAME",
    "password": "MONGODB_PASSWORD"
}

db_name = 'CENTRAL_LIMITS_DB_NAME'
col_name = 'CENTRAL_LIMITS_COL_NAME'
