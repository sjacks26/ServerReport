import psutil as p
import datetime
from email.message import EmailMessage
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import time
import smtplib
import numpy as np
import pymongo
import logging
import traceback

import config as cfg

logging.basicConfig(filename=cfg.script_log_file,filemode='a+',level=logging.INFO)

stacks_flags = {}
stacks_flags["stacks_dir"] = 0
stacks_flags["projects"] = {}
ambiguous_collector_names = {}
for project in cfg.stacks_params["projects"]:
    project_collectors = project["collector_names"]
    stacks_flags["projects"][project["project_name"]] = {}
    ambiguous_collector_names[project["project_name"]] = []
    for collector in project_collectors:
        other_collectors = project_collectors.copy()
        other_collectors.remove(collector)
        ambiguous_collectors_w_collector = [f for f in other_collectors if collector in f]
        if len(ambiguous_collectors_w_collector) > 0:
            ambiguous_collector_names[project["project_name"]].append(collector)
    if len(ambiguous_collector_names[project["project_name"]]) > 0:
        logging.critical("Ambiguous collectors for project {}: {}".format(project["project_name"], ambiguous_collector_names[project["project_name"]]))
    for collector in project_collectors:
        stacks_flags["projects"][project["project_name"]][collector] = 0


def check_stacks_details(stacks_params=cfg.stacks_params):
    """
    This function checks to make sure that STACKS collectors are still collecting data as expected. STACKS project and collector names are specified in Config.
    """
    STACKS_problems = False
    STACKS_collector_problems = []
    STACKS_problems_to_email = {"main": None, "projects": [], "collectors": []}
    STACKS_problem_email_required = False
    STACKS_data_dir = os.path.join(stacks_params["stacks_dir"], "data")
    STACKS_project_data_dirs = os.listdir(STACKS_data_dir)
    now = datetime.datetime.now()
    current_hour = now.hour
    if now.minute == 0:
        time.sleep(60*1)
    if current_hour < 10:
        current_hour = '0' + str(current_hour)
    else:
        current_hour = str(current_hour)
    if os.path.isdir(stacks_params["stacks_dir"]):
        stacks_flags["stacks_dir"] = 0
    elif not os.path.isdir(stacks_params["stacks_dir"]):
        logging.critical("STACKS directory {} does not exist. Check directory specified in config file".format(stacks_params["stacks_dir"]))
        STACKS_problems = True
        if stacks_flags["stacks_dir"] == 0:
            STACKS_problems_to_email["main"] = "Main STACKS directory not found"
            stacks_flags["stacks_dir"] = 1
            STACKS_problem_email_required = True
    for project in stacks_params["projects"]:
        end_project_check = False
        while not end_project_check:
            project_name = project["project_name"]
            project_name_and_id = [f for f in STACKS_project_data_dirs if project_name in f]
            if len(project_name_and_id) > 1:
                logging.critical("{} is an ambiguous STACKS project name.".format(project_name))
                for collector in project["collector_names"]:
                    if stacks_flags["projects"][project_name][collector] == 0:
                        STACKS_problems_to_email['projects'].append(project_name)
                        stacks_flags["projects"][project_name][collector] = 1
                        STACKS_problem_email_required = True
                        end_project_check = True
                STACKS_problems = True
            elif len(project_name_and_id) == 0:
                logging.critical("Can't find a STACKS project corresponding to {}.".format(project_name))
                for collector in project["collector_names"]:
                    if stacks_flags["projects"][project_name][collector] == 0:
                        STACKS_problems_to_email['projects'].append(project_name)
                        STACKS_problem_email_required = True
                        stacks_flags["projects"][project_name][collector] = 1
                        end_project_check = True
                STACKS_problems = True
            project_name_and_id = project_name_and_id[0]
            project_data_dir = os.path.join(STACKS_data_dir, project_name_and_id, "twitter", "raw")
            collection_files = [f for f in os.listdir(project_data_dir) if f.endswith('.json')]
            for collector in project["collector_names"]:
                collector_files = [f.split('-')[1] for f in collection_files if collector in f]
                if current_hour in collector_files:
                    stacks_flags["projects"][project_name][collector] = 0
                elif current_hour not in collector_files:
                    STACKS_problems = True
                    STACKS_collector_problems.append(project_name + '-' + collector)
                    logging.critical("No data file for {} for hour {}!".format(collector, current_hour))
                    if stacks_flags["projects"][project_name][collector] == 0:
                        STACKS_problems_to_email['collectors'].append(project_name + '-' + collector)
                        STACKS_problem_email_required = True
                        stacks_flags["projects"][project_name][collector] = 1
            end_project_check = True
    if STACKS_problem_email_required:
        trigger_STACKS_email(STACKS_problems_to_email)
    if not STACKS_problems:
        logging.info("No problems with STACKS")
    return stacks_flags

def trigger_STACKS_email(STACKS_problems_to_email, email_recipients=cfg.warning_email_recipients):
    """
    This function immediately sends a warning email if there is a problem with STACKS
    """
    if not type(email_recipients) is list:
        raise Exception("Email recipients must be in a list")
    email = EmailMessage()
    email_text = 'STACK PROBLEMS \n\n'
    if STACKS_problems_to_email['main']:
        email_text += "Can't find the STACKS data directory. \n\n"
    if STACKS_problems_to_email['projects']:
        email_text += "These STACKS project names are problematic (either ambiguous or not found): \n\t" + '\n\t'.join(STACKS_problems_to_email['projects']) + '\n\n'
    if STACKS_problems_to_email['collectors']:
        email_text += "Couldn't find an expected data file for the following project-collector combinations. The collectors might not be working correctly: \n\t" + "\n\t".join(STACKS_problems_to_email['collectors']) + "\n\n"

    email.set_content(email_text)

    time = str(datetime.datetime.now().replace(microsecond=0).isoformat().split('T')[1])
    email['Subject'] = "{0}: Critical - problem with STACKS".format(cfg.server_name, time)
    email['From'] = cfg.account_to_send_emails + '@gmail.com'
    email['To'] = ", ".join(email_recipients)

    server = smtplib.SMTP(cfg.email_server[0], cfg.email_server[1])
    server.starttls()
    server.login(cfg.account_to_send_emails, cfg.password_to_send_emails)
    server.sendmail(email['From'], email_recipients, email.as_string())
    server.quit()

