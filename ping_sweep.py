from datetime import datetime
import subprocess
from select import select
import logging

def setup_logger(logger_name, log_file, level=logging.INFO):
    log_setup = logging.getLogger(logger_name)
    # formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%m-%d %H:%M:%S')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    fileHandler.terminator = ""
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    streamHandler.terminator = ""
    log_setup.setLevel(level)
    log_setup.addHandler(fileHandler)
    log_setup.addHandler(streamHandler)

    return log_setup

hostsfile=open("ping_targets.txt", "r")
kwds = {
    "stdout": subprocess.PIPE,
    "bufsize": 1,
    "close_fds": True,
    "universal_newlines": True,
}

#build commands
commands = []
log_files = {}
lines=hostsfile.readlines()
for line in lines:
    cur_cmd = ["ping", "-i", "1", "-c", "18000"]
    cur_target = line.strip()
    cur_cmd.append(cur_target)
    commands += [cur_cmd]

# Build the process list
dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%m%d%H%M%S")
procs = [subprocess.Popen(cmd, **kwds) for cmd in commands]
log_file_base = r'/Users/ezhou/Downloads/ping_sweep_test/'
for p in procs:
    # log_files[p.stdout] = open(log_file_base + p.args[-1] + '-' + timestampStr + '_ping.log', 'w')
    logger_name = p.args[-1]
    log_file = log_file_base + p.args[-1] + '-' + timestampStr + '_ping.log'
    log_files[p.stdout] = setup_logger(logger_name, log_file)


# Join on proesses, reading stdout as we can
while procs:
    # Remove finished processes from the list
    for p in procs:
        if p.poll() is not None:           # process ended
            remaing_lines = p.stdout.read()
            log_files[p.stdout].info(remaing_lines)
            p.stdout.close()               # clean up file descriptors
            # log_files[p.stdout].close()
            procs.remove(p)                # remove the process
            print(f"{p.args} closed")

    # Attempt to read stdout where we can
    rlist = select([p.stdout for p in procs], [], [], 0.1)[0]
    for fd in rlist:
        log_files[fd].info(fd.readline())
