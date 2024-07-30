import os
import numpy as np
import pandas as pd
import json
import mne

data_source = "data/VKIST"
action_list = ['Action.R', 'Action.C', 'Action.RH', 'Action.LH', 
               'Action.RF', 'Action.LF', 'Action.PTL', 'Action.PTR', 
               'Action.B', 'Action.OCM', 'Action.NH', 'Action.SH', 
               'Action.RHOC', 'Action.LHOC', 'Action.T', 'Action.A', 
               'Action.M']

subject_name = "Vu Thanh Long"
session_scenario = "Pointer"

if subject_name == "" and session_scenario == "":
    subject_name = input("Enter subject name: ")
    session_scenario = input("Enter session scenario: ")

def read_raw_data(dir):
    df = pd.read_csv(dir, header=None)
    arr = df.to_numpy()
    arr = np.delete(arr, 0, axis=0).transpose()
    return arr

def process_VKIST_data(setup, X, y):
    data, X_return, y_return = [], [], None
    cur_sample, f = 0, 128
    for i in range(0, 22):
        data.append([])
    for label in y[:]:
        dur = setup.get('duration').get(action_list[label - 1])
        match label:
            case 1:
                cur_sample += (dur * f)
                y.remove(label)
            case 2:
                cur_sample += int((dur - 0.5) * f)
                y.remove(label)
            case default:
                begin = cur_sample
                end = cur_sample + int((dur + 0.5) * f)
                for i in range(0, len(X)):
                    data[i] = [*data[i], *X[i][begin : end]]
                    cur_sample = end

    data = np.array(data)
    slice_size = int(4.5 * f)
    for i in range(0, data.shape[1], slice_size):
        if i + slice_size <= data.shape[1]:
            slice_2d = data[:, i : (i + slice_size)]
            X_return.append(slice_2d)
    
    X_return = np.array(X_return)
    y_return = np.array(y)
    X_train, X_test = np.split(X_return, [int(0.8 * X_return.shape[0])], axis=0)
    y_train, y_test = np.split(np.array(y_return) - np.min(y_return), [int(0.8 * y_return.shape[0])], axis=0)
    # y_train_onehot = to_categorical(y_train)

    return X_train, y_train, X_test, y_test

def load_VKIST_data(data_path, all_trials = True):
    setup, calibrated, no_runs, X_train, y_train, X_test, y_test = None, None, None, None, None, None, None

    for folder in os.listdir(data_source):
        date = os.path.join(data_source, folder)
        for scenario in os.listdir(date):
            if scenario != session_scenario:
                continue
            session = os.path.join(date, scenario)
            subject = os.path.join(session, subject_name)
            for file in os.listdir(subject):
                if file.endswith(".csv"):
                    # print(file)
                    if "Artifact" in file and all_trials == False:
                        continue
                    data = read_raw_data(os.path.join(subject, file))
                    if X_train is not None:
                        X_train = np.concatenate((X_train, data), axis=1)
                    else:
                        X_train = data
                elif file.endswith(".json") and setup == None:
                    setup = json.load(open(os.path.join(subject, file)))
                    calibrated = setup.get('calibrated')
                    no_runs = setup.get('num_of_runs')
                elif file.endswith(".txt"):
                    if "Artifact" in file and all_trials == False:
                        continue   
                    labels = list(map(int, open(os.path.join(subject, file)).read().splitlines()))
                    if y_train is not None:
                        y_train = y_train + labels
                    else:
                        y_train = labels

    temp = []
    print(X_train)
    electrodes_map = [0, 1, 2, 11, 12, 13, 3, 4, 5, 6, 14, 15, 16, 7, 8, 19, 18, 17, 9, 10, 20, 21]
    for i in electrodes_map:
        temp.append(X_train[i])
    X_train = temp
    
    X_train, y_train, X_test, y_test = process_VKIST_data(setup, X_train, y_train)

    return setup, calibrated, no_runs, X_train, y_train, X_test, y_test
    

# setup, calibrated, no_runs, X_train, y_train, X_test, y_test = load_VKIST_data(data_source)
# # print(setup)
# # print(calibrated)
# # print(no_runs)
# print(X_train.shape)
# print(y_train.shape)
# # print(y_train)
# print(X_test.shape)
# print(y_test.shape)
path = "data/VKIST/17_July_2024/Pointer/Vu Thanh Long/Vu Thanh Long_17_July_2024_14_08_51_Ha Noi_VKIST.csv"

raw_data = read_raw_data(path)
data = []
setup = json.load(open("data/VKIST/11_July_2024/Pointer/Vu Thanh Long/Vu Thanh Long_11_July_2024_14_38_28_Ha Noi_VKIST.json"))
calibrated = setup.get('calibrated')
no_runs = setup.get('num_of_runs')

ch_names = ["Fz", "FC3", "FC1", "C5", "C3", "C1", "Cz", "CP3", "CP1", "P1", "Pz", "FCz", "FC2", "FC4", "C2", "C4", "C6", "CP4", "CP2", "CPz", "P2", "POz"]
ch_num = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
sfreq = 128

event_codes = list(map(int, open("data/VKIST/11_July_2024/Pointer/Vu Thanh Long/Vu Thanh Long_11_July_2024_14_38_28_Ha Noi_VKIST.txt").read().splitlines()))
# event_names = []
# for event_code in event_codes:
#     name = None
#     match event_code:
#         case 1: name = "Rest"
#         case 2: name = "Cue"
#         case 3: name = "Right Hand"
#         case 4: name = "Left Hand"
#         case 5: name = "Right Leg"
#         case 6: name = "Left Leg"
#     event_names.append(name)
    
event_trigger = np.zeros(len(event_codes))
event_timestamp = []
cur_timestamp = 0
for event in event_codes:
    event_timestamp.append(cur_timestamp)
    if (event == 1 or event == 2): cur_timestamp += 2*sfreq
    else: cur_timestamp += 4*sfreq
event_timestamp = np.transpose(np.array(event_timestamp))
event_trigger = np.transpose(event_trigger)
event_codes = np.transpose(np.array(event_codes))
events = np.column_stack((np.column_stack((event_timestamp, event_trigger)), event_codes))
events = np.array(events)
print(events)

dummy = raw_data[ch_num[0], : ]
for i in range(1, len(ch_num)):
    dummy = np.row_stack((dummy, raw_data[i, : ]))
print(dummy.shape)

info = mne.create_info(ch_names = ch_names, sfreq = sfreq)
raw = mne.io.RawArray(dummy, info)
raw.plot(block=True, scalings=None, events=events, highpass=8, lowpass=30)
# print(subject_name)
# eog_epochs = mne.preprocessing.create_eog_epochs(raw=raw, ch_name=ch_names, picks=[1, 2], l_freq=30, h_freq=8)
# eog_epochs.plot_image(combine="mean", picks=1)





