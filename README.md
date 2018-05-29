# ServerReport

This script is used to monitor the status of an Ubuntu server.  
It tracks a set of core system stats (RAM usage, CPU usage, hard drive usage and free space, and boot drive usage).  
It can also track the status of processes specified in [config.py](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L14), and it can [check whether MongoDB is running](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L15).  
  
### Logging
ServerReport creates a log of system stats and a log of stats for each process being tracked, allowing the user to monitor system load and process load over time.  

### Email notifications
ServerReport also sends email updates about the stats it monitors.   
* It can send a [daily email](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L7) with a summary of the states, at a [time specified by the user](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L8).
* It sends a warning email if any of the stats surpass [thresholds](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L24) set by the user or if any [process being tracked](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L14) isn't running. ServerReport is smart enough to know if it has already notified the user about a warning and won't send another email about that warning until the problem has been fixed and happens again. 

The user can specify different recipients for [warning emails](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L18) and the [daily email](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L19).  
To use email notifications, the user should specify a [gmail account](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L20) and [password](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L21) used to send the notifications. ServerReport requires that the email address used to send notification emails be a gmail account.

### Installation and setup

To run ServerReport:  
1) Clone the code to your server using `git clone https://github.com/sjacks26/ServerReport.git`. You should run this command from a directory that your user has write permissions in; otherwise, you can run ServerReport as sudo.    
2) Rename `config_template.py` to `config.py`.
3) Modify the parameters in [config.py](https://github.com/sjacks26/ServerReport/blob/master/config_template.py) to match your preferences.  
   * If you are tracking processes, ServerReport uses a grep search to find those processes on the server. You should [include enough information](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L14) about the command used to run the process you want to monitor so that ServerReport will only find one active process for each item entered in the list of processes to be monitored. If ServerReport finds more than one active process for a process specified in config.py, it will not be able to track process stats. Instead, the process log will say that the process name is ambiguous.   
   * Choose what [system level stats](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L24) should trigger a warning email. The idea here is a warning parameter leads to an alert that you should address when you can, and a critical parameter leads to an alert that you should address ASAP.  
   * Specify the email accounts for recipients and for the account used to send emails.
   * Specify the [interval (in minutes) between stats checks](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L6). ServerReport will sleep for this many minutes after it runs each time.
   * If you want a daily status email, specify the [hour (using a 24 hour clock)](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L8) you want to receive that email.
   * Specify whether you want ServerReport to [make sure MongoDB is running](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L15).
   * You may want to keep detailed information about process statistics to monitor each process's computational load over time. ServerReport creates a summary log file with the daily average for each process's load, but you can also tell it to [keep a detailed log](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L16) with the information from each time it checks those statistics.
 4) Run ServerReport:
     * You can run ServerReport with `python main.py`. This will keep ServerReport in the foreground. If you want to see output from ServerReport, make sure you [specify that in the config file](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L10).
     * To run ServerReport in the background, use `python main.py &`. ServerReport keeps a log of stderr and stdout, so you don't need to tell ServerReport what to do with those two kinds of output in the command.
     
### Requirements

ServerReport requires Python3, [psutil](https://pypi.org/project/psutil/), [pandas](https://pandas.pydata.org/), and any version of [pymongo](https://api.mongodb.com/python/current/).
