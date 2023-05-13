import re
VP_VAL = 100

PACKET_TYPE_POLL = 0x00
PACKET_TYPE_RESPONSE = 0x01
PACKET_TYPE_FINAL = 0x02

DEV_ROLE_RESPONDER = 0
DEV_ROLE_INITIATOR = 1

DEV_ROLE_STRING = ["RESPONDER", "INITIATOR"]
PACKET_TYPE_STRING = ["POLL", "RESPONSE", "FINAL"]

'''
initiator_log_list = [
    "93617820 | [APP][INFO]DS-TWR Initiator SEQ NUM 952",
    "93618240 | [APP][INFO][TX][9] Poll 3291651496",
    "93627990 | [APP][INFO][RX][7] Response 3292899597 124 1 0 0 -31 307519484 0 25 25",
    "93655920 | [APP][INFO][TX][16] Final 3294147496",

    "93716160 | [APP][INFO]DS-TWR Initiator SEQ NUM 953",
    "93716580 | [APP][INFO][TX][9] Poll 3304131496",
    "93726330 | [APP][INFO][RX][7] Response 3305379597 124 0 0 0 124 677332338 0 25 25",
    "93754410 | [APP][INFO][TX][16] Final 3306627496"
]

responder_log_list = [
    "176620590 | [APP][INFO]DS-TWR Responder SEQ NUM 952",
    "176621040 | [APP][INFO][RX][9] Poll 1583983118 124 1 1 0 -31 -917781907 0 25 23",
    "176650590 | [APP][INFO][TX][7] Response 1585231118",
    "176651280 | [APP][INFO][RX][16] Final 1586479113 124 0 0 0 -41 477033944 0 25 25",

    "176718900 | [APP][INFO]DS-TWR Responder SEQ NUM 953",
    "176719350 | [APP][INFO][RX][9] Poll 1596463093 124 1 0 0 -39 457771828 0 25 25",
    "176748390 | [APP][INFO][TX][7] Response 1597711093",
    "176749080 | [APP][INFO][RX][16] Final 1598959088 124 3 1 0 -128 -392326566 0 25 24",
    "176750640 | [APP][INFO]Raw Distance 199cm"
]
'''

initiator_log_list = [
    "656177190 | [APP][INFO]DS-TWR Initiator SEQ NUM 6674",
    "656177670 | [APP][INFO][TX][9] Poll 1687960656",
    "656202060 | [APP][INFO][RX][7] Response 1691080784 124 0 1 0 0 98249514 0 25 25",
    "656228340 | [APP][INFO][TX][16] Final 1694200656",
    
    "656275500 | [APP][INFO]DS-TWR Initiator SEQ NUM 6675",
    "656275980 | [APP][INFO][TX][9] Poll 1700440656",
    "656300370 | [APP][INFO][RX][7] Response 1703560793 124 2 1 0 0 -759492268 0 25 25",
    "656326680 | [APP][INFO][TX][16] Final 1706680656",
]

responder_log_list = [
    "539317530 | [APP][INFO]DS-TWR Responder SEQ NUM 6674",
    "539318010 | [APP][INFO][RX][9] Poll 4038026028 124 2 0 0 0 -131659786 0 25 25",
    "539345970 | [APP][INFO][TX][7] Response 4041146028",
    "539366640 | [APP][INFO][RX][16] Final 4044266033 124 3 1 0 0 -454923486 0 25 25",
    
    "539415840 | [APP][INFO]DS-TWR Responder SEQ NUM 6675",
    "539416320 | [APP][INFO][RX][9] Poll 4050506048 124 0 0 0 0 682916532 0 25 25",
    "539443170 | [APP][INFO][TX][7] Response 4053626048",
    "539464950 | [APP][INFO][RX][16] Final 4056746044 124 0 0 0 0 -175094194 0 25 25",
]

