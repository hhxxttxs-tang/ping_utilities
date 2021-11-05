from parsy import string, regex, seq, ParseError, line_info, success, generate, fail, success, Parser, Result

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from pyecharts import options as opts
from pyecharts.charts import Line, Grid,Tab

import pysnooper

from datetime import datetime
import os, re, time, json, logging

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
    logging.debug("str parsed =\n%s", mark_result[3])
    logging.debug("parsing result = %s", mark_result[1])

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
            if (not cur_ln.startswith('#')) and (not cur_ln.startswith('/')):
                # print(cur_ln)
                return json.loads(cur_ln)

        return None

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
def skip_until_before(target_str):
    p_str = any_str + r'(?=' + target_str + r')'
    # print("search_until: regular expression =", p_str)
    return regex(p_str)

def skip_inline_until_before(target_str):
    p_str = any_str_within_line + r'(?=' + target_str + r')'
    return regex(p_str)

# search for target starting from current pointer
# stream pointer move to after target after the function
# target is returned if found
def search_and_parse(target_str):
    return skip_until_before(target_str) >> parse_current(target_str)

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

# pattern
PCC_leading = r'(\[.*\])*[ \t]*'
SCC_leading = r'(\[.*\])*[ \t]*\[SCC\d*\]'

#parsing the line of PERF
# [06-03 14:15:34]PERF : C(93.8) I(3801) M(H:7.8/6MB/456/709) IC(0) \n
# [06-03 14:15:34] PERF : C(93.8) I(3801) M(H:7.8/6MB/456/709) IC(0) \n
# PERF : C(93.8) I(3801) M(H:7.8/6MB/456/709) IC(0) \n

# PERF_leading = r'(\[.*\])*\s*PERF :'
PERF_leading = r'(\[.*\])*[ \t]*PERF :'
# PERF_leading = PCC_leading + r'PERF :'

# Parser instance:
#   call to its member functions(parse(), parse_partial()) starts the parsing procedure
# parsing procedure output of below Parser instance:
#   A dictionary
PERF_pattern = seq(
    PERF_time = search_and_parse(PERF_leading).map(to_datetime),
    Line_no_in_logfile = success('PCC').mark().map(lambda result:result[0][0]),
    # PERF_note = parse_current(r'.*') << skip_until_EOL,
    CC_type = success('PCC')
)

#parsing the line of FRAME
#[06-03 14:15:34]FRAME: IDLE CAT6/6 TDD(2:7,N) Pos=(272223,272223,272223,272225) STI=7064 \n

FRAME_leading = r'FRAME:'
# FRAME_leading = PCC_leading + FRAME_leading
# FRAME_status = r'\S+'
FRAME_status = r'INACT|IDLE|CONNECTED'
# FRAME_cat = r'CAT\S*'
FRAME_cat = r'CAT\d+/\d+'
FRAME_duplex = r'TDD|FDD'
FRAME_config = r'\(\S+\)'
FRAME_config_strip = lambda s: s[1:-1]

# Parser instance:
#   call to its member functions(parse(), parse_partial()) starts the parsing procedure
# parsing procedure output of below Parser instance:
#   A dictionary, e.g.: {'FRAME_leading': 'YES', 'FRAME_status': 'IDLE', 'FRAME_cat': 'CAT6/5', 'FRAME_duplex': 'TDD'}
FRAME_pattern = seq(
        _FRAME_leading = search_within_block(FRAME_leading, PERF_leading).result('YES'),
        FRAME_status = search_and_parse(FRAME_status),
        FRAME_cat = search_and_parse(FRAME_cat),
        # FRAME_duplex = search_and_parse(FRAME_duplex) << skip_until_EOL
        FRAME_duplex = search_and_parse(FRAME_duplex),
        FRAME_config = parse_current(FRAME_config).map(FRAME_config_strip) << skip_until_EOL,
)

#parsing the line of RF
# [06-03 14:15:34]RF   : E(1150,19150) B2 F19850 AFC(R,1:-110:104,4,H,0x48b) \n
# [06-03 14:15:34]       AGC(N,0x32:31:32,0x39:37:3b,0x30:2f:31,0x37:31:3b) LPF_PWR(0xc3:a4,0xc3:a3,0xc3:a3,0xc3:a3) ACI=1 THM=118 \n
#NOTE:
#   E(1150->Earfcn DL,19150->Earfcn UL) B2->band F19850->MHz DL

RF_leading = r'RF   :'
# RF_leading = PCC_leading + RF_leading
rf_earfcn = r'\d+'
RF_band = r'B\d+'
RF_freq = r'F\d+'
RF_afc = r'AFC.*'
# 'B40' -> 40
RF_band_to_int = lambda a: int(a[1:])
# 'F23900' -> 23900
RF_freq_to_int = RF_band_to_int

