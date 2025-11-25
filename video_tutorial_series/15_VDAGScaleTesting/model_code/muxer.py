from collections import defaultdict
import copy
import json

class Muxer:
    def __init__(self, N: int):
        self.N = N
        self.store = defaultdict(list)
        self.counts = defaultdict(int)

    def process_packet(self, packet):
        print(f"Muxer received packet: session_id={packet.session_id}, seq_no={packet.seq_no}")
        if self.N == 1:
            return packet  # No merging needed

        key = (packet.session_id, packet.seq_no)
        self.store[key].append(packet)
        self.counts[key] += 1

        if self.counts[key] == self.N:
            merged_packet = self._merge_packets(self.store[key])
            del self.store[key]
            del self.counts[key]
            #print(f"Muxer merging packets for session_id={packet.session_id}, seq_no={packet.seq_no}")
            print(f"Muxer merged packet 1: {merged_packet}")
            return merged_packet
        print(f"Muxer merged packet 2: None")
        return None

    def _merge_packets(self, packets):
        merged_data = {"inputs": [json.loads(p.data) for p in packets]}
        #merged_files = [file for p in packets for file in p.files]

        base_packet = copy.deepcopy(packets[0])
        base_packet.data = json.dumps(merged_data)
        #base_packet.files = merged_files

        return base_packet