1. ping_sweep.py
read hosts from ping_targets.txt
for each host, start a process and execute below command:
------------------------------------------------
    cur_cmd = ["ping", "-i", "1", "-c", "18000"] + host
------------------------------------------------
log file is saved to:
    log_file_base = r'/Users/ezhou/Downloads/ping_sweep_test/'

2. ping_plot.py
read names of the ping log files to be analysis from "ping_log_file_name.json"
for each file, parsing it and create plot/analysis file in the same directory
A csv file will be created with information collected from all log files
    csv file = '/Users/ezhou/Downloads/ping_stats_merged-'+timestampStr+'.csv

3. ping_rtt.py and ping_filter.py
??? To be analyzed




