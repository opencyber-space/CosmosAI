class Batcher:
    def __init__(self, N: int):
        self.N = N
        self.batch = []

    def add_to_batch(self, packet):
        self.batch.append(packet)

        if len(self.batch) >= self.N:
            batch_copy = self.batch
            self.batch = []
            return batch_copy

        return None