RF_pattern = seq(
    _RF_leading = search_within_block(RF_leading, PERF_leading).result('YES'),
    RF_earfcn_dl = skip_until_after(r'E\(') >> parse_current(rf_earfcn).map(int) << skip_current(','),
    RF_earfcn_ul= parse_current(rf_earfcn).map(int) << skip_current('\)'),
    RF_band = search_and_parse(RF_band).map(RF_band_to_int),
    RF_freq_dl = search_and_parse(RF_freq).map(RF_freq_to_int) << skip_until_EOL
    # RF_afc = search_and_parse(RF_afc) << skip_until_EOL
)

#parsing the line of CHAN
# [06-03 14:15:34]CHAN : 20MHz #A2 TM2 PCI=360 DS(S,100,0,0,0/0.2,0.3) ACE(I) FIB(-1:-1:-1:-2) CS(17:17:17:17)

CHAN_leading = r'CHAN :'
# CHAN_leading = PCC_leading + CHAN_leading
# CHAN_bw = r'\d+MHz'
CHAN_bw = r'(?:\d+MHz)|(?:1\.4MHz)'
CHAN_bw_to_str = lambda s : s if s else '-99MHz'
CHAN_enb_tx_ports = r'#A\d'
CHAN_enb_tx_ports_to_int = lambda s : int(s[2:])
CHAN_tm_mode = r'TM\d'
CHAN_tm_mode_to_int = lambda s : int(s[2:])
CHAN_pci = r'PCI\=\d+'
CHAN_pci_to_int = lambda s : int(s.split("=")[1])

CHAN_pattern = seq(
    _CHAN_leading = search_within_block(CHAN_leading, PERF_leading).result('YES'),
    # CHAN_bw = search_and_parse(CHAN_bw),
    # needs to match immediately after CHAN_leading...
    CHAN_bw = skip_current(r'\s*') >> parse_current(CHAN_bw).optional().map(CHAN_bw_to_str),
    CHAN_enb_tx_ports = search_and_parse(CHAN_enb_tx_ports).map(CHAN_enb_tx_ports_to_int),
    CHAN_tm_mode = search_and_parse(CHAN_tm_mode).map(CHAN_tm_mode_to_int),
    CHAN_pci = search_and_parse(CHAN_pci).map(CHAN_pci_to_int) << skip_until_EOL
)

#parsing the line of MEAS
# [06-03 14:15:37]MEAS : CINR(33.4,33.2) RSRP(-57.4,-62.6) RSSI(-31.5,-36.8) RSRQ(-5.9,-5.8)
# [06-03 14:15:37]       CINR(33.3,33.1) RSRP(-57.1,-58.8) RSSI(-31.3,-33.0) RSRQ(-5.8,-5.8) C RPT(33.2,-57.1) pcSINR(38.0)

MEAS_leading = 'MEAS :'
# MEAS_leading = PCC_leading + MEAS_leading
float_val = r'-?\d+\.\d+'
cinr_val = float_val
rsrp_val = float_val

CRRR_items = ['CINR', 'RSRP', 'RSSI', 'RSRQ']
# skip_current(r'\s*') = CINR immediately following "MEAS :"
# skip_current(r'(?:\[.*\])*')) = optional CINR line
CINR_leading = PCC_leading + r'CINR\('


@generate
def MEAS_CRRR_parser():
    res = []
    idx = 0

    while True:
        # Following is much slower than using CRRR_start_flag
        # cinr_found = yield (peek(search_within_block('CINR\(',SCC_leading + '|' + PERF_leading)) | success(""))

        cinr_found = yield (peek(parse_current(CINR_leading)) | success(""))

        if not cinr_found:
            res.append(('MEAS_Rx_num',idx))
            # print(res)
            return dict(res)
        else:
            for item in CRRR_items:
                cur_parser = (skip_until_after(item+'\(') >> parse_current(float_val).map(float) << skip_current(',')).tag('MEAS_'+ item + str(idx))
                cur_res = yield cur_parser
                # print(cur_res)
                res.append(cur_res)

                cur_parser = ( parse_current(float_val).map(float) << skip_current('\)') << skip_current(r'\s*') ).tag('MEAS_'+ item + str(idx+1))
                cur_res = yield cur_parser
                # print(cur_res)
                res.append(cur_res)
            idx += 2

MEAS_pattern = seq(
    _MEAS_leading = search_within_block(MEAS_leading, PERF_leading).result('YES'),
    MEAS_CRRR = MEAS_CRRR_parser,
    MEAS_rpt_CINR = skip_until_after(r'RPT\(') >> parse_current(float_val).map(float) << skip_current(','),
    MEAS_rpt_RSRP = parse_current(float_val).map(float),
    MEAS_cmb_SINR = skip_until_after(r'pcSINR\(') >> parse_current(float_val).map(float) << skip_until_EOL
).map(flatten_dict)

#parsing the line of NMEAS
# NMEAS: S={1150,387,-100.5,-16.5} S={2300,143,-111.0,-47.5}
# [06-03 14:15:34]NMEAS: S={39550,360,-57.0,-6.0} S={2300,143,-111.0,-47.5}  \n \

