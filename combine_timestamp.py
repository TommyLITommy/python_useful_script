import os
import shutil
import re

LOG_FILE_EXTENSION = ".log"

#INITIATOR_PATTERN = "Initiator"
#RESPONDER_PATTERN = "Responder"

INITIATOR_PATTERN = "GB_New_I"
RESPONDER_PATTERN = "GB_New_R"
COMBINE_PATTERN = "combined"

def parse_log(packet_dict, role, file):
    cur_seq_num = -1
    with open(file, errors='ignore') as file_obj:
        line = file_obj.readline()
        while line:
            seq_num_re = re.search("SEQ NUM (\d+)", line)
            if seq_num_re:
                cur_seq_num = int(seq_num_re.group(1))
                if not cur_seq_num in packet_dict:
                    packet_dict[cur_seq_num] = {}

            if cur_seq_num in packet_dict:
                
                poll_re = re.search("Poll (.*)", line)
                if poll_re:
                    packet_dict[cur_seq_num][role + "_poll"] = poll_re.group(1)

                response_re = re.search("Response (.*)", line)
                if response_re:
                    packet_dict[cur_seq_num][role + "_response"] = response_re.group(1)
                
                final_re = re.search("Final (.*)", line)
                if final_re:
                    packet_dict[cur_seq_num][role + "_final"] = final_re.group(1)

            line = file_obj.readline() 

if __name__ == '__main__':

    for root, dirs, files in os.walk(".", topdown=False):
        print("\n\n")
        print("folder:{}, files:{}".format(root, files))

        responder_file_list = []
        initiator_file_list = []
        angle_list = []
        
        file_list = files

        for file in file_list:
            print(file)
            if not file.endswith(LOG_FILE_EXTENSION):
                continue
                
            if re.search(RESPONDER_PATTERN, file):
                responder_file_list.append(file)
            
            if re.search(INITIATOR_PATTERN, file):
                initiator_file_list.append(file)
                
        if len(responder_file_list) == 0:
            continue

        responder_file_list.sort(key= lambda file:int(file.split('_')[-1].replace('.log', '')))
        initiator_file_list.sort(key= lambda file:int(file.split('_')[-1].replace('.log', '')))
        print(responder_file_list)
        print(initiator_file_list)

        print("len(responder_file_list):%d" %(len(responder_file_list)))
        print("len(initiator_file_list):%d" %(len(initiator_file_list)))
        assert(len(responder_file_list) == len(initiator_file_list))

        for file in responder_file_list:
            angle_list.append(file.split('_')[-1].replace('.log', ''))

        print(angle_list)
                
        for index, angle in enumerate(angle_list):
            packet_dict = {}
            
            # angle_dir = os.path.join(root, angle)
            # os.makedirs(angle_dir, exist_ok=True)
            
            initiator_path = os.path.join(root, initiator_file_list[index])
            responder_path = os.path.join(root, responder_file_list[index])
            
            parse_log(packet_dict, "initiator", initiator_path)
            parse_log(packet_dict, "responder", responder_path)
                      
            combined_timestamp_file = os.path.join(root, "combined_" + angle + ".log") 
   
            with open(combined_timestamp_file, 'w') as file_obj:
                for seq_num, value in packet_dict.items():
                    # print(packet, value)
                    if "initiator_poll" in value and "initiator_response" in value and "initiator_final" in value and "responder_poll" in value and "responder_response" in value and "responder_final" in value:
                        timestamp_str = "%d %s %s %s %s %s %s\n" %(seq_num, value["initiator_poll"], value["responder_poll"], value["responder_response"], value["initiator_response"], value["initiator_final"], value["responder_final"])
                        print("%s" %timestamp_str)
                        file_obj.write(timestamp_str)


    for root, dirs, files in os.walk(".", topdown=False):
        responder_file_list = []
        initiator_file_list = []
        combined_list = []
        angle_list = []

        file_list = files

        for file in file_list:
            print(file)
            if not file.endswith(LOG_FILE_EXTENSION):
                continue
                
            if re.search(RESPONDER_PATTERN, file):
                responder_file_list.append(file)

            if re.search(INITIATOR_PATTERN, file):
                initiator_file_list.append(file)

            if re.search(COMBINE_PATTERN, file):
                combined_list.append(file)
                
        if len(responder_file_list) == 0:
            continue

        responder_file_list.sort(key= lambda file:int(file.split('_')[-1].replace('.log', '')))
        initiator_file_list.sort(key= lambda file:int(file.split('_')[-1].replace('.log', '')))
        combined_list.sort(key= lambda file:int(file.split('_')[-1].replace('.log', '')))

        print(responder_file_list)
        print(initiator_file_list)
        print(combined_list)

        print("len(responder_file_list):%d" %(len(responder_file_list)))
        print("len(initiator_file_list):%d" %(len(initiator_file_list)))
        assert(len(responder_file_list) == len(initiator_file_list))

        for file in responder_file_list:
            angle_list.append(file.split('_')[-1].replace('.log', ''))

        print(angle_list)
                
        for index, angle in enumerate(angle_list):
            packet_dict = {}
            
            angle_dir = os.path.join(root, angle)
            os.makedirs(angle_dir, exist_ok=True)
            
            initiator_path = os.path.join(root, initiator_file_list[index])
            responder_path = os.path.join(root, responder_file_list[index])
            combined_path = os.path.join(root, combined_list[index])

            parse_log(packet_dict, "initiator", initiator_path)
            parse_log(packet_dict, "responder", responder_path)
                      
            shutil.move(initiator_path, angle_dir)
            shutil.move(responder_path, angle_dir)
            shutil.move(combined_path, angle_dir)

            
'''
sequence {
i_poll_tx
r_poll_rx
r_response_tx
i_response_rx
i_final_tx
r_final_rx
}
'''