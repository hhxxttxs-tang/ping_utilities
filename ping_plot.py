from parsy import string, regex, seq, ParseError, line_info, success, generate, fail, success, Parser, Result

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from pyecharts import options as opts
from pyecharts.charts import Line, HeatMap, Grid, Tab

import pysnooper

from datetime import datetime
import os, re, time, json, logging
import glob


# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.DEBUG,
                    # format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    format='%(message)s',
                    # datefmt='%m-%d %H:%M',
                    filename='parser.log',
                    filemode='w')

log_mark_count = 0

# usage: PARSER.mark().map(log_mark)
# parsy lib has been updated to support output of parsed string.
def log_mark(mark_result):
    # print(mark_result)
    global log_mark_count
    log_mark_count += 1
    logging.debug("\n--------------%s--------------------------------------",str(log_mark_count))
    logging.debug("parsing start = %s", mark_result[0])
    logging.debug("parsing end = %s", mark_result[2])
    logging.debug("str parsed =\n%s%s", mark_result[3],"^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    logging.debug("parsing result = %s", [mark_result[1]])

    return mark_result[1]


# updated part of parsy lib

# 1. updated member function of Parser class

# # def mark(self):
# #     @generate
# #     def marked():
# #         start = yield line_info
# #         body = yield self
# #         end = yield line_info
# #         return (start, body, end)
# #
# #     return marked
#
# def mark(self):
#     @generate
#     def marked():
#         start_index = yield index
#         start = yield line_info
#         body = yield self
#         end_index = yield index
#         end = yield line_info
#         stream_head = yield stream
#         str_parsed = stream_head[start_index:end_index]
#         return (start, body, end, str_parsed)
#
#     return marked

# 2. add a new global variable
# stream = Parser(lambda stream, index: Result.success(index, stream))



# @pysnooper.snoop('/Users/ezhou/Downloads/snoop.log')
def load_var_from_file(f_name):
    with open(f_name, errors='ignore') as file:
        for cur_ln in file:
            if cur_ln.strip() and (not cur_ln.startswith('#')) and (not cur_ln.startswith('/')):
                # print(cur_ln)
                return json.loads(cur_ln)

        return None

def load_all_var_from_file(f_name):
    fn_list = []
    with open(f_name, errors='ignore') as file:
        for cur_ln in file:
            cur_ln = cur_ln.strip()
            if cur_ln and (not cur_ln.startswith('#')) and (not cur_ln.startswith('/')):
                if not "*" in cur_ln:
                    fn_list.append(cur_ln[1:-1])
                else:
                    fn_list += glob.glob(cur_ln[1:-1])

    return fn_list

# @pysnooper.snoop('/Users/ezhou/Downloads/snoop.log')
def flatten_dict(target_dict):
    res_dict = {}
    if type(target_dict) is not dict:
        return res_dict

    for k, v in target_dict.items():
        if type(v) == dict:
            # res_dict.update(flatten_dict(v))
            # No need to recurse further (dict is two level deep)
            res_dict.update(v)
        else:
            res_dict[k] = v

    return res_dict

# merge multi-dictionaried into one
# def merge_dict(*dicts):
#     ret = {}
#     for d in dicts:
#         if d:
#             ret = {**d, **ret}
#     return ret

def merge_dict(*args):
    # print("in FUN: combineDict")
    result = {}
    for cur_dict in args:
        # print("dict to be merged = ", cur_dict)
        if cur_dict:
            result.update(cur_dict)

    result = {k: v for k, v in result.items() if not k.startswith('_')}

    return result

# Final version
# merge sequence(list) of dictionaries into one, e.g.:
# [dic1, dic2, dic3]
#     dic1 = {'A': 1, 'B': 1, 'C': [1, 1]}
#     dic2 = {'A': 2, 'B': [2, 2], 'C': 2}
#     dic3 = {'D': 3, 'E': 3, 'F': [3, 3]}
#     output: {'A': [1, 2], 'B': [1, 2, 2], 'C': [1, 1, 2], 'D': 3, 'E': 3, 'F': [3, 3]}
def merge_dict_of_list(*args):
    # print("in FUN: combineDict")
    result = {}
    for cur_dict in args:
        # print("dict to be merged = ", cur_dict)
        if not cur_dict:
            continue
        key_both = result.keys() & cur_dict.keys()

        for key in cur_dict.keys():
            if key in key_both:
                if type(result[key]) is not list:
                    result[key] = [result[key]]
                if type(cur_dict[key]) is not list:
                    cur_dict[key] = [cur_dict[key]]

                result.setdefault(key, []).extend(cur_dict[key])

            # only in current dict
            else:
                result[key] = cur_dict[key]

    # print("final dict = \n", result)
    return result

# convert string with format
# " [06-03 14:17:03]PERF :"
# to datetime object
# def to_datetime(str):
#     ret = ['1970','01','01','0','0','0']
#     str = str.strip()
#     if not str:
#         return datetime(*map(int, ret))
#     date_str = re.match(r'\[(.*)\]', str)
#     if date_str and date_str[1] and date_str[1][0:3]!='SCC':
#         str_split = re.split(r'[-:\s]',date_str[1])
#         delta = len(ret) - len(str_split)
#         for i in range(len(str_split)):
#             ret[i+delta] = str_split[i]
#     return datetime(*map(int, ret))

def to_datetime(str):
    # print("\nin Fun: to_datetime:")
    # print("input str = ", str)
    date_str = re.match(r'\[(.*?)\]', str)
    # print("matched str = ", date_str)
    # date_str has the string within '[]'(excluding '[',']')
    if date_str and date_str[1] and date_str[1][0:3]!='SCC':
        return date_str[1]
    else:
        return '1970-01-01 00:00:00.000'

# Pattern
# space(or \n) delimited string
space_sep_str = r'(?:\S*[ |\n])*'

# Pattern
# arbitary strings or lines (might be multiple lines)
any_str = r'(?:.|\n)*?'
any_str_within_line = r'(?:.)*?'

# Parse primitive:
#   function all returns a parser instance
# parse target starting from current stream pointer in the stream
# stream pointer move to after target after the function
# target is returned if found
# parse_current = lambda x: regex(x)
parse_current = regex

# Parse primitive:
#   function all returns a parser instance
# skip target starting from current stream pointer in the stream
# stream pointer move to after target after the function
# target is returned if found
# needs to be followed by ">>" or preceded by " << ""
skip_current = parse_current

# Parser instance:
#   call to its member functions(parse(), parse_partial()) starts the parsing procedure
# skipped starting from current pointer until EOL(including EOL)
# needs to be followed by ">>" or preceded by " << ""
skip_until_EOL = skip_current(r'.*\n')

# Parse primitive:
#   function all returns a parser instance
# search for target starting from current pointer
# stream pointer move to after target after the function
# all between current pointer and target(included) is returned if target is found
# needs to be followed by ">>" or preceded by " << ""
def skip_until_after(target_str):
    # p_str = any_str + target_str
    # print("search_and_skip: regular expression =", p_str)
    return regex(any_str + target_str)

# Parse primitive:
#   function all returns a parser instance
def skip_inline_until_after(target_str):
    return regex(any_str_within_line + target_str)

# search for target starting from current pointer
# stream pointer move to right before target after the function
# all between current pointer and target is returned if target is found
# needs to be followed by ">>" or preceded by " << ""
def skip_until_before(target_str,flags=0):
    p_str = any_str + r'(?=' + target_str + r')'
    # print("search_until: regular expression =", p_str)
    return regex(p_str,flags)

def skip_inline_until_before(target_str):
    p_str = any_str_within_line + r'(?=' + target_str + r')'
    return regex(p_str)

# search for target starting from current pointer
# stream pointer move to after target after the function
# target is returned if found
def search_and_parse(target_str,flags=0):
    return skip_until_before(target_str,flags) >> parse_current(target_str,flags)

def search_inline_and_parse(target_str):
    return skip_inline_until_before(target_str) >> parse_current(target_str)

def peek(parser):
    @Parser
    def peek_parser(stream, index):
        result = parser(stream, index)
        if result.status:
            return Result.success(index, result.value)
        else:
            return result
    return peek_parser

# Parse primitive:
#   function all returns a parser instance
# Note: ?????
#   target_pattern and until_marker are NOT suppoed to be in the same line
#   until_marker are assumed to be in the beginning of a line
def search_within_block(target_pattern, until_marker):
    # print("\nIn Fun search_within_block: ")
    # print(" target = ", target_pattern)
    # print(" until_marker = ", until_marker)

    # generated function cannot have parameters.
    # so parameters have to be wrapped by outer function if there are
    # ref: source code of "generate" decorator
    @generate
    def search_within_block_generator():
        # print("\nIn Fun search_within_block: ")
        while True:
            # TODO: to return None or ""???
            # following two ways are equivalent
            # marker_found = yield peek(search_inline_and_parse(until_marker)) | success("")
            marker_found = yield (peek(search_inline_and_parse(until_marker)) | success(""))

            # print("until marker found (?) = ", marker_found, "target = ", target_pattern)
            if marker_found:
                # print("target found >>> FAILED <<<")
                return fail(target_pattern)

            # TODO: to return None or ""???
            # following two ways are equivalent
            # res = yield search_inline_and_parse(target_pattern) | success("")
            res = yield (search_inline_and_parse(target_pattern) | success(""))

            if res:
                # print("target found >>> OK << = ", res, "until_marker =", until_marker)
                return res
            else:
                yield skip_until_EOL

    return search_within_block_generator

#extract pattern from a string and save it into a list
#return: list of string
def string_splitter(the_pattern):

    @generate
    def pattern_splitter_gen():
        res = []
        while True:
            pattern_found = yield(skip_until_before(the_pattern) | success(""))
            if not pattern_found:
                return res

            mcs_parse_str = yield parse_current(the_pattern)
            res.append(mcs_parse_str)
    return pattern_splitter_gen

#extract pattern from a string, save it into a list, convert each string(list element) using a pattern parser
def string_to_list_by_pattern(the_str, the_pattern, pattern_parser):
    str_list = (string_splitter(the_pattern).parse_partial(the_str))[0]
    res = []
    for str_list_ele in str_list:
        cur_res = pattern_parser.parse_partial(str_list_ele)
        if cur_res[0]:
            res.append(cur_res[0])

    return res

#parsing the line of Ping
# [10-17 06:59:56] 64 bytes from 172.20.12.53: seq=1 ttl=121 time=21.646 ms

PING_timestamp = r'\[\d\d-\d\d \d\d:\d\d:\d\d\]'
# PING_host_ip = r'\d+\.\d+\.\d+\.\d+'
PING_host_ip = r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}'
PING_seq = r'\d+'
PING_ttl = r'\d+'
float_val = r'-?\d+\.\d+'
PING_time = float_val
# PING_line = PING_timestamp + r' 64 bytes from 172\.20\.12\.53\:'
PING_line = PING_timestamp + r'\s*64 bytes from ' + PING_host_ip


