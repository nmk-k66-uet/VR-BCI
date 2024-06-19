import collections
import socket
from pylsl import StreamInlet, resolve_stream
from sklearn.preprocessing import StandardScaler
import modelUtils
import numpy as np
import tensorflow as tf
import keyboard
import time

# Set dataset paramters 
dataset_conf = { 'name': 'BCI2a', 'n_classes': 4, 'cl_labels': ['Left hand', 'Right hand', 'Foot', 'Tongue'],
                    'n_sub': 9, 'n_channels': 22, 'in_samples': 512,
                    'data_path': './datasets/BCI2a/raw/', 'isStandard': False, 'LOSO': True}
# Load model weight
model = modelUtils.getModel('ATCNet', dataset_conf)
model.load_weights('./best_model/subject-8.weights.h5')

print("looking for a stream...")
# first resolve a EEG stream on the lab network
streams = resolve_stream('type', 'EEG') # Currently EMOTIV EPOC Flex supports: EEG, Motion
print(streams)
# create a new inlet to read from the stream
inlet = StreamInlet(streams[0])

data = []
t1 = 0
t2 = 512
counter = 0
sample_count = 0
queue = False
label_count = 0
group = []
started = False

# def standardize_data(data, channels): 
#     # X_train & X_test :[Trials, MI-tasks, Channels, Time points]
#     for j in range(channels):
#           scaler = StandardScaler()
#           scaler.fit(data[:, 0, j, :])
#           data[:, 0, j, :] = scaler.transform(data[:, 0, j, :])
#     return data

def data_converter(data):
    data_return = np.zeros((1, 22, 512))
    data_return[0, :, :] = np.transpose(np.array(data))
    data_return = data_return[0:1, :, t1:t2]
    N_tr, N_ch, T = data_return.shape
    data_return = data_return.reshape(N_tr, 1, N_ch, T)
    return data_return

def labelManipulate(label):
    res = 0
    temp = 0
    if label[0][0] >= 0.3 and label[0][1] >= 0.3:
        temp = max(label[0][0], label[0][1])
        if temp == label[0][0]:
            res = "0"
        else:
            res = "1"
    else:
        res = str(label.argmax(axis = -1)[0])
    return res

def mostFrequentLabels(group):
    counter = collections.Counter(group)
    res = counter.most_common(1)
    return res[0][0]

# Establish TCP connection
HOST = "192.168.137.1"
PORT = 8000

# log_write = open("log.txt", "w")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            # event = keyboard.read_event(suppress=True)
            # if event.event_type == keyboard.KEY_DOWN:
            #     if event.name == "s":
            #         if started == False:
            #             started = True
            #             print("Server has started!")
            #         else:
            #             started = False
            #             print("Server is on pause!")
            #     elif event.name == "q":
            #         print("Quitting Program!")
            #         break
            # if started == True:
            # time.sleep(1/128)
            sample, timestamp = inlet.pull_sample()
            if timestamp != None:
                values = [sample[3], sample[4], 
                        sample[5], sample[14], 
                        sample[15], sample[16], 
                        sample[6], sample[7], 
                        sample[8], sample[9],
                        sample[17], sample[18], 
                        sample[19], sample[10], 
                        sample[11], sample[22], 
                        sample[21], sample[20],
                        sample[12], sample[13],
                        sample[23], sample[24]]
                if queue == True:
                    data.pop(0)
                data.append(values)
                sample_count += 1
            if sample_count == 512:
                data_return = standardize_data(data_converter(data), 22)
                label = model.predict(data_return)
                res = labelManipulate(label)
                print(type(res))
                group.append(res)
                print("Predicted: " + str(len(group)) + "/10")
                if len(group) == 10:
                    temp = mostFrequentLabels(group)
                    print(type(temp))
                    conn.sendall(bytes(temp, 'utf-8'))
                    print("Group: " + str(group))
                    print("Res: " + str(temp))
                    group = []
                sample_count -= 128
                queue = True
    
