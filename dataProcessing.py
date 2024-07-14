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

def load_VKIST_data(data_path, all_trials = True):
    setup, X_train, y_train = None, None, None

    for folder in os.listdir(data_source):
        date = os.path.join(data_source, folder)
        for scenario in os.listdir(date):
            session = os.path.join(date, scenario)
            subject = os.path.join(session, subject_name)
            for file in os.listdir(subject):
                if file.endswith(".csv"):
                    if "Artifact" in file and all_trials == False:
                        pass
                    else:
                        data = read_raw_data(os.path.join(subject, file))
                        if X_train is not None:
                            X_train += data
                        else:
                            X_train = data
                elif file.endswith(".json") and setup == None:
                    setup = json.load(open(os.path.join(subject, file)))
                elif file.endswith(".txt"):
                    labels = list(map(int, open(os.path.join(subject, file)).read().splitlines()))
                    if y_train is not None:
                        y_train += labels
                    else:
                        y_train = labels
    
    calibrated = setup.get('calibrated')
    no_runs = setup.get('num_of_runs')

    return setup, calibrated, no_runs, X_train, labels
    

setup, calibrated, no_runs, X_train, y_train = load_VKIST_data(data_source)
print(setup)
print(calibrated)
print(no_runs)
print(X_train.shape)
print(y_train)

# print(subject_name)



