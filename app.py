import customtkinter as CTk
import json
from pylsl import StreamInlet, resolve_stream
import socket
from socket import SHUT_RDWR
import threading

CTk.set_appearance_mode("light")
CTk.set_default_color_theme("green")
server_running = False

genders = ["Nam", "Nữ"]
# Init main app
# app = CTk.CTk()

# VR Stream Attribute
HOST, PORT = "127.0.0.1", 8000

# Add elements to Settings Tab

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

class App(CTk.CTk):
    def __init__(self):
        super().__init__()
        
        w, h = 1280, 720
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        
        # Main app configuration
        self.title("VR-BCI")
        self.resizable(False, False)
        self.geometry('%dx%d+%d+%d'% (w, h, x, y))
        self.iconbitmap("assets/icon/cat_icon.ico")
        #------------------------------------------------------#
        # Create tab view
        self.tabs = CTk.CTkTabview(self, width=1200, height=675)
        self.tabs.pack()

        # Create tabs
        self.home = self.tabs.add("Home")
        self.recording = self.tabs.add("Recording")
        self.training = self.tabs.add("Training")
        self.settings = self.tabs.add("Settings")
        
        #-------------------------Home--------------------------#
        #EEG Stream connection
        self.eeg_stream = None #LSL Stream for emotiv connection

        self.eeg_connection_flag = CTk.IntVar(value=0)
        def toggle_eeg_connection():
            if self.eeg_connection_flag.get() == 0:
                self.eeg_stream = None
                self.eeg_connection_switch.configure(text="Connect Emotiv Headset | Disconnected")
            else:
                # eeg_stream = resolve_stream('type', 'EEG')
                self.eeg_connection_switch.configure(text="Connect Emotiv Headset | Connected")
        self.eeg_connection_switch = CTk.CTkSwitch(self.home, text="Connect Emotiv Headset",
                                    command=toggle_eeg_connection, variable=self.eeg_connection_flag,
                                    onvalue=1, offvalue=0,
                                    switch_width=48, switch_height=27)
        self.eeg_connection_switch.pack(pady=10)
        
          
        #TCP to VR Connection
        self.server_thread = None
        def handle_client_connection(client_socket):
            while True:
                try:
                    client_socket.send(bytes(input(), 'utf-8')) #demo for connection  via app, need button interface
                except ConnectionResetError:
                    break
            client_socket.close()
        
        def start_server():
            global server_running
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            print(f"Server started and listening on port {PORT}")
            while server_running:
                client_socket, addr = server_socket.accept()
                print(f"Connected from {addr}")
                client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
                client_handler.start()
            server_socket.close()
            
        def start_server_thread(self):
            if self.server_thread is None or not self.server_thread.is_alive():
                self.server_thread = threading.Thread(target=start_server, daemon=True)
                self.server_thread.start()
        
        def toggle_vr_connection():
            global server_running
            if self.vr_connection_flag.get() == 1:
                print(f"Initializing TCP connection...")
                server_running = True
                start_server_thread(self)
                self.vr_connection.configure(text="Connect Oculus Headset | Connected")
            elif self.vr_connection_flag.get() == 0:
                server_running = False
                self.vr_connection.configure(text="Connect Oculus Headset | Disconnected")
                
        self.vr_connection_flag = CTk.IntVar(value=0)
        self.vr_connection = CTk.CTkSwitch(self.home, text="Connect Oculus Headset",
                                    command=toggle_vr_connection, variable=self.vr_connection_flag,
                                    onvalue=1, offvalue=0,
                                    switch_width=48, switch_height=27)
        self.vr_connection.pack(pady=10)
            
        # Patient information entry field
        def submit(): # Implement to send messages through TCP connection for character selection
            pass 

        self.name_entry = CTk.CTkEntry(self.home, placeholder_text="Nhập tên bệnh nhân",
                                height=40, width=240, font=("Arial", 18))
        self.name_entry.pack(pady=10)

        self.age_entry = CTk.CTkEntry(self.home, placeholder_text="Nhập tuổi bệnh nhân",
                                height=40, width=240, font=("Arial", 18))
        self.age_entry.pack(pady=10)

        self.gender_options = CTk.CTkOptionMenu(self.home, values=genders)
        self.gender_options.pack(pady=10)

        self.submit_button = CTk.CTkButton(self.home, text="Submit", command=submit)
        self.submit_button.pack(side='right', anchor='center', pady=10)
        
        
        #----------------------Recording----------------------#
        
        
        
        #----------------------Settings----------------------#
        # Light and Dark Mode switch
        def switch_display_mode():
            if self.display_mode_flag.get() == 0:
                CTk.set_appearance_mode("light")
            elif self.display_mode_flag.get() == 1:
                CTk.set_appearance_mode("dark")

        self.display_mode_flag = CTk.IntVar(value=0)
        self.display_mode_switch = CTk.CTkSwitch(self.settings, text="Dark Mode", 
                                    command=switch_display_mode, variable=self.display_mode_flag, 
                                    onvalue=1, offvalue=0,
                                    switch_width=48, switch_height=27)
        self.display_mode_switch.pack(pady=20)

        
# Main loop
app = App()
app.mainloop()
