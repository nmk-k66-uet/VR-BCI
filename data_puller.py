from data_stream import DataStream
import threading
#Class for delegate data pulling to a separate thread
class DataPuller:
    def __init__(self):
        self.data_stream = DataStream()
        self.eeg_thread = None
    
    