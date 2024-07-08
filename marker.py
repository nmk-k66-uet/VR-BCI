import pyedflib as plib
import numpy as np
import matplotlib.pyplot as plt

path = "D:/BCI_Keyboard/EEG_Data/DoThiTrang01_EPOCFLEX_195777_2023.11.25T10.52.38+07.00.edf"
inputSignals, signal_headers, header = plib.highlevel.read_edf(path)

colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
          'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan',
          'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
          'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan',
          'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
          'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan',
          'tab:brown', 'tab:pink']
targets = ["TP9", "TP10", "C3", "T7", "FC1", "FC5", "FT9", "F3",
           "F7", "Fp1", "Pz", "Cz", "O1", "PO9", "P3", "P7", "CP1",
           "CP5", "C4", "T8", "FC2", "FC6", "FT10", "F4", "F8",
           "Fp2", "Oz", "Fz", "O2", "PO10", "P4", "P8", "CP2", "CP6"]
outputSignals = []

for i in range(0, len(signal_headers)):
    if signal_headers[i]["label"] in targets:
        outputSignals.append(inputSignals[i])

# print("Headers: ")
# print(header)
figure, axes = plt.subplots(16, 2)
x, y = 0, 0
for i in range(0, len(outputSignals)):
    axes[x][y].plot(outputSignals[i], color=colors[i])
    axes[x][y].set_title(targets[i])
    if y < 1:
        y += 1
    else:
        y = 0
        x += 1

plt.legend()
plt.show()
