import os
import numpy as np

data_source = "data"

subject_name = "Vu Thanh Long"
session_scenario = "Pointer"

if subject_name == "" and session_scenario == "":
    subject_name = input("Enter subject name: ")
    session_scenario = input("Enter session scenario: ")

def list_subfolders(dir):
    for file in os.listdir(data_source):
        date = os.path.join(data_source, file)
        # print(date)
        for scenario in os.listdir(date):
            session = os.path.join(date, scenario)
            for file in os.listdir(os.path.join(session, subject_name)):
                if file.endswith(".csv") and "Artifact" not in file:
                    print(os.path.join(file))
        
list_subfolders(data_source)

# print(subject_name)



