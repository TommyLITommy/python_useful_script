import matplotlib.pyplot as plt
from matplotlib.pyplot import MultipleLocator
import numpy as np
import os
import sys
import re

LOG_FILE_EXTENSION = ".log"
LOG_FILE_PREFIX = "Blvd_New_R"
OUTPU_FOLDER = "plot trace\\"

def parse_log_file(root, input_file):
    data_ori = []
    data_optimized = []
    rx_fail_list = []

    ## 全局变量设置
    title = os.path.splitext(input_file)[0]
    input_file = os.path.join(root, input_file)
    y_angle_min = -90
    y_angle_max = 90
    y_angle_multipleLocator = 10

    RAW_DISTANCE_PATTERN = "Raw Distance"
    FILTER_DISTANCE_PATTERN = "Peer .* Distance"
    RX_FAIL_PATTERN = "UWB RX fail"

    with open(input_file,'r') as fin:
        for line in fin:
            raw_distance_re = re.search(r'%s (\d+)cm' %RAW_DISTANCE_PATTERN, line)
            if raw_distance_re:
                data_ori.append(int(raw_distance_re.group(1)))
                
            filter_distance_re = re.search(r'%s (\d+)cm' %FILTER_DISTANCE_PATTERN, line)
            if filter_distance_re:
                data_optimized.append(int(filter_distance_re.group(1)))
                
            rx_fail_re = re.search(r'%s  0x(\d+)' %RX_FAIL_PATTERN, line)
            if rx_fail_re:
                rx_fail_list.append(int(rx_fail_re.group(1), 16))
    if len(data_ori) == 0:
        return

    if len(data_ori) < len(data_optimized):
        remove_count = len(data_optimized) - len(data_ori)
        data_optimized = data_optimized[0 : -remove_count]
    if len(data_ori) > len(data_optimized):
        remove_count = len(data_ori) - len(data_optimized)
        data_ori = data_ori[0 : -remove_count]
    min_val_ori = min(data_ori)
    max_val_ori = max(data_ori)
    delta_val_ori = max_val_ori - min_val_ori

    min_val_optimized = min(data_optimized)
    max_val_optimized = max(data_optimized)
    delta_val_optimized = max_val_optimized - min_val_optimized

    print ('min_val_ori = ', min_val_ori)
    print ('max_val_ori = ', max_val_ori)
    print ('delta_val_ori = ', delta_val_ori)

    print ('min_val_optimized = ', min_val_optimized)
    print ('max_val_optimized = ', max_val_optimized)
    print ('delta_val_optimized = ', delta_val_optimized)

    min_all = min(min_val_ori, min_val_optimized)
    max_all = max(max_val_ori, max_val_optimized)
    print ('min_all = ', min_all)
    print ('max_all = ', max_all)
    # plt.rcParams['font.sans-serif'] = ['SimHei']


    '''
    设置纵轴的范围和刻度，影响整体的美观度！！
    '''
    y_min = (min_all // 10) * 10 - 40    # //获整数部分
    y_max = (max_all // 10) * 10 + 20
    #y_min = 13900
    #y_max = 14100
    y_multipleLocator = 10
    plt.figure(figsize=(40,20))
    ax = plt.gca()
    ax.yaxis.set_major_locator(MultipleLocator(y_multipleLocator))  #设置纵坐标刻度
    ax.set_ylabel('Distance / cm', fontsize=20)
    ax.set_title(title, fontsize=30)
  
    x = [i+1 for i in range(len(data_ori))]
    plt.grid()
    plt.plot(x, data_ori, color='darkblue',label='origin')
    plt.plot(x, data_optimized, color='darkred',label='optimized')
    plt.legend(fontsize=20)
    plt.axis([0, len(data_ori), y_min, y_max]) #set the x and y axis ranging

    ## 数值处理
    std_ori = np.std(data_ori)
    std_ori = round(std_ori,2) #数值精度 保留4位
    std_optimized = np.std(data_optimized)
    std_optimized = round(std_optimized,2)
    print ('std_ori = ', std_ori)
    print ('std_optimized = ', std_optimized)

    ## 添加关键信息
    y_index_text = (min_all // 5 ) * 5 - y_multipleLocator
    x_ori = 1
    x_list = [x_ori, x_ori, x_ori, x_ori]
    y_list = [y_index_text,y_index_text - y_multipleLocator, y_index_text - y_multipleLocator*2,y_index_text - y_multipleLocator*3]

    text = []
    text.append('min of ori = ' + str(min_val_ori) + 'cm')   # + 字符串拼接
    text.append('max of ori = ' + str(max_val_ori) + 'cm')
    text.append('delta of ori = ' + str(delta_val_ori) + 'cm')
    text.append('std of ori = ' + str(std_ori) + 'cm')
    for idx in range(len(x_list)):    #range :
        plt.text(x_list[idx],y_list[idx],text[idx],color='darkblue',fontsize=20)

    #x_list = [len(data_ori) / 2,len(data_ori) / 2, len(data_ori) / 2, len(data_ori) / 2]
    x_opt = len(data_ori) / 5
    x_list = [x_opt, x_opt, x_opt, x_opt]
    y_list = [y_index_text,y_index_text - y_multipleLocator, y_index_text 
    - y_multipleLocator*2, y_index_text - y_multipleLocator*3]
    text = []
    text.append('min of optimized = ' + str(min_val_optimized) + 'cm')
    text.append('max of optimized = ' + str(max_val_optimized) + 'cm')
    text.append('delta of optimized = ' + str(delta_val_optimized) + 'cm')
    text.append('std of optimized = ' + str(std_optimized) + 'cm')
    idx = 0
    for idx in range(len(x_list)):
        plt.text(x_list[idx],y_list[idx],text[idx],color='darkred',fontsize=20)

    #lack_rate = fail_count / (max(data_package) - min(data_package) + 1)
    #lack_rate = round(lack_rate, 4)*100
    lack_rate = len(rx_fail_list) / (len(rx_fail_list) + len(data_ori))*100
    lack_rate = round(lack_rate, 2)

    x = x_opt * 2
    y = y_index_text
    text = 'ranging failed = ' + str(lack_rate) + '%'
    plt.text(x,y,text,color='green',fontsize=20)

    #creating folder
    output_dir = os.path.join(root, OUTPU_FOLDER)
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    plt.savefig(output_dir + title + '.png')
    # plt.show()

def find_all_file(base):
    for root, dirs, files in os.walk(base):
        for f in files:
            print(f)
            yield f

#list all files in current direction, could not include the subdirection.
def find_cur_dir_files(path):
    file_name = []
    for file in os.listdir(path):
        print(file)
        file_name.append(file)
    return file_name

# if __name__ == '__main__':
#     path = os.getcwd()
#     print(path)
#     for i in find_cur_dir_files(path):        
#         if i.endswith(LOG_FILE_EXTENSION):
#             print(i)
#             print("---------------new file-----------------")
#             parse_log_file(i)

def parse_file_and_draw_trace(root, files):
    for file in files:
        if file.endswith(LOG_FILE_EXTENSION) and file.startswith(LOG_FILE_PREFIX):
            parse_log_file(root, file)
            
    pass

if __name__ == '__main__':
    for root, dirs, files in os.walk(".", topdown=False):
        parse_file_and_draw_trace(root, files)