NMEAS_leading = 'NMEAS:'
# NMEAS_leading = PCC_leading + NMEAS_leading
# float_val = r'-?\d+\.\d+'

#exact match with: "GAP={40:15} \s"
NMEAS_gap = parse_current(r'GAP={\d+:\d+}\s*').times(0,1)
# exact match with: "{39550,360,-57.0,-6.0}  \s  "
NMEAS_val = parse_current(r'{\d+,\d+,-?\d+\.\d+,-?\d+\.\d+}') << skip_current(r'\s*')
# exact match with: "S={39550,360,-57.0,-6.0}  \s  {39550,360,-57.0,-6.0}  \s "
NMEAS_result = skip_current(r'S=') >> NMEAS_val.at_least(1) << skip_current(r'\s*')
# with leading \s
# matched with " \s  S={39550,360,-57.0,-6.0}  \s  "
NMEAS_result_row = skip_current(r'\s*') >> (NMEAS_gap + NMEAS_result.at_least(1))
#match with: "[06-03 14:15:34] \s  S={39550,360,-57.0,-6.0} ... \s
NMEAS_result_row_optional = skip_current(r'(?:\[.*\])*') >> NMEAS_result_row

NMEAS_pattern = seq(
    # NMEAS_leading = parse_current(NMEAS_leading).result('YES'),
    _NMEAS_leading=search_within_block(NMEAS_leading, PERF_leading).result('YES'),
    NMEAS_result = NMEAS_result_row,
    NMEAS_result_more = NMEAS_result_row_optional.many()
)

#parsing the line of L1D
# [17.07 14:43:35.121] L1D  : DCI0/4=(168,0) DCI={2(20/371)}{2(6/254)} BLER(20/371,6/254) Dup(1,1) HI(0/170) CFI(800:0:0:0) TB(0,0) TP=34M
# [17.07 14:43:35.121]        BLER(RV) ={20/370,0/0,0/1,0/0}{6/250,0/0,0/4,0/0}
# [17.07 14:43:35.121]        BLER(RC) ={19/352,1/18,0/1,0/0,0/0,0/0,0/0}{6/249,0/5,0/0,0/0,0/0,0/0,0/0}
# [17.07 14:43:35.121]        BLER(TTI)={0(3/44,2/31),1(1/54,0/31),3(1/45,0/32),4(1/45,1/32),5(6/45,1/32)},
# [17.07 14:43:35.121]                  {6(3/45,1/33),8(1/45,1/32),9(4/48,0/31)}
# [17.07 14:43:35.121]        Layer-Map={1C1L=20/107,1C2L=0/10,2C2L=6/486,2C3L=0/0,2C4L=0/26}, ARBC={35252/24692}, NIR=228384

L1D_leading = r'L1D  :'
# L1D_leading = PCC_leading + L1D_leading


L1D_bler = r'\d+/\d+'
to_bler_percent = lambda ss : round(int(ss.split('/')[0])/int(ss.split('/')[1])*100,2) if (int(ss.split('/')[1]) != 0) else 1

def to_Kbsp(str):
    if not str:
        return np.nan
    if str[-1] == 'M':
        return int(str[:-1])*1024
    elif str[-1] == 'K':
        # return round(int(str[:-1])/1024.,3)
        return int(str[:-1])
    else:
        return round(int(str)/1024,3)

L1D_tp = r'\d+M|\d+K|\d+'

L1D_pattern = seq(
    _L1D_leading = search_within_block(L1D_leading, PERF_leading).result('YES'),
    L1D_bler_tb1 = peek(skip_until_after(r'BLER\(') >> parse_current(L1D_bler).map(to_bler_percent) << skip_current(r',')),
    L1D_total_tb1 = skip_until_after(r'BLER\(') >> skip_current(r'\d+/') >> parse_current(r'\d+') << skip_current(r','),
    L1D_bler_tb2 = peek(parse_current(L1D_bler).map(to_bler_percent) << skip_current(r'\)')),
    L1D_total_tb2 = skip_current(r'\d+/') >> parse_current(r'\d+') << skip_current(r'\)'),
    L1D_tp_kbps = skip_until_after(r'TP=') >> parse_current(L1D_tp).map(to_Kbsp) << skip_until_EOL
)

#CSI
# CSI  : C(AP0,S1) A30(0:0), P10(6:0), RI(3,0,0,0) CQI={15(3)}{}
CSI_leading = r'CSI  :'
CSI_RI = r'\d+'
CSI_pattern = seq(
    _CSI_leading = search_within_block(CSI_leading, PERF_leading).result('YES'),
    CSI_RI_1 = skip_until_after(r'RI\(') >> parse_current(CSI_RI) << skip_current(r','),
    CSI_RI_2 = parse_current(CSI_RI) << skip_current(r','),
    CSI_RI_3 = parse_current(CSI_RI) << skip_current(r','),
    CSI_RI_4 = parse_current(CSI_RI) << skip_until_EOL
)

