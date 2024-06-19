import customtkinter as CTk
import json
from pylsl import StreamInlet, resolve_stream
import socket
from socket import SHUT_RDWR
import threading
from enum import Enum

CTk.set_appearance_mode("light")
CTk.set_default_color_theme("green")
server_running = False

genders = ["Nam", "Nữ"]

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
        self.inlet = None #InletStream

        self.eeg_connection_flag = CTk.IntVar(value=0)

        def toggle_eeg_connection():
            if self.eeg_connection_flag.get() == 0:
                self.eeg_stream = None
                self.inlet = None
                self.eeg_connection_switch.configure(text="Connect Emotiv Headset | Disconnected")
            else:
                print("Looking for a stream...")
                self.eeg_stream = resolve_stream('type', 'EEG')
                self.inlet = StreamInlet(self.eeg_stream[0])
                print(self.inlet)
                # print(self.inlet.pull_sample())
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
        #TODO: Sesison configuration: actions per trial of sessions
        #Configuration: duration of trial, rest time between trial,

        #Run configuration stage:
        # self.recording_scheme_per_run = [   (Action.R, 2), (Action.C, 2), (Action.LH, 4),
        #                                     (Action.R, 2), (Action.C, 2), (Action.RH, 4),
        #                                     (Action.R, 2), (Action.C, 2), (Action.LF, 4),
        #                                     (Action.R, 2), (Action.C, 2), (Action.RF, 4) ]
        
        self.recording_scheme_per_run = []
        def add_action():
            action_type = None
            value = self.action_type_combo_box.get()
            duration = self.action_duration_entry.get()
            match value:
                case "Nghỉ":
                    action_type = Action.R
                case "Gợi ý":
                    action_type = Action.C
                case "Tay trái":
                    action_type = Action.LH
                case "Tay phải":
                    action_type = Action.RH
                case "Chân trái":
                    action_type = Action.LF
                case "Chân phải":
                    action_type = Action.RF
            if (duration != ""):
                action = (action_type, duration)
                self.recording_scheme_per_run.append(action)
                update_run_config() #add the last action added to the representition string
            else:
                show_error_message(self, "Thời lượng thực hiện hành động không xác định")

        def remove_action():
            if len(self.recording_scheme_per_run) != 0:
                self.recording_scheme_per_run.pop()
                update_run_config()
            else: 
                pass

        def update_run_config(): 
            cur = ""
            for action in self.recording_scheme_per_run:
                action_name = ""
                match action[0]:
                    case Action.R:
                        action_name = "Nghỉ"
                    case Action.C:
                        action_name = "Gợi "
                    case Action.LH:
                        action_name = "Tay trái"
                    case Action.RH:
                        action_name = "Tay phải"
                    case Action.LF:
                        action_name = "Chân trái"
                    case Action.RF:
                        action_name = "Chân phải"
                cur = action_name if (cur == "") else (cur + ", " + action_name)
            print(self.recording_scheme_per_run)
            self.run_config_label.configure(text=cur)
            
        
        self.action_type_combo_box = CTk.CTkComboBox(self.recording, values=["Nghỉ", "Gợi ý", "Tay trái", "Tay phải", "Chân trái", "Chân phải"])
        self.action_type_combo_box.pack(pady=10)

        self.action_duration_label = CTk.CTkLabel(self.recording, text="Thời gian (giây):")
        self.action_duration_label.pack(pady=10)
        self.action_duration_entry = CTk.CTkEntry(self.recording, placeholder_text="2",
                                height=40, width=240, font=("Arial", 18))
        self.action_duration_entry.pack(pady=10)

        self.add_action_to_run_button = CTk.CTkButton(self.recording, text="+", command=add_action, height=40, width=40)
        self.add_action_to_run_button.pack(padx=10)

        self.remove_action_to_run_button = CTk.CTkButton(self.recording, text="-", command=remove_action, height=40, width=40)
        self.remove_action_to_run_button.pack(padx=10)

        self.run_config_label = CTk.CTkLabel(self.recording, text="")
        self.run_config_label.pack(pady=10)
        #Recording stage:
        def start_recording():
            if self.eeg_connection_flag.get() == 0:
                show_error_message(self,"Không có kết nối với mũ thu EEG")
            #else: Start recording based on run config
        
        self.recording_button = CTk.CTkButton(self.recording, text="Start Recording", command=start_recording)
        self.recording_button.pack(pady=10)

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
        #----------------------Utils----------------------#
        def show_error_message(self, error_message):
            error_window = CTk.CTkToplevel(self)
            error_window.title("Error")
            error_window.geometry("300x200")

            error_label = CTk.CTkLabel(error_window, text="Error", fg_color="red")
            error_label.pack(pady=10)

            message_label = CTk.CTkLabel(error_window, text=error_message, fg_color="red")
            message_label.pack(pady=10)

            ok_button = CTk.CTkButton(error_window, text="OK", command=error_window.destroy)
            ok_button.pack(pady=10)
        Action = Enum("Action", ["R", "C", "RH", "LH", "RF", "LF"])


            

        
# Main loop
app = App()
app.mainloop()
