# Dataset BCI Competition IV-2a is available at 
# http://bnci-horizon-2020.eu/database/data-sets

import os
import json
import numpy as np
import scipy.io as sio
import pandas as pd
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle
from scipy.signal import resample

#%%
def load_data_LOSO (data_path, subject, dataset): 
    """ Loading and Dividing of the data set based on the 
    'Leave One Subject Out' (LOSO) evaluation approach. 
    LOSO is used for  Subject-independent evaluation.
    In LOSO, the model is trained and evaluated by several folds, equal to the 
    number of subjects, and for each fold, one subject is used for evaluation
    and the others for training. The LOSO evaluation technique ensures that 
    separate subjects (not visible in the training data) are usedto evaluate 
    the model.
    
        Parameters
        ----------
        data_path: string
            dataset path
            # Dataset BCI Competition IV-2a is available at 
            # http://bnci-horizon-2020.eu/database/data-sets
        subject: int
            number of subject in [1, .. ,9/14]
            Here, the subject data is used  test the model and other subjects data
            for training
    """
    X_train, y_train = [], []
    for sub in range (0,9):
        print("Loading on data file no" + str(sub+1))
        path = data_path+'s' + str(sub+1) + '/'
        
        if (dataset == 'BCI2a'):
            X1, y1 = load_BCI2a_data(path, sub+1, True)
            X2, y2 = load_BCI2a_data(path, sub+1, False)
        
        X = np.concatenate((X1, X2), axis=0)
        y = np.concatenate((y1, y2), axis=0)
                   
        if (sub == subject):
            X_test = X
            y_test = y
        elif (len(X_train) == 0):
            X_train = X
            y_train = y
        else:
            X_train = np.concatenate((X_train, X), axis=0)
            y_train = np.concatenate((y_train, y), axis=0)

    return X_train, y_train, X_test, y_test


#%%
def load_BCI2a_data(data_path, subject, training, all_trials = True):
    """ Loading and Dividing of the data set based on the subject-specific 
    (subject-dependent) approach.
    In this approach, we used the same training and testing dataas the original
    competition, i.e.:
    - A total of 9 subjects, 2 sessions for each subject
    - 48 trials x 6 runs in session 1 for training, 
    and 48 trials x 6 runs in session 2 for testing, yielding a total of 288 trials per session.  
    288 
        Parameters
        ----------
        data_path: string
            dataset path
            # Dataset BCI Competition IV-2a is available on 
            # http://bnci-horizon-2020.eu/database/data-sets
        subject: int
            number of subject in [1, .. ,9]
        training: bool
            if True, load training data
            if False, load testing data
        all_trials: bool
            if True, load all trials
            if False, ignore trials with artifacts 
    """
    
    # Define MI-trials parameters
    n_channels = 22
    n_tests = 6*48     
    window_Length = 7*250 
    
    # Define MI trial window 
    fs = 250          # sampling rate
    t1 = int(1.5*fs)  # start time_point
    t2 = int(6*fs)    # end time_point

    class_return = np.zeros(n_tests)
    data_return = np.zeros((n_tests, n_channels, window_Length))

    NO_valid_trial = 0
    if training:
        a = sio.loadmat(data_path+'A0'+str(subject)+'T.mat')
    else:
        a = sio.loadmat(data_path+'A0'+str(subject)+'E.mat')
    a_data = a['data']
    for ii in range(0,a_data.size):
        a_data1 = a_data[0,ii]
        a_data2= [a_data1[0,0]]
        a_data3= a_data2[0]
        a_X         = a_data3[0]
        a_trial     = a_data3[1]
        a_y         = a_data3[2]
        a_artifacts = a_data3[5]

        for trial in range(0,a_trial.size):
             if(a_artifacts[trial] != 0 and not all_trials):
                 continue
             data_return[NO_valid_trial,:,:] = np.transpose(a_X[int(a_trial[trial]):(int(a_trial[trial])+window_Length),:22])
             class_return[NO_valid_trial] = int(a_y[trial])
             NO_valid_trial +=1        
    

    data_return = data_return[0:NO_valid_trial, :, t1:t2]
    class_return = class_return[0:NO_valid_trial]
    class_return = (class_return-1).astype(int)

    return data_return, class_return

