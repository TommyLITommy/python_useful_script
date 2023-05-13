import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import sys

from matplotlib.font_manager import FontProperties  # 步骤一
font = FontProperties(fname=r"c:\windows\fonts\simsun.ttc", size=14)  # 步骤二

MAX_RANGING_COUNT = 0xFFFFFFFF

REAL_RANGING_COUNT = MAX_RANGING_COUNT 

#RANGING_INTERVAL = 10 * 1000
RANGING_INTERVAL = None

LOG_FILE_EXTENSION = ".log"

CAL_RANGING_CNT_USING_SEQ_NUM = 0

'''
[22-10-57-12,045] 602457300 | [APP][INFO]DS-TWR Responder SEQ NUM 12514
[22-10-51-50,573] 286387350 | [APP][INFO]Raw Distance 344cm, AoA azimuth -31 FoM 5
[30-18-20-40,795] 672567150 | [APP][INFO]Peer AAA1, Distance 534cm, AoA azimuth 30
'''
output_csv = "output\\csv\\"
output_png = "output\\png\\"

title_array =   [
                    ["Raw Distance", "Filtered Distance"],
                    ["Raw Azimuth", "Filterted Azimuth"]
                ]

x_label_array = ["Distance", "Azimuth"]

RAW_DISTANCE_RE_PATTERN = "Raw Distance"
FILTERED_DISTANCE_RE_PATTERN = "Peer .* Distance"

DISPLAY_MODE_RAW_DISTANCE_ONLY = 0
DISPLAY_MODE_FILTERED_DISTANCE_ONLY = 1
DISPLAY_MODE_RAW_AOA_ONLY = 2
DISPLAY_MODE_FILTERED_AOA_ONLY = 3
DISPLAY_MODE_DISTANCE_ONLY = 4
DISPLAY_MODE_AOA_ONLY = 5
DISPLAY_MODE_DISTANCE_AND_AOA = 6

DISPLAY_MODE = DISPLAY_MODE_RAW_DISTANCE_ONLY

PER = -1

log_file_info_list = []

rssi_list = []
snr_list = []
rx_fail_list = []

def statistic_ranging_count_using_seq_num(seq_num_list):
    ranging_count = 0
    last_seq_num = -1
    if len(seq_num_list) < 20:
        return 0

    for current_seq_num in seq_num_list:
        if last_seq_num == -1:
            last_seq_num = current_seq_num

        if current_seq_num > last_seq_num:
            ranging_count = ranging_count + (current_seq_num - last_seq_num)
        
        if current_seq_num < last_seq_num:
            ranging_count = ranging_count + (65535 - last_seq_num) + current_seq_num #Attention need check again
        
        last_seq_num = current_seq_num
    print("seq_num -> ranging_count:%d" %ranging_count)
    print("seq_num_list[-1]:%d - seq_num_list[0]:%d = %d" %(seq_num_list[-1], seq_num_list[0], seq_num_list[-1] - seq_num_list[0]))
    return ranging_count

def statistic_ranging_count_using_timestamp(timestamp_list):

    if len(timestamp_list) == 0:
        return 0

    total_ranging_period = 0
    first_timestamp = timestamp_list[0]
    last_timestamp = -1

    for current_timestamp in timestamp_list:
        if last_timestamp == -1:
            last_timestamp = current_timestamp
        
        if current_timestamp < last_timestamp:
            total_ranging_period = total_ranging_period + (last_timestamp - first_timestamp)
            first_timestamp = 0

        if current_timestamp == timestamp_list[-1]:
            total_ranging_period = total_ranging_period + (current_timestamp - first_timestamp)
        
    print("total_rangign_period:%d" %total_ranging_period)
    ranging_count = total_ranging_period / RANGING_INTERVAL
    return ranging_count

def extract_timestamp(timestamp_list, line):
    tmp_timestamp_re = re.search(r'\d{10}', line) # \d{9}匹配9个\d
    if tmp_timestamp_re:
        timestamp = int(tmp_timestamp_re.group(0))
        #print("timestamp:", timestamp)
        timestamp_list.append(timestamp)

def extract_sequence_num(seq_num_list, line):
    #print("func:%s, line:%d" %(sys._getframe().f_code.co_name, sys._getframe().f_lineno))
    tmp_sequence_re = re.search(r'SEQ NUM (\d+$)', line, re.I) #re.I ignore case
    if tmp_sequence_re:
        seq_num = int(tmp_sequence_re.group(1))
        #print(seq_num)
        seq_num_list.append(seq_num)

