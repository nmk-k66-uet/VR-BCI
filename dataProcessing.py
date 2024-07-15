import os
import numpy as np
import pandas as pd
import json

data_source = "data"
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

def process_VKIST_data(setup, X_train, y_train):
    X_return = []
    cur_sample, f = 0, 128
    for i in range(0, 22):
        X_return.append([])
    for label in y_train[:]:
        dur = setup.get('duration').get(action_list[label - 1])
        match label:
            case 1:
                cur_sample += (dur * f)
                y_train.remove(label)
            case 2:
                cur_sample += int((dur - 0.5) * f)
                y_train.remove(label)
            case default:
                begin = cur_sample
                end = cur_sample + int((dur + 0.5) * f)
                for i in range(0, len(X_train)):
                    X_return[i] = [*X_return[i], *X_train[i][begin : end]]
                    cur_sample = end
    X_return = np.array(X_return)
    return X_return, y_train

def load_VKIST_data(data_path, all_trials = True):
    setup, calibrated, no_runs, X_train, y_train = None, None, None, None, None

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
    
    X_train, y_train = process_VKIST_data(setup, X_train, y_train)

    return setup, calibrated, no_runs, X_train, y_train
    

setup, calibrated, no_runs, X_train, y_train = load_VKIST_data(data_source)
print(setup)
print(calibrated)
print(no_runs)
print(X_train.shape)
print(len(y_train))
# print(y_train)

# print(subject_name)



