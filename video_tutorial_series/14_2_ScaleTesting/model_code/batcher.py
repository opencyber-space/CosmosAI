import time
import copy

class Batcher:
    def __init__(self, N: int, timeout_seconds: float = 5.0):
        self.N = N
        self.timeout_seconds = timeout_seconds
        self.batch = []
        self.first_added_time = None

    def add_to_batch(self, packet):
        if not self.batch:
            self.first_added_time = time.time()

        self.batch.append(packet)

        if len(self.batch) >= self.N:
            batch_copy = copy.deepcopy(self.batch)
            self.batch = []
            self.first_added_time = None
            return batch_copy, False, False
        elif (time.time() - self.first_added_time) >= self.timeout_seconds:
            batch_copy = copy.deepcopy(self.batch)
            orig_size = len(batch_copy)
            
            # Pad the batch with copies of the last item until it reaches size N
            while len(batch_copy) < self.N:
                batch_copy.append(copy.deepcopy(batch_copy[-1]))
                
            self.batch = []
            self.first_added_time = None
            return batch_copy, True, orig_size

        return None, False, False