class UWBTimestampItem():
    def __init__(self):
        self.seq_num = 0
        self.role = 0

        self.timestamp_per_15p56ps = 0
        self.packet_type = 0

        self.phy_timer_count = 0
        self.tadv = 0
        self.pid = 0
        self.ds2phase = 0
        self.ds1phase = 0
        self.delta = 0
        self.frac_drift = 0
        self.int_drift = 0
        self.main_path_loc = 0
        self.fap_loc = 0

    def to_string(self):
        print("\nrole:", DEV_ROLE_STRING[self.role])
        print("packet_type:", PACKET_TYPE_STRING[self.packet_type])
        print("seq_num:", self.seq_num)
        print("phy_timer_count:", self.phy_timer_count)
        print("tadv:", self.tadv)
        print("pid:", self.pid)
        print("ds2phase:", self.ds2phase)
        print("ds1phase:", self.ds1phase)
        print("delta:", self.delta)
        print("frac_drift:", self.frac_drift)
        print("int_drif:", self.int_drift)
        print("main_path_loc:", self.main_path_loc)
        print("fap_loc:", self.fap_loc)
        print("\n")

class UWBCustomRanging():
    def __init__(self):
        self.uwb_timestamp_item_list = [[{}, {}, {}], [{}, {}, {}]] #Responder[Poll Response Final] Initiator[Poll Responder Final]
        self.uwb_timestamp_item = UWBTimestampItem()
        self.cur_seq_num = 0
        self.rx_pattern = "(-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+)"
        self.packet_type_dic = {"Poll":PACKET_TYPE_POLL,"Response":PACKET_TYPE_RESPONSE,"Final":PACKET_TYPE_FINAL}

    def get_timestamp_item(self, role, packet_type, seq_num):
        if seq_num in self.uwb_timestamp_item_list[role][packet_type]:
            return self.uwb_timestamp_item_list[role][packet_type][seq_num]
        else:
            return None

    def get_distance(self, seq_num):
        initiator_poll_tx_item = self.get_timestamp_item(DEV_ROLE_INITIATOR, PACKET_TYPE_POLL, seq_num)
        initiator_poll_tx_item.to_string()

        responder_poll_rx_item = self.get_timestamp_item(DEV_ROLE_RESPONDER, PACKET_TYPE_POLL, seq_num)
        responder_poll_rx_item.to_string()
        
        responder_response_tx_item = self.get_timestamp_item(DEV_ROLE_RESPONDER, PACKET_TYPE_RESPONSE, seq_num)
        responder_response_tx_item.to_string()

        initiator_responde_rx_item = self.get_timestamp_item(DEV_ROLE_INITIATOR, PACKET_TYPE_RESPONSE, seq_num)
        initiator_responde_rx_item.to_string()

        initiator_final_tx_item = self.get_timestamp_item(DEV_ROLE_INITIATOR, PACKET_TYPE_FINAL, seq_num)
        initiator_final_tx_item.to_string()

        responder_final_rx_item = self.get_timestamp_item(DEV_ROLE_RESPONDER, PACKET_TYPE_FINAL, seq_num)
        responder_final_rx_item.to_string()

        initiator_poll_tx_timestamp = self.ranging_tx_timestamp(initiator_poll_tx_item.phy_timer_count)
        responder_poll_rx_timestamp = self.ranging_rx_timetamp(responder_poll_rx_item)

        responder_response_tx_timestamp = self.ranging_tx_timestamp(responder_response_tx_item.phy_timer_count)
        initiator_response_rx_timestamp = self.ranging_rx_timetamp(initiator_responde_rx_item)

        initiator_final_tx_timestamp = self.ranging_tx_timestamp(initiator_final_tx_item.phy_timer_count)
        responder_final_rx_timestamp = self.ranging_rx_timetamp(responder_final_rx_item)

        print("initiator_poll_tx_timestamp:", initiator_final_tx_timestamp)
        print("initiator_response_rx_timestmap:", initiator_response_rx_timestamp)
        print("initiator_final_tx_timestamp:", initiator_final_tx_timestamp)

        print("responder_poll_rx_timestamp:", responder_poll_rx_timestamp)
        print("responder_response_tx_timestamp:", responder_response_tx_timestamp)
        print("responder_final_rx_timestamp:", initiator_response_rx_timestamp)
        
        tround1 = self.ranging_tround(initiator_poll_tx_timestamp, initiator_response_rx_timestamp)
        treply1 = self.ranging_treply(responder_poll_rx_timestamp, responder_response_tx_timestamp)
        
        treply2 = self.ranging_treply(initiator_response_rx_timestamp, initiator_final_tx_timestamp)
        tround2 = self.ranging_tround(responder_response_tx_timestamp, responder_final_rx_timestamp)

        print("tround1:%d, treplay1:%d, tround2:%d, treply2:%d" %(tround1, treply1, tround2, treply2))

        distance = self.calculate_distance(tround1, treply1, tround2, treply2)
        print("distance:", distance)

    def parse_tx_timestamp(self, line):
        uwb_timestamp_item = None

        regex = re.search("\[TX\]\[\d+\] ([a-zA-Z]+) (\d+)", line)
        if regex:
            uwb_timestamp_item = UWBTimestampItem()

            index = 1
            uwb_timestamp_item.packet_type = self.packet_type_dic[regex.group(index)]

            index += 1
            uwb_timestamp_item.phy_timer_count = int(regex.group(index))
        
        return uwb_timestamp_item
    
    def parse_rx_timestamp(self, line):
        uwb_timestamp_item = None

        regex = re.search("\[RX\]\[\d+\] ([a-zA-Z]+) %s" %self.rx_pattern, line)
        if regex:
            uwb_timestamp_item = UWBTimestampItem()
            index = 1
            uwb_timestamp_item.packet_type = self.packet_type_dic[regex.group(index)]

            index += 1
            uwb_timestamp_item.phy_timer_count = int(regex.group(index))

            index += 1
            uwb_timestamp_item.tadv = int(regex.group(index))

            index += 1
            uwb_timestamp_item.pid = int(regex.group(index))

            index += 1
            uwb_timestamp_item.ds2phase = int(regex.group(index))

            index += 1
            uwb_timestamp_item.ds1phase = int(regex.group(index))

            index += 1
            uwb_timestamp_item.delta = int(regex.group(index))

            index += 1
            uwb_timestamp_item.frac_drift = int(regex.group(index))

            index += 1
            uwb_timestamp_item.int_drift = int(regex.group(index))

            index += 1
            uwb_timestamp_item.main_path_loc = int(regex.group(index))

            index += 1
            uwb_timestamp_item.fap_loc = int(regex.group(index))

        return uwb_timestamp_item

    def parse_log(self, role, line):
        seq_num_re = re.search("SEQ NUM (\d+)", line)
        if seq_num_re:
            self.cur_seq_num = int(seq_num_re.group(1))

        uwb_timestamp_item = self.parse_tx_timestamp(line)
        if uwb_timestamp_item:
            uwb_timestamp_item.role = role
            uwb_timestamp_item.seq_num = self.cur_seq_num
            self.uwb_timestamp_item_list[role][uwb_timestamp_item.packet_type][self.cur_seq_num] = uwb_timestamp_item

        uwb_timestamp_item = self.parse_rx_timestamp(line)
        if uwb_timestamp_item:
            uwb_timestamp_item.role = role
            uwb_timestamp_item.seq_num = self.cur_seq_num
            self.uwb_timestamp_item_list[role][uwb_timestamp_item.packet_type][self.cur_seq_num] = uwb_timestamp_item

    def ranging_rx_timetamp(self, timestamp_item):
        tap_diff = 0
        rx_timestamp = timestamp_item.phy_timer_count

        if timestamp_item.fap_loc == timestamp_item.main_path_loc:
            tap_diff = 0
        else:
            tap_diff = 25 - timestamp_item.fap_loc

        #Timestmap counter at 124.8MHz

        #Corrected counter difference at 499.2MHz
        rx_timestamp = (rx_timestamp - 78) * 4 + timestamp_item.tadv

        #Correct with PID
        rx_timestamp = rx_timestamp - (4 - timestamp_item.pid)

        #Correct with ds2phase at 998.4MHz
        rx_timestamp = rx_timestamp * 2 + (1 - timestamp_item.ds2phase)

        rx_timestamp = rx_timestamp - 2

        rx_timestamp = rx_timestamp * 64

        if tap_diff == 0:
            rx_timestamp = rx_timestamp - timestamp_item.int_drift * 128 - (timestamp_item.frac_drift / 0x800000)
        else:
            rx_timestamp = rx_timestamp - timestamp_item.int_drift * 128

        if tap_diff:
            rx_timestamp = rx_timestamp - timestamp_item.delta / 2 - tap_diff * 128

        return rx_timestamp

    # uinit 15.56ps
    def ranging_tx_timestamp(self, tx_phy_timer_count):
        print("tx_phy_timer_count:", tx_phy_timer_count)
        tx_timetamp = ((tx_phy_timer_count - 1) * 4 + 3) * 2
        tx_timetamp = tx_timetamp + 5
        tx_timetamp = tx_timetamp * 64
        return tx_timetamp

    def ranging_tround(self, tx_timestamp, rx_timestamp):
        tround = 0
        if rx_timestamp < tx_timestamp:
            tround = 0x20000000000 - tx_timestamp + rx_timestamp
        else:
            tround = rx_timestamp - tx_timestamp
        return tround

    def ranging_treply(self, rx_timestamp, tx_timestamp):
        treply = 0
        if tx_timestamp < rx_timestamp:
            treply = 0x20000000000 - rx_timestamp + tx_timestamp
        else:
            treply = tx_timestamp - rx_timestamp
        return treply
        
    def calculate_distance(self, tround1, treply1, tround2, treply2):
        distance = 0
        tof_i = (tround1 * tround2 - treply1 * treply2) / (tround1 + tround2 + treply1 + treply2)
        if tof_i < 0:
            print("ilegal tof")
        
        tof_f = tof_i * 1000 
        tof_f = tof_f / 499.2
        tof_f = tof_f / 128
        print("tof_i:", tof_i)
        print("tof_f:", tof_f)
        distance = tof_f * 0.299792458 * VP_VAL
        return distance

