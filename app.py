import customtkinter as CTk
import json
from pylsl import StreamInlet, resolve_stream
import socket
from socket import SHUT_RDWR

CTk.set_appearance_mode("light")
CTk.set_default_color_theme("green")

# Init main app
app = CTk.CTk()

# Calulate window position
w, h = 1280, 720
ws = app.winfo_screenwidth()
hs = app.winfo_screenheight()
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)

# Main app configuration
app.title("VR-BCI")
app.resizable(False, False)
app.geometry('%dx%d+%d+%d'% (w, h, x, y))
app.iconbitmap("assets/icon/cat_icon.ico")

# Create tab view
tabs = CTk.CTkTabview(app, width=1200, height=675)
tabs.pack()

# Create tabs
home = tabs.add("Home")
recording = tabs.add("Recording")
training = tabs.add("Training")
settings = tabs.add("Settings")

# Add elements to Home Tab
# EEG Stream attributes
eeg_stream = None

def toggle_eeg_connection():
    if eeg_connection_flag.get() == 0:
        eeg_stream = None
        eeg_connection.configure(text="Connect Emotiv Headset | Disconnected")
    elif eeg_connection_flag.get() == 1:
        # eeg_stream = resolve_stream('type', 'EEG')
        eeg_connection.configure(text="Connect Emotiv Headset | Connected")

eeg_connection_flag = CTk.IntVar(value=0)
eeg_connection = CTk.CTkSwitch(home, text="Connect Emotiv Headset",
                               command=toggle_eeg_connection, variable=eeg_connection_flag,
                               onvalue=1, offvalue=0,
                               switch_width=48, switch_height=27)
eeg_connection.pack(pady=20)

# VR Stream Attribute
tcp_socket, conn, addr = None, None, None
HOST, PORT = "192.168.137.1", 8000

def toggle_vr_connection():
    if vr_connection_flag.get() == 1:
        # tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # tcp_socket.bind((HOST, PORT))
        # tcp_socket.listen()
        # conn, addr = tcp_socket.accept()
        # with conn:
        #     vr_connection.configure(text="Connect Oculus Headset | Connected")
        vr_connection.configure(text="Connect Oculus Headset | Connected")
    elif vr_connection_flag.get() == 0:
        tcp_socket.shutdown(SHUT_RDWR)
        tcp_socket.close()
        tcp_socket, conn, addr = None, None, None
        vr_connection.configure(text="Connect Oculus Headset | Disconnected")
        
vr_connection_flag = CTk.IntVar(value=0)
vr_connection = CTk.CTkSwitch(home, text="Connect Oculus Headset",
                               command=toggle_vr_connection, variable=vr_connection_flag,
                               onvalue=1, offvalue=0,
                               switch_width=48, switch_height=27)
vr_connection.pack(pady=30)

# Add elements to Settings Tab
# Light and Dark Mode switch
def switch_display_mode():
    if display_mode_flag.get() == 0:
        CTk.set_appearance_mode("light")
    elif display_mode_flag.get() == 1:
        CTk.set_appearance_mode("dark")

display_mode_flag = CTk.IntVar(value=0)
display_mode = CTk.CTkSwitch(settings, text="Dark Mode", 
                             command=switch_display_mode, variable=display_mode_flag, 
                             onvalue=1, offvalue=0,
                             switch_width=48, switch_height=27)
display_mode.pack(pady=20)

# Color theme picker
# def switch_theme(choice):
#     path = "assets/themes/" + choice + ".json"
#     print(path)
#     CTk.set_default_color_theme(path)

# themes = ["Anthracite", "Blue", "Cobalt", "DaynNight", "GhostTrain", "Greengage",
#           "GreyGhost", "Hades", "Harlequin", "MoonlitSky", "NeonBanana", "NightTrain",
#           "Oceanix", "Sweetkind", "TestCard", "TrojanBlue"]
# themes_option = CTk.CTkOptionMenu(settings, values=themes, command=switch_theme)
# themes_option.pack(pady=60)

# Main loop
app.mainloop()