# TP   : PHY(12K:8141K) MAC(12K:4580K/0) RLC(104:4574K) PDCP(66:4519K)
TP_leading = r'TP   :'
TP_phy = L1D_tp

TP_pattern = seq(
    _TP_leading = search_within_block(TP_leading, PERF_leading).result('YES'),
    TP_phy_dl_kbps = skip_until_after(r'PHY\(') >> parse_current(TP_phy).map(to_Kbsp) << skip_current(r':'),
    TP_phy_ul_kbps= parse_current(TP_phy).map(to_Kbsp) << skip_until_EOL
)


#SCC
#parsing the line of PERF
# [17.07 14:43:35.121] [SCC1]FRAME: SC1(1) ACT=1 FDD(N) Pos=(113513,113513) STI=3991
#[SCC1]FRAME: SC1(1) ACT=1 FDD(N) Pos=(113513,113513) STI=3991

# SCC_FRAME_leading = r'(\[.*\])*\s*\[SCC\d*\]FRAME:'
SCC_FRAME_leading = r'(\[.*\])*[ \t]*\[SCC\d*\]FRAME:'
SCC_FRAME_act = r'ACT=[01]'
SCC_FRAME_duplex = FRAME_duplex

SCC_FRAME_pattern = seq(
    # PERF_time=search_and_parse(SCC_FRAME_leading).map(to_datetime),
    PERF_time = search_within_block(SCC_FRAME_leading,PERF_leading).map(to_datetime),
    Line_no_in_logfile=success('SCC').mark().map(lambda result: result[0][0]),
    FRAME_status = search_and_parse(SCC_FRAME_act),
    FRAME_duplex = search_and_parse(SCC_FRAME_duplex),
    FRAME_note = parse_current(r'.*') << skip_until_EOL,
    # FRAME_status = success("ToBeParsed"),
    CC_type = success('SCC')
)

#Any pattern in the seq is not matched, the whole sequence is not matched
# description:
#    https://parsy.readthedocs.io/en/latest/ref/methods_and_combinators.html?highlight=parsy.seq#parsy.seq

# TODO: use times(0,1) or optional()??
# PCC_block = seq(PERF_pattern,
#                    FRAME_pattern.times(0,1).combine(merge_dict),
#                    RF_pattern.times(0,1).combine(merge_dict),
#                    CHAN_pattern.times(0,1).combine(merge_dict),
#                    MEAS_pattern.times(0,1).combine(merge_dict),
#                    NMEAS_pattern.times(0,1).combine(merge_dict),
#                    L1D_pattern.times(0,1).combine(merge_dict),
#                    TP_pattern.times(0,1).combine(merge_dict)) \
#     .combine(merge_dict) \
#     .many()

PCC_block = seq(PERF_pattern,
                   FRAME_pattern.optional(),
                   RF_pattern.optional(),
                   CHAN_pattern.optional(),
                   MEAS_pattern.optional(),
                   NMEAS_pattern.optional(),
                   L1D_pattern.optional(),
                   CSI_pattern.optional(),
                   TP_pattern.optional()) \
    .combine(merge_dict)
    # .many()

SCC_block = seq(SCC_FRAME_pattern,
                   RF_pattern.times(0,1).combine(merge_dict),
                   CHAN_pattern.times(0,1).combine(merge_dict),
                   MEAS_pattern.times(0,1).combine(merge_dict),
                   NMEAS_pattern.times(0,1).combine(merge_dict),
                   L1D_pattern.times(0,1).combine(merge_dict),
                   CSI_pattern.times(0, 1).combine(merge_dict)) \
    .combine(merge_dict)
    # .many()

PCC_block_PERF_only = PERF_pattern
keep_SCC_only = lambda left, right: right if right else {}

parse_block = {
    "PCC":PCC_block.many(),

    # purpose: SCC result can be aligned with PCC in case there is no timestamp
    # some log file might not strictly follow below rules(1 PCC + 1 SCC)
    # e.g:
    #   1PCC + 2SCC, in which case half of the SCC will not be parsed
    #   to get the complete list in this case:
    #       1. use orginal SCC parser ["SCC":SCC_block.many()]
    #       2. PERF_time = search_and_parse(SCC_FRAME_leading).map(to_datetime),
    # Note:
    #   The following does not work, becuase it returns "None" when SCC does not present. The return is supposed to be "{}"
    #       "SCC": (PCC_block >> (SCC_block.optional())).many()

    # "SCC":seq(PCC_block_PERF_only, SCC_block.optional()).combine(keep_SCC_only).many(),
    # "SCC":seq(PCC_block_PERF_only, SCC_block.optional()).mark().map(log_mark).combine(keep_SCC_only).many(),

    # original SCC parser
    #   need to use together with: PERF_time = search_and_parse(SCC_FRAME_leading).map(to_datetime),
    # "SCC":SCC_block.many()

}



