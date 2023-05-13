#******************************************************************************
# Copyright (c) 2021 Mauna Kea Semiconductor Holdings.
# All Rights Reserved.
#******************************************************************************

import sys
import os, fnmatch
import shutil
import logging
import subprocess
import re
import glob
import getopt
import stat
import time
from collections import defaultdict
from shutil import rmtree
from os.path import splitext
import linecache




#*************** initiator sample**************************
# [APP][INFO]DS-TWR Initiator SEQ NUM 18035
# [APP][INFO][TX][5] Poll 871037402
# [APP][INFO][RX][5] Response 872285504 124 1 1 0 -570336409 170676052 0 0 0
# [APP][INFO]CH Freq off 7396
# x, x
# [APP][INFO][TX][15] Final 873533402

#*************** responder sample **************************
# [APP][INFO]DS-TWR Responder SEQ NUM 18035
# [APP][INFO][RX][5] Poll 3432809881 124 0 1 0 -4500648 -173712409 0 0 0
# x, x
# [APP][INFO][TX][5] Response 3434057881
# [APP][INFO][RX][15] Final 3435305878 124 3 1 0 -173712409 38506164 0 0 0
# [APP][INFO]Raw Distance 462cm
# [APP][INFO]Peer AAA1, Distance 469cm
# x, x

def removeprefix(string, prefix):
    if not (isinstance(string, str) and isinstance(prefix, str)):
        raise TypeError('Param value type error')
    if string.startswith(prefix):
        return string[len(prefix):]
    return string

def removesuffix(string, suffix):
    if not (isinstance(string, str) and isinstance(suffix, str)):
        raise TypeError('Param value type error')
    if string.endswith(suffix):
        return string[:-len(suffix)]
    return string


