"""Example program to show how to read a multi-channel time series from LSL."""
import time
import  UdpComms as U
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
from test1 import get_data
# from keras.utils.vis_utils import plot_model

# Set dataset paramters 
dataset_conf = { 'name': 'BCI2a', 'n_classes': 4, 'cl_labels': ['Left hand', 'Right hand', 'Foot', 'Tongue'],
                    'n_sub': 9, 'n_channels': 9, 'in_samples': 512,
                    'data_path': './datasets/BCI2a/raw/', 'isStandard': True, 'LOSO': True}

model = utils.getModel('EEGTCNet', dataset_conf)
model.load_weights('./results_EEGTCNet/saved models/run-1/subject-1.weights.h5')

_, _, _, X_test, y_test, y_test_onehot = get_data('./datasets/BCI2a/raw/', 1, 'BCI2a', LOSO = True, isStandard = True, isShuffle=False)

countFalse = 0
countFalseRec = 0

for i in range (0, len(y_test)):
    label = model.predict(X_test[i].reshape(1,1,9,512))
    lb = label.argmax(axis = -1)
    gt = y_test[i]
    if lb[0] != gt:
        countFalse += 1
    res = 0
    if label[0][0] >= 0.3 or label[0][1] >= 0.3:
        res = max(label[0][0], label[0][1])
        if res == label[0][0]:
            res = 0
        else:
            res = 1
        if res != gt: 
            countFalseRec += 1
    else:
        res = label.argmax(axis = -1)
        if res[0] != gt:
            countFalseRec += 1
    print("Model prediction:", label)
    print("Ground truth:", gt)
    print("Result:", res)

print("Number of False Labels: ", countFalse)
print("Number of False Labels after Reduction: ", countFalseRec)

# label = model.predict(data_return)
# print(label)
# label = model.predict(data_return).argmax(axis=-1)
# print(label)
