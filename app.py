import customtkinter as CTk
from tkinter import filedialog
import json
from pylsl import StreamInlet, resolve_stream
import socket
from socket import SHUT_RDWR
import threading
from enum import Enum
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
import ctypes

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

CTk.set_appearance_mode("light")
CTk.set_default_color_theme("green")
server_running = False
recording_in_progress = False

genders = ["Nam", "Nữ"]
Action = Enum("Action", ["R", "C", "RH", "LH", "RF", "LF"])

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
        ws = user32.GetSystemMetrics(0)
        hs = user32.GetSystemMetrics(1)
        print(ws, hs)
        print(self._get_window_scaling())
        x = int(((ws-w)/2)/self._get_window_scaling())
        y = int(((hs-h)/2)/self._get_window_scaling())
        print(w, h, x, y)
        
        # Main app configuration
        self.title("VR-BCI")
        self.resizable(False, False)
        self.geometry('%dx%d+%d+%d'% (w, h, x, y))
        self.iconbitmap("assets/icon/cat_icon.ico")
        #------------------------------------------------------#
        # Create tab view
        self.tabs = CTk.CTkTabview(self, width=1280, height=720)
        self.tabs.pack(expand=True, fill="both")

        # Create tabs
        self.home = self.tabs.add(" Trang chủ ")
        self.recording = self.tabs.add("Thu dữ liệu")
        self.training = self.tabs.add(" Luyện tập ")
        self.settings = self.tabs.add("  Cài đặt  ")
        
        #Grid configuration
        self.home.grid_columnconfigure(0, weight=2)
        self.home.grid_columnconfigure(1, weight=1)
        self.home.grid_rowconfigure(0, weight=1)
        
        self.recording.grid_columnconfigure(0, weight=1)
        self.recording.grid_columnconfigure(1, weight=1)
        self.recording.grid_columnconfigure(2, weight=1)
        self.recording.grid_rowconfigure(0, weight=1)
        
        self.training.grid_columnconfigure(0, weight=1)
        self.training.grid_rowconfigure(0, weight=1)
        
        self.settings.grid_columnconfigure(0, weight=1)
        self.settings.grid_rowconfigure(0, weight=1)
        
        #-------------------------Home--------------------------#
        #Layout
        self.home_connection_frame = CTk.CTkFrame(master=self.home, fg_color="light blue")
        self.home_connection_frame.grid_rowconfigure(0, weight=1)
        self.home_connection_frame.grid_rowconfigure(1, weight=1)
        self.home_connection_frame.grid_rowconfigure(2, weight=4)
        self.home_connection_frame.grid_columnconfigure(0, weight=1)
    
        
        self.home_patient_info_frame = CTk.CTkFrame(master=self.home, fg_color="SpringGreen2")
        self.home_patient_info_frame.grid_columnconfigure(0, weight=1)
        self.home_patient_info_frame.grid_columnconfigure(1, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(0, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(1, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(2, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(3, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(4, weight=8)
        #EEG Stream connection
        self.eeg_stream = None #LSL Stream for emotiv connection
        self.inlet = None #InletStream

        self.eeg_connection_flag = CTk.IntVar(value=0)

        self.eeg_connection_switch = CTk.CTkSwitch(self.home_connection_frame, text="Kết nối thiết bị Emotiv", font=("Arial", 18),
                                    command=self.toggle_eeg_connection, variable=self.eeg_connection_flag,
                                    onvalue=1, offvalue=0,
                                    switch_width=48, switch_height=27)
        
        #TCP to VR Connection
        self.server_thread = None
        self.vr_connection_flag = CTk.IntVar(value=0)
        self.vr_connection = CTk.CTkSwitch(self.home_connection_frame, text="Kết nối kính VR", font=("Arial", 18),
                                    command=self.toggle_vr_connection, variable=self.vr_connection_flag,
                                    onvalue=1, offvalue=0,
                                    switch_width=48, switch_height=27)

        #Patient entry field
        self.patient_image = CTk.CTkImage(light_image=Image.open("images/patient_placeholder.png"), size=(200, 200))
        self.patient_image_label = CTk.CTkLabel(self.home_patient_info_frame, image= self.patient_image, text="")
        #TODO: add choose and save image option

        self.name_entry = CTk.CTkEntry(self.home_patient_info_frame, placeholder_text="Nhập tên bệnh nhân",
                                height=40, width=240, font=("Arial", 18))

        self.age_entry = CTk.CTkEntry(self.home_patient_info_frame, placeholder_text="Nhập tuổi bệnh nhân",
                                height=40, width=240, font=("Arial", 18))

        self.gender_options = CTk.CTkOptionMenu(self.home_patient_info_frame, values=genders, font=("Arial", 18))

        self.submit_button = CTk.CTkButton(self.home_patient_info_frame, text="Gửi", font=("Arial", 18), command=self.submit)
        
        self.home_connection_frame.grid(row=0, column=0,rowspan=5, sticky="nsew")
        self.eeg_connection_switch.grid(row=0, column=0, columnspan=1)
        self.vr_connection.grid(row=1, column=0, columnspan=1)
        
        self.home_patient_info_frame.grid(row=0, column=1, rowspan=5, sticky="nsew")
        self.patient_image_label.grid(row=0, column=0, rowspan=4, sticky="e")
        self.name_entry.grid(row=0, column=1, columnspan=1)
        self.age_entry.grid(row=1, column=1, columnspan=1)
        self.gender_options.grid(row=2, column=1, columnspan=1)
        self.submit_button.grid(row=3, column=1, columnspan=1)

        #----------------------Recording----------------------#
        #Layout
        self.recording_duration_config_frame = CTk.CTkFrame(master=self.recording, fg_color="light blue")
        self.recording_duration_config_frame.grid_columnconfigure(0, weight=3)
        self.recording_duration_config_frame.grid_columnconfigure(1, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(0, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(1, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(2, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(3, weight=6)
        
        self.recording_scheme_config_frame = CTk.CTkFrame(master=self.recording, fg_color="aquamarine")
        self.recording_scheme_config_frame.grid_columnconfigure(0, weight=1)
        self.recording_scheme_config_frame.grid_columnconfigure(1, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(0, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(1, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(2, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(3, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(4, weight=4)
        
        self.recording_operation_frame = CTk.CTkFrame(master=self.recording, fg_color="khaki")
        self.recording_operation_frame.grid_columnconfigure(0, weight=1)
        self.recording_operation_frame.grid_columnconfigure(1, weight=1)
        self.recording_operation_frame.grid_rowconfigure(0, weight=1)
        self.recording_operation_frame.grid_rowconfigure(1, weight=1)
        self.recording_operation_frame.grid_rowconfigure(2, weight=1)
        self.recording_operation_frame.grid_rowconfigure(3, weight=3)
        
        #Run configuration stage:
        self.recording_scheme_per_run = []

        self.rest_duration_label = CTk.CTkLabel(self.recording_duration_config_frame, text="Thời gian nghỉ (giây):", wraplength=200,font=("Arial", 18))
        self.rest_duration_entry = CTk.CTkEntry(self.recording_duration_config_frame, placeholder_text="2", height=40, font=("Arial", 18))
        
        self.cue_duration_label = CTk.CTkLabel(self.recording_duration_config_frame, text="Thời gian gợi ý (giây):", wraplength=200, font=("Arial", 18))
        self.cue_duration_entry = CTk.CTkEntry(self.recording_duration_config_frame, placeholder_text="2", height=40, font=("Arial", 18))
        
        self.action_duration_label = CTk.CTkLabel(self.recording_duration_config_frame, text="Thời gian thực hiện (giây):", wraplength=250, font=("Arial", 18))
        self.action_duration_entry = CTk.CTkEntry(self.recording_duration_config_frame, placeholder_text="2", height=40, font=("Arial", 18))
        
        self.action_type_label = CTk.CTkLabel(self.recording_scheme_config_frame, text="Hành động tiếp theo:", wraplength=180, font=("Arial", 18))
        self.action_type_combo_box = CTk.CTkComboBox(self.recording_scheme_config_frame, values=["Nghỉ", "Gợi ý", "Tay trái", "Tay phải", "Chân trái", "Chân phải"],font=("Arial", 18), width=100)
        self.add_action_to_run_button = CTk.CTkButton(self.recording_scheme_config_frame, text="Thêm",font=("Arial", 18),  command=self.add_action, height=40, width=100)
        self.remove_action_to_run_button = CTk.CTkButton(self.recording_scheme_config_frame, text="Bớt",font=("Arial", 18),  command=self.remove_action, height=40, width=100)
        
        self.run_config_label = CTk.CTkLabel(self.recording_scheme_config_frame, text="", font=("Arial", 18))
        self.repeated_runs_label = CTk.CTkLabel(self.recording_scheme_config_frame, text="Số lần lặp lại kịch bản:", wraplength=180, font=("Arial", 18))
        self.repeated_runs_entry = CTk.CTkEntry(self.recording_scheme_config_frame, placeholder_text="1", height=40, font=("Arial", 18))
        
        #Recording stage:
        self.sampling_frequency = 128
        
        self.eeg_thread = None

        self.trial_button = CTk.CTkButton(self.recording_operation_frame, text="Thu thử",font=("Arial", 18), command=lambda: self.init_cue_window(), height=40, width=100)
        self.recording_button = CTk.CTkButton(self.recording_operation_frame, text="Bắt đầu thu",font=("Arial", 18), command=self.start_recording, height=40, width=100)

        self.stop_recording_button = CTk.CTkButton(self.recording_operation_frame, text="Dừng thu",font=("Arial", 18), command=self.stop_recording, height=40, width=100)
        
        self.recording_progress_label = CTk.CTkLabel(self.recording_operation_frame, text="", font=("Arial", 18))
        
        self.recording_duration_config_frame.grid(row=0, column=0, sticky="nsew")
        self.rest_duration_label.grid(row=0, column=0, columnspan=1, sticky="nsew")
        self.rest_duration_entry.grid(row=0, column=1, columnspan=1)
        self.cue_duration_label.grid(row=1, column=0, columnspan=1, sticky="nsew")
        self.cue_duration_entry.grid(row=1, column=1, columnspan=1)
        self.action_duration_label.grid(row=2, column=0, columnspan=1, sticky="nsew")
        self.action_duration_entry.grid(row=2, column=1, columnspan=1)
        
        self.recording_scheme_config_frame.grid(row=0, column=1, sticky="nsew")
        self.action_type_label.grid(row=0, column=0, columnspan=1)
        self.action_type_combo_box.grid(row=0, column=1, columnspan=1)
        self.add_action_to_run_button.grid(row=1, column=0, columnspan=1)
        self.remove_action_to_run_button.grid(row=1, column=1, columnspan=1)
        self.run_config_label.grid(row=2, column=0, columnspan=2)
        self.repeated_runs_label.grid(row=3, column=0, columnspan=1, sticky="nsew")
        self.repeated_runs_entry.grid(row=3, column=1, columnspan=1)
    
        self.recording_operation_frame.grid(row=0, column=2, sticky="nsew")
        self.trial_button.grid(row=0, column=0, columnspan=2)
        self.recording_button.grid(row=1, column=0, columnspan=1, padx=10)
        self.stop_recording_button.grid(row=1, column=1, columnspan=1, padx=10)
        self.recording_progress_label.grid(row=2, column=0, columnspan=2)
        # add_border(self.recording, 3, 8)

        #---------------------Cue Window---------------------#
        self.cue_window = None

        #---------------------Settings---------------------#
        self.display_mode_flag = CTk.IntVar(value=0)
        self.display_mode_switch = CTk.CTkSwitch(self.settings, text="Chế độ tối", font=("Arial", 18), 
                                    command=self.switch_display_mode, variable=self.display_mode_flag, 
                                    onvalue=1, offvalue=0,
                                    switch_width=48, switch_height=27)
        self.display_mode_switch.grid(row=0, column=0, sticky="n")
        
    def toggle_eeg_connection(self):
        if self.eeg_connection_flag.get() == 0:
            self.eeg_stream = None
            self.inlet = None
            self.eeg_connection_switch.configure(text="Kết nối thiết bị Emotiv | Ngắt kết nối", font=("Arial", 18))
        else:
            print("Looking for a stream...")
            self.eeg_stream = resolve_stream('type', 'EEG')
            self.inlet = StreamInlet(self.eeg_stream[0], max_buflen=1)
            print(self.inlet)
            # print(self.inlet.pull_sample())
            self.eeg_connection_switch.configure(text="Kết nối thiết bị Emotiv | Đã kết nối", font=("Arial", 18))
          
    def handle_client_connection(client_socket): #demo for connection  via app, need button interface and message queue
        while True:
            try:
                client_socket.send(bytes(input(), 'utf-8')) 
            except ConnectionResetError:
                break
        client_socket.close()
        
    def start_server(self):
        global server_running
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Server started and listening on port {PORT}")
        while server_running:
            client_socket, addr = server_socket.accept()
            print(f"Connected from {addr}")
            client_handler = threading.Thread(target=self.handle_client_connection, args=(client_socket,))
            client_handler.start()
        server_socket.close()
            
    def start_server_thread(self):
        if self.server_thread is None or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(target=self.start_server, daemon=True)
            self.server_thread.start()
        
    def toggle_vr_connection(self):
        global server_running
        if self.vr_connection_flag.get() == 1:
            print(f"Initializing TCP connection...")
            server_running = True
            self.start_server_thread()
            self.vr_connection.configure(text="Kết nối kính VR | Đã kết nối", font=("Arial", 18))
        elif self.vr_connection_flag.get() == 0:
            server_running = False
            self.vr_connection.configure(text="Kết nối kính VR | Đã ngắt kết nối", font=("Arial", 18))
                            
    # Patient information entry field
    def submit(self): # Implement to send messages through TCP connection for character selection
        pass 
        
        # add_border(self.home, 2, 6)

    def add_action(self):
        action_type = None
        value = self.action_type_combo_box.get()
        match value:
            case "Nghỉ":
                action_type = Action.R
                duration = int(self.rest_duration_entry.get())
            case "Gợi ý":
                action_type = Action.C
                duration = int(self.cue_duration_entry.get())
            case "Tay trái":
                action_type = Action.LH
                duration = int(self.action_duration_entry.get())
            case "Tay phải":
                action_type = Action.RH
                duration = int(self.action_duration_entry.get())
            case "Chân trái":
                action_type = Action.LF
                duration = int(self.action_duration_entry.get())
            case "Chân phải":
                action_type = Action.RF
                duration = int(self.action_duration_entry.get())
        if (duration != ""):
            action = (action_type, duration)
            self.recording_scheme_per_run.append(action)
            self.update_run_config() #add the last action added to the representition string
        else:
            self.show_error_message(self, "Thời lượng thực hiện hành động không xác định")
                         
    def remove_action(self):
        if len(self.recording_scheme_per_run) != 0:
            self.recording_scheme_per_run.pop()
            self.update_run_config()
        else: 
            pass

    def update_run_config(self): 
        cur = ""
        for action in self.recording_scheme_per_run:
            action_name = ""
            match action[0]:
                case Action.R:
                    action_name = "Nghỉ"
                case Action.C:
                    action_name = "Gợi ý"
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
        self.run_config_label.configure(text=cur, font=("Arial", 18))
        # generate_label_file()
            
    def generate_setting_file(self):
        setting = {
            "labels":{
                "Rest": int(self.rest_duration_entry.get()),
                "Cue":  int(self.cue_duration_entry.get()),
                "Action.RH": int(self.action_duration_entry.get()),
                "Action.LH": int(self.action_duration_entry.get()),
                "Action.RF": int(self.action_duration_entry.get()),
                "Action.LF": int(self.action_duration_entry.get()),
            },
            "num_of_runs": int(self.repeated_runs_entry.get())           
        }
        with open("data" + f"/{self.get_file_path('json')}", "w") as file:
            json.dump(setting, file)
                        
    def generate_label_file(self): #Call when recording is finished
        with open("data" + f"/{self.get_file_path('txt')}", "w") as file:
            for i in range(0, int(self.repeated_runs_entry.get())):
                for action in self.recording_scheme_per_run:
                    file.write(f"{action[0].value}")
                        
    def generate_data_file(self, data):
        data = np.array(data)
        df = pd.DataFrame(data)
        df.to_csv("data" + f"/{self.get_file_path('csv')}", index = False)
            
    def pull_eeg_data(self):
        for i in range(0, int(self.repeated_runs_entry.get())):
            global recording_in_progress
            cur_action_index = 0
            sample_count = 0
            data = []
            while recording_in_progress and cur_action_index < len(self.recording_scheme_per_run):
                sample, timestamp = self.inlet.pull_sample(timeout=0.0)
                # print("Current action index: " + str(cur_action_index))
                if timestamp != None: #Depends on the mapping of electrodes on the EEG devices
                    # values = [  sample[3],  sample[4], 
                    #             sample[5],  sample[14], 
                    #             sample[15], sample[16], 
                    #             sample[6],  sample[7], 
                    #             sample[8],  sample[9],
                    #             sample[17], sample[18], 
                    #             sample[19], sample[10], 
                    #             sample[11], sample[22], 
                    #             sample[21], sample[20],
                    #             sample[12], sample[13],
                    #             sample[23], sample[24]] 
                    data.append(sample[3:(len(sample)-1)])
                    sample_count += 1
                    print(timestamp)

                if sample_count == self.recording_scheme_per_run[cur_action_index][1] * self.sampling_frequency: #All samples of an action recorded
                    sample_count = 0
                    cur_action_index = cur_action_index + 1
        recording_in_progress = False
        self.generate_label_file()
        self.generate_data_file(data)
        self.generate_setting_file()
        self.recording_progress_label.configure(text="Hoàn thành thu dữ liệu")

    def start_eeg_thread(self):
        if self.eeg_thread is None or not self.eeg_thread.is_alive():
            self.eeg_thread = threading.Thread(target=self.pull_eeg_data, daemon=True)
            self.eeg_thread.start()
                
    def start_recording(self):
        global recording_in_progress
        if self.eeg_connection_flag.get() == 0:
            self.show_error_message(self,"Không có kết nối với mũ thu EEG")
        else:
            recording_in_progress = True
            self.start_eeg_thread()
            # init_cue_window(self)
            self.recording_progress_label.configure(text="Đang thu dữ liệu...", font=("Arial", 18))
            
    def stop_recording(self):
        global recording_in_progress
        recording_in_progress = False

    #----------------------Settings----------------------#
    # Light and Dark Mode switch
    def switch_display_mode(self):
        if self.display_mode_flag.get() == 0:
            CTk.set_appearance_mode("light")
        elif self.display_mode_flag.get() == 1:
            CTk.set_appearance_mode("dark")

    #----------------------Utils----------------------#
    def show_error_message(self, error_message):
        error_window = CTk.CTkToplevel(self)
        error_window.title("Error")
        error_window.geometry("300x200")

        error_label = CTk.CTkLabel(error_window, text="Lỗi", font=("Arial", 18), fg_color="red")

        message_label = CTk.CTkLabel(error_window, text=error_message,font=("Arial", 18),  fg_color="red")

        ok_button = CTk.CTkButton(error_window, text="OK", font=("Arial", 18), command=error_window.destroy)
        
        error_label.grid(row=1,column=1, columnspan=2)
        message_label.grid(row=2, column=1, columnspan=2)
        ok_button.grid(row=3, column=1, columnspan=2)
        
        # def get_data_folder_path(): #TODO: allow users to pick data folder
        #     folder_selected = filedialog.askdirectory()
        #     if folder_selected:
        #         return f"{folder_selected}"
        
    def get_file_path(self, file_type): #TODO: get the folder directory that the user chooses
        if self.name_entry.get() != "": 
            file_path = self.name_entry.get() + "_" + datetime.now().strftime("%d_%B_%Y_%H_%M_%S") + "." + file_type
            return file_path
        else:
            self.show_error_message(self, "Chưa có tên đối tượng thu dữ liệu")
        
    def init_cue_window(self):
            window = CTk.CTkToplevel(self)
            window.title("Gợi ý")
            window.geometry("300x200")
            if (len(self.recording_scheme_per_run) == 0):
                self.show_error_message(self, error_message="Hãy nhập kịch bản thu")
            else:    
                self.cue_window = CueWindow(window, self.recording_scheme_per_run, int(self.repeated_runs_entry.get()))
                
                self.cue_window.root = window
                if self.cue_window.timerFlag == False:
                    self.cue_window.label.pack(pady=20)
                    self.cue_window.image.pack(pady=20)
                    self.cue_window.timerFlag = True
                    self.cue_window.set(self.recording_scheme_per_run[0][1])
                    # self.cue_window.set(3)
                    # self.cue_window.update()
                    
            
# def add_border(root, nums_of_cols, nums_of_rows):
#             for col in range(0, nums_of_cols):
#                 border = CTk.CTkFrame(root, width=2, bg_color="blue")
#                 border.grid(row=0, column=col, rowspan=nums_of_rows, sticky="ns", padx=(0, 10))
       
class CueWindow:
    def __init__(self, root, recording_scheme, nums_of_runs) -> None:
        self.root = root 
        self.recording_scheme=[]
        for i in range(0, nums_of_runs):
            self.recording_scheme += recording_scheme
        
        print(self.recording_scheme)
        # Initiallize timer variables
        self.seconds = 0
        self.timerFlag = False
        self.cueFlag = False
        self.counter = 0

        self.total_nums_of_actions = len(self.recording_scheme)
      
        # Create a countdown clock to display the timer
        self.label = CTk.CTkLabel(self.root, text = '00:00', font=("Helvetica", 48))
        
        # load cue images
        self.images = [CTk.CTkImage(light_image=Image.open("images/arrow_left_foot.png"),  size=(100, 100)), 
                       CTk.CTkImage(light_image=Image.open("images/arrow_right_foot.png"), size=(100, 100)), 
                       CTk.CTkImage(light_image=Image.open("images/arrow_left_hand.png"),  size=(100, 100)), 
                       CTk.CTkImage(light_image=Image.open("images/arrow_right_hand.png"), size=(100, 100))]
        self.image = CTk.CTkLabel(self.root, image=None, text="")
        # Update the timer display
        self.update()
        pass

    def stop(self):
        self.counter = 0
        self.timerFlag = 0 #stop timer
        self.root.destroy()  
        pass

    def calculate(self):
        minutes = self.seconds // 60
        seconds = self.seconds % 60
        time_str = f"{minutes:02}:{seconds:02}"
        print(time_str)
        return time_str

    def update(self):
        if self.timerFlag:
            time_str = self.calculate()
            self.label.configure(text=time_str)
            if self.cueFlag: #Current view is cue
                self.image.pack()
                if self.seconds != 0:
                    self.seconds -= 1
                else:
                    print("Current action: " + str(self.recording_scheme[self.counter][0]))
                    self.counter += 1
                    if self.counter != self.total_nums_of_actions: 

                        self.set(self.recording_scheme[self.counter][1])
                        self.image.pack_forget()
                        print("Next action:"+ str(self.recording_scheme[self.counter][0]))
                        self.cueFlag = False
                    else: #end of scheme
                       
                        self.stop()
                        pass   
            else: #Current view is rest or action
                    if self.seconds != 0:
                        self.seconds -= 1
                    else:
                        print("Current action: " + str(self.recording_scheme[self.counter][0]))
                        self.counter += 1
                        if self.counter != self.total_nums_of_actions:
                            print("Next action:"+ str(self.recording_scheme[self.counter][0]))
                            self.set(self.recording_scheme[self.counter][1]) # next segment
                            print(self.recording_scheme[self.counter][0])
                        
                            if self.recording_scheme[self.counter][0] == Action.C: #next segment is C
                                self.getCueImage(self.recording_scheme[self.counter+1][0]) #get cue image based on next action
                                self.cueFlag = True
                        else: #end of scheme
                            self.stop()
                            pass
        self.root.after(1000, self.update) # Update timer after 1s
        
    def getCueImage(self, actionType):
        print("Getting image...")
        if actionType == Action.LF:
            self.image.configure(image=self.images[0])
        
        if actionType == Action.RF:
            self.image.configure(image=self.images[1])
        
        if actionType == Action.LH:
            self.image.configure(image=self.images[2])
        
        if actionType == Action.RH:
            self.image.configure(image=self.images[3])
        
        self.image.configure(image=None)
        
    def set(self, amount):
        self.seconds = amount


# Main loop
app = App()
app.mainloop()