#Tag    Tround1--Treply2
#Anchor Treply1--Tround2
if __name__ == '__main__':
    # initiator_poll_packet_tx_timestamp = 3304131496#3291651496
    # responder_poll_packet_rx_timestamp = 1596463093#1583983118
    
    # responder_response_packet_tx_timestamp = 1597711093#1585231118
    # initiator_response_packet_rx_timestamp = 3305379597#3292899597
    
    # initiator_final_packet_tx_timestamp = 3306627496#3294147496
    # responder_final_packet_rx_timestamp = 1598959088#1586479113

    # tround1 = ranging_tround(initiator_poll_packet_tx_timestamp, initiator_response_packet_rx_timestamp)
    # treply1 = ranging_treply(responder_poll_packet_rx_timestamp, responder_response_packet_tx_timestamp)
    
    # treply2 = ranging_treply(initiator_response_packet_rx_timestamp, initiator_final_packet_tx_timestamp)
    # tround2 = ranging_tround(responder_response_packet_tx_timestamp, responder_final_packet_rx_timestamp)

    # print("tround1:%d, treplay1:%d, tround2:%d, treply2:%d" %(tround1, treply1, tround2, treply2))

    # distance = calculate_distance(tround1, treply1, tround2, treply2)
    # print("distance:", distance)

    uwb_custom_ranging = UWBCustomRanging()

    for line in initiator_log_list:
        uwb_custom_ranging.parse_log(DEV_ROLE_INITIATOR, line)

    for line in responder_log_list:
        uwb_custom_ranging.parse_log(DEV_ROLE_RESPONDER, line)

    for item_01 in uwb_custom_ranging.uwb_timestamp_item_list:
        for item_02 in item_01:
            pass
            # print("len(item_2):", len(item_02))
            # for value in item_02.values():
            #     value.to_string()

    uwb_custom_ranging.get_distance(6674)
    uwb_custom_ranging.get_distance(6675)