def extract_distance_and_azimuth(csv_file_name_ob, distance_pattern_string, distance_list, azimuth_list, input_line):
    tmp_distance_re = re.search(r'%s (\d+)cm' %distance_pattern_string, input_line)
    tmp_azimuth_re = re.search(r'AoA azimuth (-?\d+)', input_line)

    if tmp_distance_re:
        distance = int(tmp_distance_re.group(1))
        #distance /= 100
        if tmp_azimuth_re:
            #print(tmp_azimuth_re.group(0))
            azimuth = int(tmp_azimuth_re.group(1))
            #print('%.02fm %d' % (distance, azimuth))
            distance_list.append(distance)
            azimuth_list.append(azimuth)
            csv_file_name_ob.write('%.02f,%d\n' % (distance, azimuth))
        else:
            #print('%.02fm' % (distance))
            distance_list.append(distance)
            csv_file_name_ob.write('%.02f\n' % (distance))

def extract_rx_fail(rx_fail_list, line):
    rx_fail_pattern = re.search(r"UWB RX fail  0x(\d+)", line)
    if rx_fail_pattern:
        rx_fail_list.append(int(rx_fail_pattern.group(1), 16))

def extract_rssi_snr(rssi_list, snr_list, line):
    rssi_snr_pattern = re.search(r"RSSI: (-?\d+)dBm, SNR: (-?\d+)dB", line)
    if rssi_snr_pattern:
        rssi = int(rssi_snr_pattern.group(1))
        snr = int(rssi_snr_pattern.group(2))
        # print("rssi:%d, snr:%d" %(rssi, snr))
        rssi_list.append(rssi)
        snr_list.append(snr)

def calculate_percentage(data_list, lower_limit, upper_limit):
    in_range_count = 0
    for item in data_list:
        if item >= lower_limit and item <= upper_limit:
            in_range_count += 1

    percentage = (in_range_count / len(data_list)) * 100
    return percentage

def draw_histgram(axs, title, x_label, data):
    global PER
    global rssi_list
    global snr_list
    global rx_fail_list

    Min = min(data)
    Max = max(data)
    print("Min:%d, Max:%d" %(Min, Max))
    Delta = Max - Min
    Mean = np.mean(data)
    Var = np.var(data)
    Std = np.std(data)

    sigma = 5
    three_sigma_left = Mean - 3 * sigma
    three_sigma_right = Mean + 3 * sigma

    two_sigma_left = Mean - 2 * sigma
    two_sigma_right = Mean + 2* sigma
    
    one_sigma_left = Mean - sigma
    one_sigma_right = Mean + sigma

    one_sigma_percentage = calculate_percentage(data, one_sigma_left, one_sigma_right)
    two_sigma_percentage = calculate_percentage(data, two_sigma_left, two_sigma_right)
    three_sigma_percentage = calculate_percentage(data, three_sigma_left, three_sigma_right)

    print("-3sigma:%f, +3sigma:%f" %(three_sigma_left, three_sigma_right))
    print("-2sigma:%f, +2sigma:%f" %(two_sigma_left, two_sigma_right))
    print("-1sigma:%f, +1sigma:%f" %(one_sigma_left, one_sigma_right))

    xticks_list = np.arange(0, 1000, 10)
    # print("xticks_list:",xticks_list)
    axs.set_xticks(xticks_list)
    
    axs.set_title(title, fontsize=20, color="green")
    axs.set_xlabel(x_label, fontsize=20)

    combined_array = data + [three_sigma_left, three_sigma_right]
    x_lim_min = min(combined_array) - Std
    x_lim_max = max(combined_array) + Std
    axs.set_xlim(x_lim_min, x_lim_max)

    count_list = pd.value_counts(data).sort_index()
    # print(count_list)
    count_list = count_list.to_list()
    data = set(data)
    data = list(data)
    data.sort()
    
    max_count = max(count_list)
    step = 100
    if max_count >= 1000:
        step = 100
    elif max_count >= 100:
        step = 30
    else:
        step = 10
    print("max_count:%d, step:%d" %(max_count, step))
    yticks_list = np.arange(0, 2000, step)
    axs.set_yticks(yticks_list)

    color_list = []
    for value in data:
        color = 'blue'
        if value >= one_sigma_left and value <= one_sigma_right:
            color = 'black'

        if (value >= two_sigma_left and value < one_sigma_left)  or (value > one_sigma_right and value <= two_sigma_right):
            color = 'green'

        if (value >= three_sigma_left and value < two_sigma_left) or (value > two_sigma_right and value <= three_sigma_right):
            color =  'red'

        color_list.append(color)

    # print("len(data):%d, len(count_list):%d" %(len(data), len(count_list)))
    # print(data)
    # print(count_list)
    axs.bar(data, count_list, color=color_list)
    
    one_sigma = mpatches.Patch(color='black', label='1\u03C3')
    two_sigma = mpatches.Patch(color='green', label='2\u03C3')
    three_sigma = mpatches.Patch(color='red', label='3\u03C3')
    axs.legend(handles=[one_sigma,two_sigma,three_sigma], loc='upper right')

    # axs.legend(loc='upper right')

    if x_label == "Distance":
        unit = "cm"
    else:
        unit = "deg"

    BD_err = 0
    SFD_err = 0
    PHR_err = 0
    PLD_err = 0
    TO_err = 0

    for i in rx_fail_list:
        if (i >> 4) & 0x1:
            BD_err += 1

        elif (i >> 3) & 0x1:
            SFD_err += 1

        elif (i >> 2) & 0x1:
            PHR_err += 1

        elif (i >> 1) & 0x1:
            PLD_err += 1
        
        else:
            TO_err += 1

    rx_fail_str = "\nerror counter:\nBD_ERR=%d\nSFD_ERR=%d\nPHR_ERR=%d\nPLD_ERR=%d\nTO_ERR=%d" %(BD_err, SFD_err, PHR_err, PLD_err, TO_err)

    textstr = '\n'.join((
        r'min=%d%s' % (Min, unit),
        r'max=%d%s' % (Max, unit),
        r'delta=%d%s' %(Delta, unit),
        r'mean=%.2f%s' % (Mean, unit),
        # r'Var=%.4f' % (Var),
        '\nSTD=%.4f' % (Std),
        '\n1\u03C3=%.4f%%'%(one_sigma_percentage),
        '2\u03C3=%.4f%%'%(two_sigma_percentage),
        '3\u03C3=%.4f%%'%(three_sigma_percentage),
        '\nPER=%s%%' %(PER),
        "\nAVG_RSSI=%d" %(np.mean(rssi_list)),
        r"AVG_SNR=%d" %(np.mean(snr_list)),
        ))

    if len(rx_fail_list) != 0:
        textstr += "\n%s" %(rx_fail_str)

    # these are matplotlib.patch.Patch properties
    props = dict(boxstyle='round', facecolor='lightblue', alpha=0.5)

    # place a text box in upper left in axes coords
    axs.text(0.02, 0.98, textstr, transform=axs.transAxes, fontsize=15, verticalalignment='top', bbox=props, color="black")