# Parser instance:
#   call to its member functions(parse(), parse_partial()) starts the parsing procedure
# parsing procedure output of below Parser instance:
#   A dictionary, e.g.: {'FRAME_leading': 'YES', 'FRAME_status': 'IDLE', 'FRAME_cat': 'CAT6/5', 'FRAME_duplex': 'TDD'}
PING_pattern = seq(
    _skip = skip_until_before(PING_line),
    timestamp = parse_current(PING_timestamp).map(lambda s:s[1:-1]),
    host = search_inline_and_parse(r'from ') >> parse_current(PING_host_ip),
    seq = search_inline_and_parse(r'seq\=') >> parse_current(PING_seq),
    ttl = search_inline_and_parse(r'ttl\=') >> parse_current(PING_ttl),
    time = skip_inline_until_after(r'time\=') >> parse_current(PING_time).map(float) << skip_until_EOL
)
parse_pattern = PING_pattern.many()

def generateChart(list_of_columns, df):
    print("in generateChart: list_of_columns = ", list_of_columns)
    # minimum 25 on my laptop
    legend_height = 25
    # 50 looks well on my laptop, better to be >30
    y_height_per_measurement = 300

    column_list_in_df = lambda a_list, a_df: [col for col in a_list if col in a_df.columns]
    column_in_df = lambda a_column, a_df: [a_column] if a_column in a_df.columns else None

    chart_list = []
    cur_pos = 0
    for idx in range(len(list_of_columns)):
        columns = list_of_columns[idx]
        print("configured columns = ", columns)

        columns = column_list_in_df(columns, df) if type(columns) is list else column_in_df(columns, df)
        print("columns exists in df = ", columns)

        pos_top_legend = cur_pos
        pos_top_chart = cur_pos + legend_height

        chart_height = None


        line_x = Line()

        perf_time_uniq = df['PERF_time'].unique()
        perf_time_uniq = perf_time_uniq[~pd.isnull(perf_time_uniq)]

        # check if the time stamp added by the parser
        if (perf_time_uniq.size == 1) and (perf_time_uniq[0]=='01-01 00:00:00.000'):
            # added by parser, x-axis use index instead
            line_x.add_xaxis(xaxis_data=df['index'])
        else:
            line_x.add_xaxis(xaxis_data=list(df['PERF_time']))
        if columns:
            for col in columns:
                print("col = ", col)
                # print("df[col] = ", df[col])
                if 'kbps' in col:
                    line_x.add_yaxis(
                        series_name=col,
                        y_axis=df[col],
                        is_smooth=False,
                        is_hover_animation=False,
                        linestyle_opts=opts.LineStyleOpts(width=3, opacity=1),
                        label_opts=opts.LabelOpts(is_show=False),
                        symbol='none',
                        areastyle_opts=opts.AreaStyleOpts(opacity=0.3)
                    )
                # elif 'PCI_global_index' in col:
                elif col.startswith("PCI="):
                    chart_height = 30
                    line_x.add_yaxis(
                        series_name=col,
                        y_axis=df[col],
                        is_smooth=False,
                        is_hover_animation=False,
                        linestyle_opts=opts.LineStyleOpts(width=0, opacity=1),
                        label_opts=opts.LabelOpts(is_show=False),
                        symbol='none',
                        is_step = True,
                        areastyle_opts=opts.AreaStyleOpts(opacity=1),
                    )
                elif 'FRAME_status' in col or 'Line_no_in_logfile' in col:
                    line_x.add_yaxis(
                        series_name=col,
                        y_axis=df[col],
                        is_smooth=False,
                        is_hover_animation=False,
                        linestyle_opts=opts.LineStyleOpts(width=3, opacity=1),
                        label_opts=opts.LabelOpts(is_show=False),
                        symbol='none',
                        is_step = True,
                        areastyle_opts=opts.AreaStyleOpts(opacity=1),
                    )
                else:
                    line_x.add_yaxis(
                        series_name=col,
                        y_axis=df[col],
                        is_smooth=False,
                        is_hover_animation=False,
                        linestyle_opts=opts.LineStyleOpts(width=1, opacity=1),
                        label_opts=opts.LabelOpts(is_show=False),
                        symbol='none',
                    )
        # all plots to configure except for the last one
        if idx != len(list_of_columns) - 1:
            line_x.set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),
            )
        else:
            line_x.set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(is_show=True,rotate=-20),
                ),
            )
        # the sequence of configuration matters...be caution when move the code around
        line_x.set_global_opts(
            legend_opts=opts.LegendOpts(
                is_show=True, pos_top=pos_top_legend, pos_left="center"
                # is_show=True,pos_left="center"
            ),
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
        )

        if idx == 0:
            line_x.set_global_opts(
                datazoom_opts=[
                    # opts.DataZoomOpts(
                    #     is_show=False,
                    #     type_="inside",
                    #     xaxis_index=list(range(len(list_of_columns))),
                    #     range_start=0,
                    #     range_end=100,
                    # ),
                    opts.DataZoomOpts(
                        is_show=True,
                        xaxis_index=list(range(len(list_of_columns))),
                        type_="slider",
                        # pos_top=str(component_height * len(list_of_columns) + 50),
                        pos_bottom='0',
                        range_start=0,
                        range_end=100,
                    ),
                ],
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                    background_color="rgba(245, 245, 245, 0.0)",
                    border_width=1,
                    border_color="#ccc",
                    textstyle_opts=opts.TextStyleOpts(color="#000", font_size=10),
                ),
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    # label=opts.LabelOpts(background_color="#777"),
                    label=opts.LabelOpts(background_color="#f5f5f5", color="#000"),

                ),
            )

        if not chart_height:
            chart_height = y_height_per_measurement * len(columns)
        component_height = legend_height + chart_height
        cur_pos += component_height

        chart_list.append((line_x, pos_top_chart, chart_height))

    total_height = str(cur_pos + 70) + 'px'
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1400px",
            # height="2000px",
            height=total_height,
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )

    for tup in chart_list:
        grid_chart.add(
            tup[0],
            grid_opts=opts.GridOpts(pos_left="4%", pos_right="3%",
                                    pos_top=str(tup[1]), height=tup[2])
        )

    # grid_chart.render(plot_file_name)
    return grid_chart