#%% Load VKIST private data
action_list = ['Action.R', 'Action.C', 'Action.RH', 'Action.LH', 
               'Action.RF', 'Action.LF', 'Action.PTL', 'Action.PTR', 
               'Action.B', 'Action.OCM', 'Action.NH', 'Action.SH', 
               'Action.RHOC', 'Action.LHOC', 'Action.T', 'Action.A', 
               'Action.M']

subject_name = "Vu Thanh Long"
session_scenario = "Pointer"

def up_sample(input_arr, old_rate=128, new_rate=250):
    new_length = int(len(input_arr) * new_rate / old_rate)
    resampled_arr = resample(input_arr, new_length)
    return resampled_arr

def read_raw_data(dir):
    df = pd.read_csv(dir, header=None)
    arr = df.to_numpy()
    arr = np.delete(arr, 0, axis=0).transpose()
    return arr

def process_VKIST_data(setup, X, y):
    data, X_return, y_return = [], [], None
    cur_sample, f = 0, 250
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

    for folder in os.listdir(data_path):
        date = os.path.join(data_path, folder)
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
    electrodes_map = [0, 1, 2, 11, 12, 13, 3, 4, 5, 6, 14, 15, 16, 7, 8, 19, 18, 17, 9, 10, 20, 21]
    for i in electrodes_map:
        temp.append(up_sample(X_train[i]))
    X_train = temp
    
    X_train, y_train, X_test, y_test = process_VKIST_data(setup, X_train, y_train)

    return X_train, y_train, X_test, y_test

#%%
def standardize_data(X_train, X_test, channels): 
    # X_train & X_test :[Trials, MI-tasks, Channels, Time points]
    for j in range(channels):
          scaler = StandardScaler()
          scaler.fit(X_train[:, 0, j, :])
          X_train[:, 0, j, :] = scaler.transform(X_train[:, 0, j, :])
          X_test[:, 0, j, :] = scaler.transform(X_test[:, 0, j, :])

    return X_train, X_test

#%%
def get_data(path, subject, dataset = 'BCI2a', classes_labels = 'all', LOSO = False, isStandard = True, isShuffle = True):
    
    # Load and split the dataset into training and testing 
    if LOSO:
        """ Loading and Dividing of the dataset based on the 
        'Leave One Subject Out' (LOSO) evaluation approach. """ 
        X_train, y_train, X_test, y_test = load_data_LOSO(path, subject, dataset)
    else:
        """ Loading and Dividing of the data set based on the subject-specific 
        (subject-dependent) approach.
        In this approach, we used the same training and testing data as the original
        competition, i.e., for BCI Competition IV-2a, 288 x 9 trials in session 1 
        for training, and 288 x 9 trials in session 2 for testing.  
        """
        if (dataset == 'BCI2a'):
            path = path + 's{:}/'.format(subject+1)
            X_train, y_train = load_BCI2a_data(path, subject+1, True)
            X_test, y_test = load_BCI2a_data(path, subject+1, False)
        elif (dataset == 'VKIST'):
            path = 'data/VKIST'
            X_train, y_train, X_test, y_test = load_VKIST_data(path, True)

    # shuffle the data 
    if isShuffle:
        X_train, y_train = shuffle(X_train, y_train,random_state=42)
        X_test, y_test = shuffle(X_test, y_test,random_state=42)

    # Prepare training data     
    N_tr, N_ch, T = X_train.shape 
    X_train = X_train.reshape(N_tr, 1, N_ch, T)
    y_train_onehot = to_categorical(y_train)
    # Prepare testing data 
    N_tr, N_ch, T = X_test.shape 
    X_test = X_test.reshape(N_tr, 1, N_ch, T)
    y_test_onehot = to_categorical(y_test)    
    
    # Standardize the data
    if isStandard:
        X_train, X_test = standardize_data(X_train, X_test, N_ch)

    return X_train, y_train, y_train_onehot, X_test, y_test, y_test_onehot

X_train, y_train, y_train_onehot, X_test, y_test, y_test_onehot = get_data('data/VKIST', 0, 'VKIST', isStandard=False, isShuffle=False)
print(X_train.shape)
print(y_train.shape)
print(y_train_onehot.shape)
print(X_test.shape)
print(y_test.shape)
print(y_test_onehot.shape)