def calculate_per(raw_distanace_list, rx_fail_list):
    ranging_count = len(raw_distanace_list) + len(rx_fail_list)
    PER = (len(rx_fail_list) / ranging_count) * 100
    print("rx_fail_count:%d, successful_count:%d" %(len(ranging_interval_list), len(rx_fail_list)))
    return PER

first_seq_num = -1
first_seq_num_timestamp = -1
ranging_interval_list = []

last_seq_num = -1
last_seq_num_timestamp = -1

def calculate_ranging_interval_through_timestamp(line):
    global RANGING_INTERVAL
    global last_seq_num
    global last_seq_num_timestamp
    tmp_pattern_re = re.search('(\d+) \| .* SEQ NUM (\d+)', line)

    if tmp_pattern_re:
        current_seq_num_timestamp = int(tmp_pattern_re.group(1))
        current_seq_num = int(tmp_pattern_re.group(2))
        if last_seq_num == -1:
            last_seq_num = current_seq_num
            last_seq_num_timestamp = current_seq_num_timestamp
        else:
            tmp_ranging_interval = (current_seq_num_timestamp - last_seq_num_timestamp) / (current_seq_num - last_seq_num)
            ranging_interval_list.append(tmp_ranging_interval)

def draw_and_save_histgram(log_file_name):
    global PER
    global RANGING_INTERVAL
    global rssi_list
    global snr_list
    global rx_fail_list

    print("func:%s, line:%d" %(sys._getframe().f_code.co_name, sys._getframe().f_lineno))

    data_array = [[],[]]

    raw_distance_list = []
    filtered_distance_list = []

    raw_azimuth_list = []
    filtered_azimuth_list = []

    seq_num_list = []

    timestamp_list = []

    rssi_list = []
    snr_list = []
    rx_fail_list = []

    full_log_file_name = log_file_name + LOG_FILE_EXTENSION

    with open (full_log_file_name, errors='ignore') as file_object:
        line = file_object.readline()
        raw_csv_filename = os.path.join(output_csv, "raw_"+ log_file_name + ".csv")
        filtered_csv_filename = os.path.join(output_csv, "filtered_" + log_file_name + ".csv")
        
        raw_csv_filename_ob = open(raw_csv_filename, 'w')
        filtered_csv_filename_ob = open(filtered_csv_filename, 'w')

        raw_csv_filename_ob.write("%s,%s\n" % ("raw distance", "azimuth"))
        filtered_csv_filename_ob.write("%s,%s\n" % ("filtered distance", "azimuth"))

        while line:
            extract_distance_and_azimuth(raw_csv_filename_ob, RAW_DISTANCE_RE_PATTERN, raw_distance_list, raw_azimuth_list, line)
            extract_distance_and_azimuth(filtered_csv_filename_ob, FILTERED_DISTANCE_RE_PATTERN, filtered_distance_list, filtered_azimuth_list, line)
            extract_sequence_num(seq_num_list, line)
            extract_timestamp(timestamp_list, line)
            extract_rx_fail(rx_fail_list, line)
            extract_rssi_snr(rssi_list, snr_list, line)

            # calculate_ranging_interval_through_timestamp(line)
            line = file_object.readline()

    PER = calculate_per(raw_distance_list, rx_fail_list)
    PER = "{:.2f}".format(PER)
    print("PER=%s%%" %(PER))

    print(np.isnan(raw_distance_list).any())
    print(np.isnan(raw_azimuth_list).any())

    hist_row = 0
    hist_column = 0

    if DISPLAY_MODE <= DISPLAY_MODE_FILTERED_AOA_ONLY:
        hist_row = 1
        hist_column = 1

    if DISPLAY_MODE == DISPLAY_MODE_DISTANCE_ONLY or DISPLAY_MODE == DISPLAY_MODE_AOA_ONLY:
        hist_row = 1
        hist_column = 2
        
    if DISPLAY_MODE == DISPLAY_MODE_DISTANCE_AND_AOA:
        hist_row = 2
        hist_column = 2
        
    data_array[0].append(raw_distance_list)
    data_array[0].append(filtered_distance_list)

    data_array[1].append(raw_azimuth_list)
    data_array[1].append(filtered_azimuth_list)

    fig, axs = plt.subplots(hist_row, hist_column, figsize=(15,15), sharex=False, sharey=False, squeeze=False)
    fig.suptitle(log_file_name, fontproperties=font, fontsize=50)

    print("hist_row:%d, hist_column:%d" %(hist_row, hist_column))

    if DISPLAY_MODE == DISPLAY_MODE_DISTANCE_AND_AOA:
        for i in range(hist_row):
            for j in range(hist_column):
                draw_histgram(axs[i][j], title_array[i][j], x_label_array[i], data_array[i][j])
    
    if DISPLAY_MODE == DISPLAY_MODE_DISTANCE_ONLY:
        for j in range(hist_column):
            draw_histgram(axs[0][j], title_array[0][j], x_label_array[0], data_array[0][j])
        
    if DISPLAY_MODE == DISPLAY_MODE_RAW_DISTANCE_ONLY:
        draw_histgram(axs[0][0], title_array[0][0], x_label_array[0], data_array[0][0])

    if DISPLAY_MODE == DISPLAY_MODE_FILTERED_DISTANCE_ONLY:
        draw_histgram(axs[0][0], title_array[0][1], x_label_array[0], data_array[0][1])

    if DISPLAY_MODE == DISPLAY_MODE_AOA_ONLY:
        for j in range(hist_column):
            draw_histgram(axs[0][j], title_array[1][j], x_label_array[1], data_array[1][j])

    if DISPLAY_MODE == DISPLAY_MODE_RAW_AOA_ONLY:
        draw_histgram(axs[0][0], title_array[1][0], x_label_array[1], data_array[1][0])

    if DISPLAY_MODE == DISPLAY_MODE_FILTERED_AOA_ONLY:
        draw_histgram(axs[0][0], title_array[1][1], x_label_array[1], data_array[1][1])

    log_file_name = log_file_name.replace(".","_")
    path = os.getcwd()
    png_name = os.path.join(path, output_png, log_file_name)
    print("png_name:", png_name)
    plt.savefig(png_name)
    # sys.exit()

def find_all_file(base):
    for root, dirs, files in os.walk(base):
        for f in files:
            #print(f)
            yield f

if __name__ == '__main__':
    #makedirs() is recursive directory creation function

    # # print(str(a))
    # sys.exit(0)

    os.makedirs(output_csv, exist_ok=True)
    os.makedirs(output_png, exist_ok=True)
    path = os.getcwd()
    print(path)
    #find_all_file(path)
    for i in find_all_file(path):
        if i.endswith(LOG_FILE_EXTENSION):
            print("---------------new file-----------------")
            print(i)
            log_file_name = os.path.splitext(i)[0]
            log_file_info_list = log_file_name.split('_')
            print(log_file_name)
            draw_and_save_histgram(log_file_name)