df_ping_stats_merged = pd.DataFrame(columns=['count', 'mean', 'std', 'min',
                '25%', '50%', '75%', '90%', '95%', '99%', '99.9%',"max"])
print(df_ping_stats_merged)
log_file_name_list = load_all_var_from_file("ping_log_file_name.json")
print("log files = ", log_file_name_list)
for log_file in log_file_name_list:
    with open(log_file, errors='ignore') as file:
        log_content = file.read()

    # parse log file, using partial to avoid Exception thrown
    import time
    print(f'\n>>> Starting parsing:  {log_file}')
    start_time = time.time()
    res = parse_pattern.parse_partial(log_content)
    end_time = time.time()
    # print("\n", parse_name, "parsing time = ", end_time-start_time)
    print(">>>", "parsed, parsing time = ", end_time-start_time)

    if (not res[0]) or (not any(res[0])):
        print("No match for ")
        continue
    else:
        print(">>> Matched")
        # print([res[0]])

    # create a pandas DataFrame from the list of dicts
    df = pd.DataFrame(res[0])
    # cur_ping_stats = df.describe(['time'],percentiles=[.25, .5, .75, .90, .95, .99, .999])
    cur_ping_stats = df['time'].describe(percentiles=[.25, .5, .75, .90, .95, .99, .999])
    print(cur_ping_stats)

    df_ping_stats_merged.loc[log_file] = cur_ping_stats
    print(df_ping_stats_merged)

    ping_stats_txt = os.path.splitext(log_file)[0] + '_stats.txt'
    with open(ping_stats_txt, 'w+') as ping_stats_txt_file:
        # ping_stats_txt_file.write(df.describe(percentiles=[.25, .5, .75, .90, .95, .99, .999]).to_string())
        ping_stats_txt_file.write(cur_ping_stats.to_string())

    csv_raw_file_name = os.path.splitext(log_file)[0] + '.csv'
    # df.to_csv(csv_raw_file_name)

    df['PERF_time'] = df[df.columns[0]]

    y_list = ['time']

    grid_chart = generateChart(y_list,df)
    html_file_name = os.path.splitext(log_file)[0] + '.html'
    grid_chart.render(html_file_name)

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%m%d%H%M%S")
df_ping_stats_merged['count'] = df_ping_stats_merged['count'].astype(int)
df_ping_stats_merged = df_ping_stats_merged.sort_values(by=['mean'])

df_ping_stats_merged.to_csv('/Users/ezhou/Downloads/ping_stats_merged-'+timestampStr+'.csv', float_format='%.2f')

