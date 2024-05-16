import UdpComms as U
import time
import numpy as np
from keras.models import load_model

# Load model
# model = load_model('model.h5')

# Create UDP socket to use for sending (and receiving)
sock = U.UdpComms(udpIP="127.0.0.1", portTX=8000, portRX=8001, enableRX=True, suppressWarnings=True)

i = 0

while True:
    #Predict
    #pred = model.predict()

    #Send command to Unity VR interface to control doctor model
    sock.SendData(str(input()))

    #Read received data
    # data = sock.ReadReceivedData() # read data

    # if data != None: # if NEW data has been received since last ReadReceivedData function call
    #     print(data) # print new received data

    time.sleep(1)