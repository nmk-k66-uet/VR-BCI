"""Example program to show how to read a multi-channel time series from LSL."""
import time
from pylsl import StreamInlet, resolve_stream
<<<<<<< Updated upstream

print("looking for a stream...")
# first resolve a EEG stream on the lab network
streams1 = resolve_stream('type', 'EEG') # You can try other stream types such as: EEG, EEG-Quality, Contact-Quality, Performance-Metrics, Band-Power
print(streams1)
streams2 = resolve_stream('type', 'Motion')
print(streams2)
=======
from sklearn.preprocessing import StandardScaler
import utils
import os
import sys
import shutil
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import CategoricalCrossentropy
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from sklearn.metrics import confusion_matrix, accuracy_score, ConfusionMatrixDisplay
from sklearn.metrics import cohen_kappa_score
from sklearn.model_selection import train_test_split

import models 
# from preprocess import get_data
from test import get_data
# from keras.utils.vis_utils import plot_model

# Set dataset paramters 
dataset_conf = { 'name': 'BCI2a', 'n_classes': 4, 'cl_labels': ['Left hand', 'Right hand', 'Foot', 'Tongue'],
                    'n_sub': 9, 'n_channels': 3, 'in_samples': 500,
                    'data_path': './datasets/BCI2a/raw/', 'isStandard': True, 'LOSO': True}

model = utils.getModel('ATCNet', dataset_conf)
model.load_weights('./results_ATCNet/saved models/run-1/subject-1.weights.h5')

print("looking for a stream...")
# first resolve a EEG stream on the lab network
streams = resolve_stream('type', 'EEG') # You can try other stream types such as: EEG, EEG-Quality, Contact-Quality, Performance-Metrics, Band-Power
print(streams)

def standardize_data(data, channels): 
    # X_train & X_test :[Trials, MI-tasks, Channels, Time points]
    for j in range(channels):
          scaler = StandardScaler()
          scaler.fit(data[:, 0, j, :])
          data[:, 0, j, :] = scaler.transform(data[:, 0, j, :])

    return data
>>>>>>> Stashed changes

# ch_lst = [['CMS', 'TP9'],
#           ['DRL', 'TP10'],
#           ['LL', 'FCz'],
<<<<<<< Updated upstream
#           ['LM', 'C3'],
#           ['LO', 'C1'],
#           ['LP', 'C5'],
#           ['RL', 'Cz'],
#           ['RM', 'C4'],
=======
#           ['LM', 'C3'],3
#           ['LO', 'C1'],
#           ['LP', 'C5'],
#           ['RL', 'Cz'],6
#           ['RM', 'C4'],7
>>>>>>> Stashed changes
#           ['RN', 'CPz'],
#           ['RO', 'C2'],
#           ['RP', 'C6']]

# create a new inlet to read from the stream
<<<<<<< Updated upstream
inlet1 = StreamInlet(streams1[0])
inlet2 = StreamInlet(streams2[0])

f = open("log.txt", "x")

index = 0
counter = 0
=======
inlet = StreamInlet(streams[0])

f = open("log.txt", "w")

data = []
data_return = np.zeros((1, 3, 500))
t1 = 0
t2 = 500

second = 0
counter = 0
sample_count = 0
>>>>>>> Stashed changes
check = False

while True:
    # Returns a tuple (sample,timestamp) where sample is a list of channel values and timestamp is the capture time of the sample on the remote machine,
    # or (None,None) if no new sample was available
<<<<<<< Updated upstream
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
=======
    sample, timestamp = inlet.pull_sample()
    if second == 0 and check == False:
        f.write("Index of chunk: " + str(second) + '\n')
        check = True
    if timestamp != None:
        # f.write("EEG Data" + '\n')
        f.write(str(sample) + '\n')
        # print(sample)
        values = [sample[6], sample[9], sample[10]]
        data.append(values)
        # f.write("Motion Data" + '\n')
        # f.write(str(sample2) + '\n')
        counter += 1
        sample_count += 1
    if counter == 128:
        second += 1
        f.write("Index of chunk: " + str(second) + '\n')
        counter = 0
    if sample_count == 500:
        break

data_return[0, :, :] = np.transpose(np.array(data))
data_return = data_return[0:1, :, t1:t2]
N_tr, N_ch, T = data_return.shape
data_return = data_return.reshape(N_tr, 1, N_ch, T)
print(data_return.shape)

data_return = standardize_data(data_return, 3)
print(data_return.shape)

label = model.predict(data_return).argmax(axis = -1)
print(label)
>>>>>>> Stashed changes
