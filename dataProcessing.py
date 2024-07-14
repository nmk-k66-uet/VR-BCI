import os
import numpy as np
import pandas as pd
import json

data_source = "data"

subject_name = "Vu Thanh Long"
session_scenario = "Pointer"
global setup
setup = None
global labels
labels = None

if subject_name == "" and session_scenario == "":
    subject_name = input("Enter subject name: ")
    session_scenario = input("Enter session scenario: ")

def read_raw_data(dir):
    df = pd.read_csv(dir, header=None)
    arr = df.to_numpy()
    arr = np.delete(arr, 0, axis=0).transpose()
    # print(arr)

def load_VKIST_data(data_path, all_trials = True):
    global setup
    global labels
    for folder in os.listdir(data_source):
        date = os.path.join(data_source, folder)
        for scenario in os.listdir(date):
            session = os.path.join(date, scenario)
            subject = os.path.join(session, subject_name)
            for file in os.listdir(subject):
                if file.endswith(".csv") and "Artifact" not in file:
                    read_raw_data(os.path.join(subject, file))
                elif file.endswith(".json") and setup == None:
                    setup = json.load(open(os.path.join(subject, file)))
                    print(setup)
                elif file.endswith(".txt"):
                    if labels == None:
                        labels = open(os.path.join(subject, file)).read().splitlines()
                        print(labels)
                        break

load_VKIST_data(data_source)

print(type(setup.get('duration')))
# print(subject_name)



