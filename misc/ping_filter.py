import os

import glob


def filter_ping_log(ping_log_f_name):
    print("processing ping log file: " + ping_log_f_name)
    ping_log_filter_output_f_name = os.path.splitext(ping_log_f_name)[0] + '_out.txt'

    pre_ln_flag = None
    cur_ln_flag = None

    with open(ping_log_filter_output_f_name, 'w+') as output_file:
        with open(ping_log_f_name, errors='ignore') as file:
            for cur_ln in file:
                if "Request timed out" in cur_ln:
                    cur_ln_flag = "timed_out"
                elif "Reply from" in cur_ln:
                    cur_ln_flag = "Reply from"
                # else:
                #     cur_ln_flag = "MISC"

                if cur_ln_flag != pre_ln_flag:
                    # print(cur_ln)
                    output_file.write(cur_ln)

                pre_ln_flag = cur_ln_flag
            output_file.write(cur_ln)


# all_ping_log_files = glob.glob("/Users/ezhou/Documents/smawave/tech_support/cases/011_APMT_longbeach/cpe configuration/ping/*.txt")
# all_ping_log_files = glob.glob("/Users/ezhou/Documents/smawave/tech_support/cases/011_APMT_longbeach/disconnection_issue/all_logs/ping_log/*.txt")
# all_ping_log_files = glob.glob("/Volumes/FileBackup/disconnection_issue/ping-0428/*.txt")
all_ping_log_files = glob.glob("/Users/ezhou/Downloads/ping/ping_20210323_172.17.18.41.txt")




for ping_log_file in all_ping_log_files:
    if "out" in ping_log_file:
        continue
    filter_ping_log(ping_log_file)





# filter_ping_file(ping_f_name)



# with open(f_name, errors='ignore') as file:
#     pre_ln_flag = None
#     cur_ln_flag = None
#     for cur_ln in file:
#         if "Request timed out" in cur_ln:
#             cur_ln_flag = "timed_out"
#         elif "Reply from" in cur_ln:
#             cur_ln_flag = "Reply from"
#
#         if cur_ln_flag != pre_ln_flag:
#             print(cur_ln)
#
#         pre_ln_flag = cur_ln_flag