# [2020-08-18 19:24:39]<4>[353] eth-ul: 00:0b:2f:16:7b:15->00:0b:2f:16:7b:6e 0800(IPv4)
# [2020-08-18 19:24:39]<4>  tot_len=60
# [2020-08-18 19:24:39]<4>  protocol=1(ICMP)
# [2020-08-18 19:24:39]<4>  id=b25d(45661)
# [2020-08-18 19:24:39]<4>  check=069f
# [2020-08-18 19:24:39]<4>  IP: 192.168.0.91->192.168.0.25
# [2020-08-18 19:24:39]<4>  ICMP: type=8(Ping Request) code=0 csum=4f54 id=1 seq=65030 uptime=316.640
#
# [2020-08-18 19:24:39]<4>[355] lte-ul: IPv4
# [2020-08-18 19:24:39]<4>  tot_len=98
# [2020-08-18 19:24:39]<4>  frag=2 frag_off=0(0)
# [2020-08-18 19:24:39]<4>  protocol=47(GRE)
# [2020-08-18 19:24:39]<4>  id=b25d(45661)
# [2020-08-18 19:24:39]<4>  check=10f0
# [2020-08-18 19:24:39]<4>  IP: 172.16.15.133->172.16.15.122
# [2020-08-18 19:24:39]<4>  TUNNEL: 192.168.0.91->192.168.0.25
# [2020-08-18 19:24:39]<4>  ICMP: type=8(Ping Request) code=0 csum=4f54 id=1 seq=65030 uptime=316.645
# [2020-08-18 19:24:39]<4>  lte0pdn0(0x10) hdr(00:05) len=100 nr=2178/2180
#
# [2020-08-18 19:24:39]<4>[356] lte-dl: IPv4
# [2020-08-18 19:24:39]<4>  tot_len=98
# [2020-08-18 19:24:39]<4>  frag=2 frag_off=0(0)
# [2020-08-18 19:24:39]<4>  protocol=47(GRE)
# [2020-08-18 19:24:39]<4>  id=8d9f(36255)
# [2020-08-18 19:24:39]<4>  check=37ae
# [2020-08-18 19:24:39]<4>  IP: 172.16.15.122->172.16.15.133
# [2020-08-18 19:24:39]<4>  TUNNEL: 192.168.0.25->192.168.0.91
# [2020-08-18 19:24:39]<4>  ICMP: type=0(Ping Reply) code=0 csum=5754 id=1 seq=65030 uptime=316.732
# [2020-08-18 19:24:39]<4>        t=86ms
# [2020-08-18 19:24:39]<4>  lte0pdn0 hdr(0x0) len=100 nr=3291
#
# [2020-08-18 19:24:39]<4>[358] eth-dl: 00:0b:2f:16:7b:6e->00:0b:2f:16:7b:15 0800(IPv4)
# [2020-08-18 19:24:39]<4>  tot_len=60
# [2020-08-18 19:24:39]<4>  protocol=1(ICMP)
# [2020-08-18 19:24:39]<4>  id=8d9f(36255)
# [2020-08-18 19:24:39]<4>  check=6b5d
# [2020-08-18 19:24:39]<4>  IP: 192.168.0.25->192.168.0.91
# [2020-08-18 19:24:39]<4>  ICMP: type=0(Ping Reply) code=0 csum=5754 id=1 seq=65030 uptime=316.739
# [2020-08-18 19:24:39]<4>        t=97ms



icmp_leading = r'\[.*\]\s*\<\d+\>\s*'
icmp_print_id = r'\[\d+\] '
icmp_to_print_id = lambda s: int(s[1:-2])
icmp_interfaces = r'(?:eth-ul|lte-ul|lte-dl|eth-dl)\:'
icmp_to_interface_str = lambda s: s[:-1]
icmp_marker = icmp_leading + icmp_print_id + icmp_interfaces
float_val = r'-?\d+\.\d+'

icmp_pattern = seq(
    _search_icmp_marker = skip_until_before(icmp_marker),
    icmp_print_id = skip_current(icmp_leading) >> parse_current(icmp_print_id).map(icmp_to_print_id),
    icmp_interface = parse_current(icmp_interfaces).map(icmp_to_interface_str) << skip_until_EOL,
    _search_icmp_line = search_within_block(r'ICMP\:', icmp_marker) | success('failed'),
    icmp_id = skip_inline_until_after('id\=') >> parse_current(r'\d+') | success('-99'),
    icmp_seq = skip_inline_until_after(r'seq\=') >> parse_current(r'\d+') | success('-99'),
    icmp_tm = skip_inline_until_after(r'uptime\=')  >> parse_current(float_val).map(float)  << skip_until_EOL | success('-99')
).many()

