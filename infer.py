import collections
import numpy as np
import tensorflow as tf
from scipy.signal import resample, butter, filtfilt
import models

# Parameters:
""" 
    data: each EEG trial, duration = 4.5s
    gt: ground truth, 0 = Right, 1 = Left
    res: final prediction result of 6 consecutive trials
    group: predicted result for each trial
"""
data, gt, res = None, None, None
global model, group
model = models.ComplexDBEEGNet_classifier(2, 22, 1125)
model.load_weights('subject-1.weights.h5', by_name=True, skip_mismatch=True)
group = []

def mostFrequentLabels():
    """
        Calculate most frequent label in group of 6 consecutive trials
    """
    global group
    counter = collections.Counter(group)
    res = counter.most_common(1)
    return res[0][0]

def process_data(data, gt):
    """
        Process raw data
        data: raw data, only values of 22 channels, column is electrode, row is timepoint
        gt: ground truth of training scheme
    """
    def up_sample(input_arr, old_rate=128, new_rate=250):
        new_length = int(len(input_arr) * new_rate / old_rate)
        resampled_arr = resample(input_arr, new_length)
        return resampled_arr

    def butter_bandpass(lowcut=8, highcut=30, fs=250, order=4):
        nyquist = 0.5 * fs
        low = lowcut/nyquist
        high = highcut/nyquist
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def process_VKIST_data(data):
        slice_2d = np.fft.fft2(slice_2d)
        real_part = np.real(slice_2d)
        imag_part = np.imag(slice_2d)
        combined_signal = np.stack((real_part, imag_part), axis=-1)
        X_return.append(combined_signal)
        X_return = np.array(X_return)
        return X_return
    
    global model, group
    temp = []
    data = data.transpose()
    """
        Preprocess signal of each electrodes: butter bandpass => upsample => fourier transform
    """
    for i in range(0, 22):
        b, a = butter_bandpass(fs=128, lowcut=8, highcut=40)
        filtered_signal = filtfilt(b, a, data[i])
        up_sampled_signal = up_sample(filtered_signal)
        temp.append(up_sampled_signal)
    X_test = temp
    X_test= process_VKIST_data(X_test)
    y_test = gt
    """
        Predict trial label. Accept variance <= 1% 
    """
    res = model.predict(X_test.reshape(1, 2, 22, 1125))
    result = res.argmax(axis=-1)[0]
    a = abs(res[0][1] - 1)
    if y_test == 0:
        if result == 1 and a <= 1:
            result = 0
    else:
        if result == 0 and a <= 1:
            result = 1
    group.append(process_data(data, gt)) # Append each trial label into a group 

if len(group) == 6:
    res = mostFrequentLabels() # Calculate final result if a group has 6 trials
    group = []                      # Reset the group
