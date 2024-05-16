import numpy as np
import scipy.io as sio
from scipy.signal import resample
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle

def downsample(input_arr, old_rate=250, new_rate=128):
    new_length = int(len(input_arr) * new_rate / old_rate)
    resampled_arr = resample(input_arr, new_length)
    return resampled_arr

def load_data_LOSO (data_path, subject, dataset): 
    # sub = 0
    X_train, y_train = [], []
    for sub in range (0,9):
        print("Loading on data file no" + str(sub+1))
        path = data_path+'s' + str(sub+1) + '/'
        
        if (dataset == 'BCI2a'):
            X1, y1 = load_BCI2a_data(path, sub+1, training=True)
            X2, y2 = load_BCI2a_data(path, sub+1, training=False)
        
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
    # Define MI-trials parameters
    total_channels = 22
    # for this approach we selects data from 11 channels: FCz, C5, C3, C1, Cz, C2, C4, C6, CPz
    # these channels'indexes are as follow respectively
    selected_channels = [4, 7, 8, 9, 10, 11, 12, 13, 16]
    n_tests = 6*48
    org_window_Length = 7*250
    window_Length = 7*128
    
    # Define MI trial window 
    fs = 250          # sampling rate
    t1 = int(1.5*fs)  # start time_point
    t2 = int(6*fs)    # end time_point
    t_1 = int(2*128)
    t_2 = int(6*128)

    label_return = np.zeros(n_tests)
    data_return = np.zeros((n_tests, len(selected_channels), window_Length))

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
            # print(a_X[int(a_trial[trial]):(int(a_trial[trial])+window_Length),:22].shape)
            temp = []
            # if all_trials == True:
            #     print("Trial :", trial)
            #     print("Index: ", int(a_trial[trial]), int(a_trial[trial])+window_Length)
            for i in selected_channels:
                temp.append(downsample(a_X[int(a_trial[trial]):(int(a_trial[trial])+org_window_Length),i-1]))
                # print(type(temp[0][0]))
            temp = np.array(temp)
            # print(temp.shape)
            # print(np.transpose(np.array(temp)).shape)
            # print(data_return[NO_valid_trial,:,:].shape)
            data_return[NO_valid_trial,:,:] = np.array(temp)
            # print("Data_return: ", data_return[NO_valid_trial, :,:])
            label_return[NO_valid_trial] = int(a_y[trial])
            # print("label_return: ", label_return[NO_valid_trial])
            NO_valid_trial +=1      
            

    data_return = data_return[0:NO_valid_trial, :, t_1:t_2]
    # print(data_return.shape)
    label_return = label_return[0:NO_valid_trial]
    label_return = (label_return-1).astype(int)
    # print(label_return.shape)

    return data_return, label_return

def standardize_data(X_train, X_test, channels): 
    # X_train & X_test :[Trials, MI-tasks, Channels, Time points]
    for j in range(channels):
          scaler = StandardScaler()
          scaler.fit(X_train[:, 0, j, :])
          X_train[:, 0, j, :] = scaler.transform(X_train[:, 0, j, :])
          X_test[:, 0, j, :] = scaler.transform(X_test[:, 0, j, :])

    return X_train, X_test

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
    # shuffle the data 
    if isShuffle:
        X_train, y_train = shuffle(X_train, y_train,random_state=42)
        X_test, y_test = shuffle(X_test, y_test,random_state=42)
    # Prepare training data     
    N_tr, N_ch, T = X_train.shape
    X_train = X_train.reshape(N_tr, 1, N_ch, T)
    # print("Data per channel:")
    # print(X_train[0][0][0])
    # print("Data per label")
    # print(X_train[0][0])
    # print("Data per trial")
    # print(X_train[0])
    # print(len(y_train))
    y_train_onehot = to_categorical(y_train)
    # Prepare testing data 
    N_tr, N_ch, T = X_test.shape 
    X_test = X_test.reshape(N_tr, 1, N_ch, T)
    y_test_onehot = to_categorical(y_test)    
    
    # Standardize the data
    if isStandard:
        X_train, X_test = standardize_data(X_train, X_test, N_ch)

    return X_train, y_train, y_train_onehot, X_test, y_test, y_test_onehot

# X_train, y_train, X_test, y_test = load_data_LOSO('datasets/BCI2a/raw/', 0, 'BCI2a')
# print(len(X_train))
# print(len(y_train))
# print(X_test.shape)
# print(y_test.shape)

# X_train, _, y_train_onehot, x_test, _, _ = get_data('datasets/BCI2a/raw/', 0, 'BCI2a', LOSO = True, isStandard = True)
# print(X_train.shape)
# print(y_train_onehot.shape)
# print(x_test.shape)

# data_return, class_return = load_BCI2a_data('datasets/BCI2a/raw/s1/', 1, True, True)