#The following works too
# icmp_pattern = seq(
#     _search_icmp_marker = skip_until_before(icmp_marker),
#     icmp_print_id = skip_current(icmp_leading) >> parse_current(icmp_print_id).map(icmp_to_print_id),
#     icmp_interface = parse_current(icmp_interfaces).map(icmp_to_interface_str) << skip_until_EOL,
#     _search_icmp_line = (search_within_block(r'ICMP\:', icmp_marker)).optional() ,
#     icmp_id = (skip_inline_until_after('id\=') >> parse_current(r'\d+')).optional(),
#     icmp_seq = (skip_inline_until_after(r'seq\=') >> parse_current(r'\d+')).optional(),
#     icmp_tm = (skip_inline_until_after(r'uptime\=')  >> parse_current(float_val).map(float) << skip_until_EOL).optional()
# ).many()


def generateChart(list_of_columns, df):
    print("in generateChart: list_of_columns = ", list_of_columns)
    # minimum 25 on my laptop
    legend_height = 25
    # 50 looks well on my laptop, better to be >30
    y_height_per_measurement = 30

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


log_file = load_var_from_file("log_file_name_rtt.json")

print("log file = ", log_file)

with open(log_file, errors='ignore') as file:
    log_content = file.read()


import time
print("\n>>>","parsing started....")
start_time = time.time()
res = icmp_pattern.parse_partial(log_content)
end_time = time.time()
# print("\n", parse_name, "parsing time = ", end_time-start_time)
print("\n>>>", "parsed, parsing time = ", end_time-start_time)

if (not res[0]) or (not any(res[0])):
    print("No match for ", 'icmp')
else:
    print(">>> Matched for ", 'icmp')

df = pd.DataFrame(res[0])
csv_raw_file_name = os.path.splitext(log_file)[0] + '_' + 'icmp' + '_raw.csv'
df.to_csv(csv_raw_file_name)
# print("res[1] = \n")
# print(res[1])

df_id_filter = df[(df['icmp_id'] == '61515' )]
print(df_id_filter.columns)

column_names = ["icmp_id", "icmp-seq", "eth-ul", "lte-ul", "lte-dl", "eth-dl","delta-eth","delta-lte", "delta-cpe-a"]
df_final = pd.DataFrame(columns=column_names)
print(df_final.index)

eth_ul = None
lte_ul = None
lte_dl = None
eth_dl = None

cur_icmp_seq = None

for _, row in df_id_filter.iterrows():
    dict_row = dict(row)
    print(dict_row)
    if dict_row['icmp_id']=='-99' or dict_row['icmp_seq']=='-99' or dict_row['icmp_tm']=='-99':
        print(dict_row)
        print("invalid row")
        continue

    if cur_icmp_seq != dict_row['icmp_seq']:
        print("seq id changed!!!!")
        print("cur row = ", ['61515',cur_icmp_seq, eth_ul, lte_ul, lte_dl, eth_dl])
        print("\n")
        # new seq started, insert new row into the DF
        if eth_ul and lte_ul and lte_dl and eth_dl:
            delta_eth = eth_dl*1000 - eth_ul*1000
            delta_lte = lte_dl*1000 - lte_ul*1000
            delta_cpe_a = delta_eth - delta_lte
            print("add new row to DF", ['61515',cur_icmp_seq, eth_ul, lte_ul, lte_dl, eth_dl, delta_eth, delta_lte,delta_cpe_a])
            s = pd.Series(['61515',cur_icmp_seq, eth_ul, lte_ul, lte_dl, eth_dl,delta_eth, delta_lte,delta_cpe_a], index=df_final.columns)
            df_final = df_final.append(s, ignore_index=True)

        # init for new seq
        eth_ul = None
        lte_ul = None
        lte_dl = None
        eth_dl = None
        cur_icmp_seq = dict_row['icmp_seq']

    if dict_row['icmp_interface'] == 'eth-ul':
        eth_ul =  dict_row['icmp_tm']
    if dict_row['icmp_interface'] == 'lte-ul':
        lte_ul =  dict_row['icmp_tm']
    if dict_row['icmp_interface'] == 'lte-dl':
        lte_dl =  dict_row['icmp_tm']
    if dict_row['icmp_interface'] == 'eth-dl':
        eth_dl = dict_row['icmp_tm']

print(df_final)
csv_final_file_name = os.path.splitext(log_file)[0] + '_' + 'icmp' + '_final.csv'
df_final.to_csv(csv_final_file_name)
print("num of row of ping records filter out = ", len(df_id_filter))
print("num of row of ping analysis result = ", len(df_final))

print("\nSummary statistics of delta-lte:")
print(df_final["delta-lte"].describe())

print("\nSummary statistics of delta-cpe-a:")
print(df_final["delta-cpe-a"].describe())


exit(0)


