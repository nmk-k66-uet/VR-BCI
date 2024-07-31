from pylsl import resolve_stream, StreamInlet
#Container for LSL EEG stream and StreamInlet
class DataStream:
    def __init__(self):
        self.eeg_stream = None
        self.inlet = None
        
    def start_stream(self): #TODO: make function independent of the main thread
        print("Looking for a stream...")
        self.eeg_stream = resolve_stream('type', 'eeg')
        self.inlet = StreamInlet(self.eeg_)
    
    def end_stream(self):
        self.eeg_stream = None
        self.inlet = None
    