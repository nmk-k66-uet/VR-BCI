"""Example program to show how to read a multi-channel time series from LSL."""
import time
from pylsl import StreamInlet, resolve_stream
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
                    'n_sub': 9, 'n_channels': 9, 'in_samples': 512,
                    'data_path': './datasets/BCI2a/raw/', 'isStandard': True, 'LOSO': True}

model = utils.getModel('EEGTCNet', dataset_conf)
model.load_weights('./results_EEGTCNet/saved models/run-1/subject-1.weights.h5')

print("looking for a stream...")
# first resolve a EEG stream on the lab network
streams = resolve_stream('type', 'EEG') # You can try other stream types such as: EEG, EEG-Quality, Contact-Quality, Performance-Metrics, Band-Power
print(streams)

data = []

t1 = 0
t2 = 512

def standardize_data(data, channels): 
    # X_train & X_test :[Trials, MI-tasks, Channels, Time points]
    for j in range(channels):
          scaler = StandardScaler()
          scaler.fit(data[:, 0, j, :])
          data[:, 0, j, :] = scaler.transform(data[:, 0, j, :])
    return data

def data_converter(data):
    data_return = np.zeros((1, 9, 512))
    data_return[0, :, :] = np.transpose(np.array(data))
    data_return = data_return[0:1, :, t1:t2]
    N_tr, N_ch, T = data_return.shape
    data_return = data_return.reshape(N_tr, 1, N_ch, T)
    return data_return


# ch_lst = [['CMS', 'TP9'],3
#           ['DRL', 'TP10'],4
#           ['LL', 'FCz'],5
#           ['LM', 'C3'],6
#           ['LO', 'C1'],7
#           ['LP', 'C5'],8
#           ['RL', 'Cz'],9
#           ['RM', 'C4'],10
#           ['RN', 'CPz'],11
#           ['RO', 'C2'],12
#           ['RP', 'C6']]13

# create a new inlet to read from the stream
inlet = StreamInlet(streams[0])

f = open("log.txt", "w")

data = []
data_return = np.zeros((1, 9, 512))
t1 = 0
t2 = 512

second = 0
counter = 0
sample_count = 0
queue = False
label_count = 0

while True:
    # Returns a tuple (sample,timestamp) where sample is a list of channel values and timestamp is the capture time of the sample on the remote machine,
    # or (None,None) if no new sample was available
    sample, timestamp = inlet.pull_sample()
    if timestamp != None:
        # f.write("EEG Data" + '\n')
        # f.write(str(sample) + '\n')
        # print(sample)
        values = [sample[5], sample[8], sample[6], sample[7], sample[9], sample[12], sample[10], sample[13], sample[11]]
        if queue == True:
            data.pop(0)
        data.append(values)
        # f.write("Motion Data" + '\n')
        # f.write(str(sample2) + '\n')
        counter += 1
        sample_count += 1
        print("Sample_count: ", sample_count)
    if counter == 128:
        second += 1
        # f.write("Index of chunk: " + str(second) + '\n')
        counter = 0
    if sample_count == 512:
        data_return = standardize_data(data_converter(data), 9)
        label = model.predict(data_return).argmax(axis=-1)
        print(label)
        label_count += 1
        sample_count -= 128
        queue = True
    if label_count == 10:
        break

# label = model.predict(data_return)
# print(label)
label = model.predict(data_return).argmax(axis=-1)
print(label)