tab = Tab()
for parse_name, parse_pattern in parse_block.items():
    # parse log file, using partial to avoid Exception thrown
    import time
    print("\n>>>", parse_name, "parsing started....")
    start_time = time.time()
    res = parse_pattern.parse_partial(log_content)
    end_time = time.time()
    # print("\n", parse_name, "parsing time = ", end_time-start_time)
    print("\n>>>", parse_name, "parsed, parsing time = ", end_time-start_time)

    if (not res[0]) or (not any(res[0])):
        print("No match for ", parse_name)
        continue
    else:
        print(">>> Matched for ", parse_name)

    # print matched and un-matched parts of log
    # print("\nmatched =\n", res[0])
    # print('type = ', type(res[0]), 'len = ', len(res[0]))

    #
    # print("\nUN-matched =\n", res[1])

    # create a pandas DataFrame from the list of dicts
    df = pd.DataFrame(res[0])
    # csv_raw_file = log_file.replace('.log', '_' + parse_name + '_raw.csv')
    csv_raw_file_name = os.path.splitext(log_file)[0] + '_' + parse_name + '_raw.csv'

    if parse_name == 'SCC':
        # following filter is based on below columns
        cols_to_int = ['RF_band', 'RF_earfcn_dl', 'RF_earfcn_ul', 'RF_freq_dl', 'CHAN_pci']
        df[cols_to_int] = df[cols_to_int].astype('Int64')


    df.to_csv(csv_raw_file_name)

    # add column: 'MEAS_Rx_num'
    if 'MEAS_Rx_num' in df.columns:
        # add columns for noise/interference
        ideal_noise_floor = -94
        # ideal_noise_floor = -97  # 94 for 20Mhz, 97 for 10Mhz
        # The following not working any more for SCC
        #   MEAS_Rx_num changed to float due to nan in empty line(where PCC found while SCC not)
        # CRRR_max_num = max(df['MEAS_Rx_num'])
        CRRR_max_num = int(df['MEAS_Rx_num'].max())
        for idx in range(CRRR_max_num):
            s_idx = str(idx)
            df["MEAS_NI_INF" + s_idx] = (df['MEAS_RSSI'+s_idx] - df['MEAS_CINR'+s_idx] - ideal_noise_floor).round(1)

    # add column: 'FRAME_status_val'
    status_map_int = {
        'IDLE': 0,
        'CONNECTED': 1,
        'INACT': -1,
        'ACT=0': 0,
        'ACT=1': 1,
        np.nan: np.nan
    }
    # TODO: "SettingWithCopyWarning" with test_data/putty-01.log
    df['FRAME_status_val'] = df['FRAME_status'].apply(
        lambda x: status_map_int[x] if x in status_map_int else -99)

    # setup filter of "col_freq"
    # print information of dataframe for reference(to screen and file)
    cols_freq = ['RF_band', 'RF_earfcn_dl', 'RF_earfcn_ul', 'RF_freq_dl', 'CHAN_bw', 'CHAN_pci', 'FRAME_duplex']
    df_freq = df[cols_freq].drop_duplicates()
    print_out_freq = parse_name + " freq list(No duplicates):\n" + \
        df_freq.to_string() + \
        '\n\n'
    print(print_out_freq)

    # add column: 'PCI_global_index', 'PCI_global_str'
    # df['PCI_global_index'] = np.nan
    # df['PCI_global_str'] = np.nan
    # df['PCI_global_index'] = df['PCI_global_index'].astype('Int64')

    # cur_pci_global_val = 1
    for _, row in df_freq.iterrows():
        # skip rows like below:
            #     RF_band  RF_earfcn_dl  RF_earfcn_ul  RF_freq_dl CHAN_bw  CHAN_pci FRAME_duplex
            # 0       NaN           NaN           NaN         NaN     NaN       NaN          NaN
        if pd.isnull(row['CHAN_bw']):
            continue

        filter = dict(row)
        filter_str = " ".join(("{}:{}".format(*i) for i in filter.items()))
        filter_val_str = "_".join((str(i) for i in filter.values()))

        df['PCI='+ filter_val_str] = 0 # if assigned with np.nan, certian pci is not able to show correctly???
        df.loc[(df[list(filter)] == pd.Series(filter)).all(axis=1),['PCI='+ filter_val_str]] = 1


        # df.loc[(df[list(filter)] == pd.Series(filter)).all(axis=1),['PCI_global_index']] = cur_pci_global_val
        # df.loc[(df[list(filter)] == pd.Series(filter)).all(axis=1),['PCI_global_str']] = filter_val_str
        # cur_pci_global_val += 1

    df['index'] = df.index

    PCI_col_list = [c for c in df.columns if c.startswith("PCI=")]
    tab.add(generateChart([PCI_col_list,['Line_no_in_logfile']], df), parse_name+ ' dashboard')

    # save dataFrame to file(.csv,etc)
    csv_file_name = os.path.splitext(log_file)[0] + '_' + parse_name + '.csv'
    df.to_csv(csv_file_name)

    #setup filter of "cols_freq_stats"
    cols_freq_stats = cols_freq + ['FRAME_status']
    # if parse_name == 'PCC':
    df_freq_stats = df[cols_freq_stats].drop_duplicates()
    print_out_freq_stats = parse_name + " freq list with status(No duplicates):\n" + \
        df_freq_stats.to_string() + \
        '\n\n'
    print(print_out_freq_stats)

    #setup filter of "cols_freq_stats_time"
    cols_freq_stats_time = ['PERF_time'] + cols_freq_stats
    df_freq_stats_time = df[df.index.isin(df_freq_stats.index)][cols_freq_stats_time]
    print_out_freq_stats_time = parse_name + " freq list with status, time(No duplicates):\n" + \
        df_freq_stats_time.to_string() + \
        '\n\n'
    print(print_out_freq_stats_time)

    #print out df.info and df.head
    print('df.info():\n', df.info(), "\n")
    print('df.head():\n', df.head())

    #write to file
    # ref_txt_fn_name = log_file.replace('.log', '_' + parse_name + '.txt')
    ref_txt_fn_name = os.path.splitext(log_file)[0] + '_' + parse_name + '.txt'
    with open(ref_txt_fn_name, 'w+') as ref_txt_file:
        ref_txt_file.write(print_out_freq)
        ref_txt_file.write(print_out_freq_stats)
        ref_txt_file.write(print_out_freq_stats_time)

        # write df.info() to text file
        import io
        buffer = io.StringIO()
        df.info(buf=buffer)
        ref_txt_file.write('df.info():\n' + buffer.getvalue() + '\n')

        ref_txt_file.write('df.head():\n'+ df.head().to_string())



    if not 'PERF_time' in df.columns:
        continue

    # extract time only from datetime for better show on plot
    # if PERF_time is in foramt as: '1970-06-03 14:15:35',
    # if not, change lamda accordingly
    # df['PERF_time'] = df['PERF_time'].apply(lambda x: x.split()[1])
    # df['PERF_time'] = df['PERF_time'].apply(lambda x: x.split()[1] if not pd.isnull(x) else x)

    # "2020-04-29 11:54:54.144" -> "04-29 11:54:54.144"
    df['PERF_time'] = df['PERF_time'].apply(lambda x: x[5:] if not pd.isnull(x) else x)
    # df['PERF_time'] = pd.to_datetime(df['PERF_time'])

    for _, row in df_freq.iterrows():
        print("\n")

        # skip rows like below:
            #     RF_band  RF_earfcn_dl  RF_earfcn_ul  RF_freq_dl CHAN_bw  CHAN_pci FRAME_duplex
            # 0       NaN           NaN           NaN         NaN     NaN       NaN          NaN
        if pd.isnull(row['CHAN_bw']):
            continue

        filter = dict(row)
        filter_str = " ".join(("{}:{}".format(*i) for i in filter.items()))
        filter_val_str = "_".join((str(i) for i in filter.values()))

        print("filter = ", filter_str)

        # df_f_out = df.loc[(df[list(filter)] == pd.Series(filter)).all(axis=1)]
        df_f_out = df.copy(deep=True)
        df_f_out.loc[(df_f_out[list(filter)] != pd.Series(filter)).any(axis=1)] = np.nan

        # print("%d of rows filtered out(list of index followed): " % (len(df_f_out.index.tolist())))
        # print(str(df_f_out.index.tolist()))
        df_f_out_csv_fn = os.path.splitext(log_file)[0] + '_' + parse_name + '_' + filter_val_str + '.csv'
        df_f_out.to_csv(df_f_out_csv_fn)

        with open(ref_txt_fn_name, 'a+') as ref_txt_file:
            ref_txt_file.write("\n\nfilter = " + filter_str)
            # ref_txt_file.write("\n%d of rows filtered out(list of index followed): " % (len(df_f_out.index.tolist())))
            # ref_txt_file.write('\n' + str(df_f_out.index.tolist()))

        status_map_int = {
            'IDLE': 0,
            'CONNECTED':1,
            'INACT':-1,
            'ACT=0':0,
            'ACT=1':1,
             np.nan:np.nan
        }
        # TODO: "SettingWithCopyWarning" with test_data/putty-01.log
        df_f_out['FRAME_status'] = df_f_out['FRAME_status'].apply(lambda x: status_map_int[x] if x in status_map_int else -99)


        y_list = load_var_from_file("y_list.json")
        y_mean_list = load_var_from_file("y_mean_list.json")

        # "x_item = None" means x_axis is index #
        x_item = None
        print("\nx_item = ", x_item, "\nylist_configured = ", y_list, "\ny_mean_list_configured = ", y_mean_list)


        df_f_out['index'] = df_f_out.index
        tab_label = parse_name + '_' + filter_val_str
        grid = generateChart(y_list, df_f_out)
        tab.add(grid, tab_label)

tab_fig_filename = os.path.splitext(log_file)[0] + '.html'
tab.render(tab_fig_filename)

