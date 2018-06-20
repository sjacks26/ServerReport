# ServerReport

ServerReport contains two primary tools:
1) [ServerReport.py](https://github.com/sjacks26/ServerReport/blob/master/ServerReport.py): This script should run continuously in the background, logging computer stats, sending daily report emails, and sending warning emails when a problem arises.
2) [get_plot.py](https://github.com/sjacks26/ServerReport/blob/master/get_plot.py): This script can be run on as-needed basis to generate line charts that visualize information logged by ServerReport.py. This script only works if ServerReport.py has been running on the same machine.

### Installation and setup
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


## ServerReport.py

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

### Running ServerReport.py

First, make sure that you have modified the parameters in config.py as appropriate. Then, run ServerReport.py.
 * You can run ServerReport.py with `python ServerReport.py`. This will keep ServerReport.py in the foreground. If you want to see output from ServerReport.py, make sure you [specify that in the config file](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L10).
 * To run ServerReport.py in the background, use `python ServerReport.py &`. ServerReport.py keeps a log of stderr and stdout, so you don't need to tell it what to do with those two kinds of output in the command.
     
## get_plot.py

This script allows users to ask for plots of information tracked by ServerReport.py. It uses the same config file used by ServerReport.py.
get_plot.py is highly interactive. When you run this script, it will ask you a series of questions:
1) What email addresses should the plots be sent to? If more than one, separate them with commas.
2) Do you want plots for processes or the computer?
    2a) If you choose processes, get_plot.py will print a list of processes it can generate plots for. You can choose any or all of those processes.
3) Please specify a start date for the plot, or enter "None" if you want plots for all data with no date restriction.

Once you answer these questions, get_plot.py will gather logged stats, generate a line chart, then email that chart to you as a PNG file. get_plot.py uses the same email address to send this chart as ServerReport.py uses to send you status emails.

### Plot information

Plots will contain information about CPU usage and about RAM usage (both in percentages) over time. The granularity of the plot (i.e., the time period between data points) will be determined by the [time between stats checks from ServerReport.py](https://github.com/sjacks26/ServerReport/blob/master/config_template.py#L6). CPU usage information will always be the solid line in the returned plots, and RAM usage will always be the dashed line.  
* If you ask for plots for the computer, you will receive one plot with one dashed line and one solid line, covering the time period you asked for.  
* If you ask for plots for one process, you will receive one plot with one dashed line and one solid line, covering the time period you asked for.  
* If you ask for plots for more than one process, you will receive one plots with one dashed line and one solid line for each process you asked for, covering the time period you asked for. Each process will be assigned a color, and both the CPU line and the RAM line will use that color.   
  * Note that get_plot.py only uses 11 unique colors, so if you have more than 11 processes, the plot might be a little confusing.

### Running get_plot.py

Running get_plot.py is simple. Just enter `python get_plot.py` from the directory containing the script. Then follow the on-screen prompts. That's it!  
     
## ServerReport Requirements

* Python3  
* [psutil](https://pypi.org/project/psutil/) (tested with version 5.4.3)
* [matplotlib](https://matplotlib.org/) (tested with version 2.1.2)  
* [pandas](https://pandas.pydata.org/) (tested with version 0.22.0)  
* [pymongo](https://api.mongodb.com/python/current/)
