"""Example program to show how to read a multi-channel time series from LSL."""
import time
from pylsl import StreamInlet, resolve_stream

print("looking for a stream...")
# first resolve a EEG stream on the lab network
streams1 = resolve_stream('type', 'EEG') # You can try other stream types such as: EEG, EEG-Quality, Contact-Quality, Performance-Metrics, Band-Power
print(streams1)
streams2 = resolve_stream('type', 'Motion')
print(streams2)

# ch_lst = [['CMS', 'TP9'],
#           ['DRL', 'TP10'],
#           ['LL', 'FCz'],
#           ['LM', 'C3'],
#           ['LO', 'C1'],
#           ['LP', 'C5'],
#           ['RL', 'Cz'],
#           ['RM', 'C4'],
#           ['RN', 'CPz'],
#           ['RO', 'C2'],
#           ['RP', 'C6']]

# create a new inlet to read from the stream
inlet1 = StreamInlet(streams1[0])
inlet2 = StreamInlet(streams2[0])

f = open("log.txt", "x")

index = 0
counter = 0
check = False

while True:
    # Returns a tuple (sample,timestamp) where sample is a list of channel values and timestamp is the capture time of the sample on the remote machine,
    # or (None,None) if no new sample was available
    sample1, timestamp1 = inlet1.pull_sample()
    sample2, timestamp2 = inlet2.pull_sample()
    if index == 0 and check == False:
        f.write("Index of chunk: " + str(index) + '\n')
        check = True
    if timestamp1 != None and timestamp2 != None:
        f.write("EEG Data" + '\n')
        f.write(str(sample1) + '\n')
        f.write("Motion Data" + '\n')
        f.write(str(sample2) + '\n')
        counter += 1
    if counter == 256:
        index += 1
        f.write("Index of chunk: " + str(index) + '\n')
    if index == 3:
        break