def process_files(initiator_file_name, responder_file_name):
    total = 0;
    
    # open input files
    initiator_file = open(initiator_file_name, 'r', errors='ignore')
    responder_file = open(responder_file_name, 'r', errors='ignore')    
    
    #prepare output file name
    file_name,extension = splitext(initiator_file_name)
    initiator_output_filename = file_name + "_o.txt"
    
    file_name,extension = splitext(responder_file_name)
    responder_output_filename = file_name + "_o.txt"
    output_filename = file_name + "_both.txt"
    
    initiator_output_file = open(initiator_output_filename, 'w')
    responder_output_file = open(responder_output_filename, 'w')
    output_file = open(output_filename, 'w')


    responder_lines = responder_file.readlines()
    initiator_lines = initiator_file.readlines()
    
    initiator_line_count = len(initiator_lines)
    initiator_line_start = 0
    
    ##################################################
    # responder part
    ##################################################

    responder_cursor = 0
    responder_seq = 0
    
    for responder_line in responder_lines:
        
        if re.search('DS-TWR Responder SEQ NUM',responder_line):
            responder_cursor = 1
            responder_seq_re = re.search('\w*NUM ([0-9]*).*',responder_line)
            if not responder_seq_re:
                print("ERROR: seq was missed at responder file")
            responder_seq = int(str(responder_seq_re.group(1)))
            # print(responder_seq)
        elif re.search('Poll',responder_line):
            if responder_cursor == 1:
                responder_cursor = 2
                responder_rx_poll = re.search('\w*Poll ([0-9]*).*',responder_line)
        elif re.search('Response',responder_line):
            if responder_cursor == 2:
                responder_cursor = 3
                responder_tx_response = re.search('\w*Response ([0-9]*).*',responder_line)
        elif re.search('Final',responder_line):
            if responder_cursor == 3:
                responder_cursor = 4
                responder_rx_final = re.search('\w*Final ([0-9]*).*',responder_line)
        elif re.search('Raw Distance',responder_line):
            if responder_cursor == 4:
                responder_distance_re = re.search('\w*Raw Distance ([0-9\.\-]*)cm.*', responder_line)
                # print(responder_line)
                responder_cursor = 5
        else:
            pass
            # print("ERROR: Unknown line at responder file")
            # print(responder_line)


        if responder_cursor == 5:
            responder_cursor = 0
            initiator_cursor = 0
            initiator_seq = 0
            
            ##################################################
            # initiator part
            ##################################################        
            for i in range(initiator_line_start,initiator_line_count):
                initiator_line = initiator_lines[i]

                if re.search('DS-TWR Initiator SEQ NUM',initiator_line):
                    initiator_cursor = 1
                    initiator_seq_re = re.search('\w*SEQ NUM ([0-9]*).*',initiator_line)
                    if not initiator_seq_re:
                        print("ERROR: seq was missed at initiator file")
                    initiator_seq = int(str(initiator_seq_re.group(1)))
                    # print(initiator_seq)
                elif re.search('Poll',initiator_line):
                    if initiator_cursor == 1:
                        initiator_cursor = 2
                        initiator_tx_poll = re.search('\w*Poll ([0-9]*).*',initiator_line)
                elif re.search('Response',initiator_line):
                    if initiator_cursor == 2:
                        initiator_cursor = 3
                        initiator_rx_response = re.search('\w*Response ([0-9]*).*',initiator_line)                       
                elif re.search('Final',initiator_line):
                    if initiator_cursor == 3:
                        initiator_cursor = 4
                        initiator_tx_final = re.search('\w*Final ([0-9]*).*',initiator_line)
                else:
                    pass
                    # print("ERROR: Unknown line at initiator file")
                    # print(initiator_line)


                if initiator_cursor == 4 and initiator_seq == responder_seq:
                    initiator_cursor = 0
                    initiator_line_start = i

                    print("seq:", initiator_seq);
                    
                    response_string = initiator_rx_response.group(0).replace('Response ', '')

                    initiator_res = initiator_tx_poll.group(1) + '\t' + response_string.replace(' ', '\t') + '\t'  + initiator_tx_final.group(1)
                    initiator_output_file.write(initiator_res + '\n')
                
                    poll_string = responder_rx_poll.group(0).replace('Poll ', '')
                    final_string = responder_rx_final.group(0).replace('Final ', '')
                
                    responder_res = poll_string.replace(' ', '\t') + '\t' + responder_tx_response.group(1) + '\t' + final_string.replace(' ', '\t')
                    responder_output_file.write(responder_res + '\n')
                    
                    output_line = str(initiator_seq) + '\t' + initiator_res + '\t' + responder_res + '\t' + responder_distance_re.group(1) + '\n'
                    output_file.write(output_line)

                    total = total + 1
                    break
                elif initiator_seq > responder_seq:
                    break
                

    print("Total", total, " records are saved")
#
# Parse and validate the command line
#
def process_command_line():
    global initiator_file_name, responder_file_name
   
    if len(sys.argv) < 3:
        print("Usage: ", str(sys.argv[0]), "[initiator_input] [responder_input]")
        sys.exit(1)
    else:
        initiator_file_name = str(sys.argv[1])
        responder_file_name = str(sys.argv[2])

        if not os.path.isfile(initiator_file_name) :
            print("ERROR: ", initiator_file_name, " does NOT exist")
            sys.exit(1)

        if not os.path.isfile(responder_file_name) :
            print("ERROR: ", responder_file_name, " does NOT exist");
            sys.exit(1)
            
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("initiator_file: %s", initiator_file_name)
            logging.debug("responder_file: %s", responder_file_name)

    src_file = str(sys.argv[1])
    output_file = str(sys.argv[2])
    
    

# main
if os.getenv("DEBUG") or os.getenv("VERBOSE"):
   logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
else:
   logging.basicConfig(stream=sys.stderr, level=logging.INFO)
   
logging.debug("Argument List: %s", str(sys.argv))

process_command_line()
process_files(initiator_file_name, responder_file_name)
