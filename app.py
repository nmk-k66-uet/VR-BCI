import os
import customtkinter as CTk
import tkinter
import json
from pylsl import StreamInlet, resolve_stream
import socket
from socket import SHUT_RDWR
import threading
from enum import Enum
import numpy as np
import pandas as pd
from datetime import datetime
import time
from PIL import Image
import ctypes
from playsound import playsound

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

CTk.set_appearance_mode("light")
CTk.set_default_color_theme("green")
server_running = False
recording_in_progress = False

genders = ["Nam", "Nữ"]
# Actions include: Rest, Cue, Right Hand, Left Hand, Right Feet, Left Feet,
# Pupil to Left, Pupil to Right, Blink, Open/Close Mouth, Nod head, Shake head,
# Left Hand Open/Close, Right Hand Open/Close, Tongue, Add, Multiply
Action = Enum("Action", ["R", "C", "RH", "LH", "RF",
              "LF", "PTL", "PTR", "B", "OCM", "NH", "SH", "LHOC", "RHOC", "T", "A", "M"])

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
        # print(ws, hs)
        # print(self._get_window_scaling())
        x = int(((ws-w)/2)/self._get_window_scaling())
        y = int(((hs-h)/2)/self._get_window_scaling())
        # print(w, h, x, y)

        # Main app configuration
        self.title("VR-BCI")
        self.resizable(False, False)
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.iconbitmap("assets/icon/cat_icon.ico")
        # ------------------------------------------------------#
        # Create tab view
        self.tabs = CTk.CTkTabview(self, width=w, height=h)
        self.tabs.pack(expand=True, fill="both")

        # Create tabs
        self.home = self.tabs.add(" Trang chủ ")
        self.recording = self.tabs.add("Thu dữ liệu")
        self.training = self.tabs.add(" Luyện tập ")
        self.settings = self.tabs.add("  Cài đặt  ")

        self.tabs._segmented_button._buttons_dict[" Trang chủ "].configure(
            font=("Arial", 24))
        self.tabs._segmented_button._buttons_dict["Thu dữ liệu"].configure(
            font=("Arial", 24))
        self.tabs._segmented_button._buttons_dict[" Luyện tập "].configure(
            font=("Arial", 24))
        self.tabs._segmented_button._buttons_dict["  Cài đặt  "].configure(
            font=("Arial", 24))
        # Grid configuration
        self.home.grid_columnconfigure(0, weight=2)
        self.home.grid_columnconfigure(1, weight=1)
        self.home.grid_rowconfigure(0, weight=1)

        self.recording.grid_columnconfigure(0, weight=1)
        self.recording.grid_columnconfigure(1, weight=2)
        self.recording.grid_columnconfigure(2, weight=2)
        self.recording.grid_columnconfigure(2, weight=2)
        self.recording.grid_rowconfigure(0, weight=1)

        self.training.grid_columnconfigure(0, weight=1)
        self.training.grid_rowconfigure(0, weight=1)

        self.settings.grid_columnconfigure(0, weight=1)
        self.settings.grid_rowconfigure(0, weight=1)

        # -------------------------Home--------------------------#
        # Layout
        self.home_connection_frame = CTk.CTkFrame(
            master=self.home, fg_color="light blue")
        self.home_connection_frame_label = CTk.CTkLabel(
            master=self.home_connection_frame,  text="Thiết lập kết nối", font=("Arial", 24))
        self.home_connection_frame.grid_rowconfigure(0, weight=1)
        self.home_connection_frame.grid_rowconfigure(1, weight=1)
        self.home_connection_frame.grid_rowconfigure(2, weight=1)
        self.home_connection_frame.grid_rowconfigure(3, weight=4)
        self.home_connection_frame.grid_columnconfigure(0, weight=1)

        self.home_info_frame = CTk.CTkFrame(
            master=self.home, fg_color="SpringGreen2")

        self.home_patient_info_frame = CTk.CTkFrame(
            master=self.home_info_frame, fg_color="SpringGreen2"
        )
        self.home_patient_info_frame_label = CTk.CTkLabel(
            master=self.home_patient_info_frame,
            text="Thông tin bệnh nhân",
            font=("Arial", 24))

        self.home_recorder_info_frame = CTk.CTkFrame(
            master=self.home_info_frame, fg_color="SpringGreen2"
        )
        self.home_recorder_info_frame_label = CTk.CTkLabel(
            master=self.home_recorder_info_frame,
            text="Thông tin bên thu",
            font=("Arial", 24))

        self.home_info_frame.grid_columnconfigure(0, weight=1)
        self.home_info_frame.grid_rowconfigure(0, weight=1)
        self.home_info_frame.grid_rowconfigure(1, weight=1)

        self.home_patient_info_frame.grid_columnconfigure(0, weight=1)
        self.home_patient_info_frame.grid_columnconfigure(1, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(0, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(1, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(2, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(3, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(4, weight=1)
        self.home_patient_info_frame.grid_rowconfigure(5, weight=1)

        self.home_recorder_info_frame.grid_columnconfigure(0, weight=1)
        self.home_recorder_info_frame.grid_rowconfigure(0, weight=1)
        self.home_recorder_info_frame.grid_rowconfigure(1, weight=2)
        self.home_recorder_info_frame.grid_rowconfigure(2, weight=2)

        # EEG Stream connection
        self.eeg_stream = None  # LSL Stream for emotiv connection
        self.inlet = None  # InletStream

        self.eeg_connection_flag = CTk.IntVar(value=0)
        self.eeg_connection_switch = CTk.CTkSwitch(self.home_connection_frame, text="Kết nối thiết bị Emotiv", font=("Arial", 18),
                                                   command=self.toggle_eeg_connection, variable=self.eeg_connection_flag,
                                                   onvalue=1, offvalue=0,
                                                   switch_width=48, switch_height=27)

        # TCP to VR Connection
        self.server_thread = None
        self.vr_connection_flag = CTk.IntVar(value=0)
        self.vr_connection = CTk.CTkSwitch(self.home_connection_frame, text="Kết nối kính VR", font=("Arial", 18),
                                           command=self.toggle_vr_connection, variable=self.vr_connection_flag,
                                           onvalue=1, offvalue=0,
                                           switch_width=48, switch_height=27)

        # Patient entry field
        self.patient_image = CTk.CTkImage(light_image=Image.open(
            "assets/images/patient_placeholder.png"), size=(200, 200))
        self.patient_image_label = CTk.CTkLabel(
            self.home_patient_info_frame, image=self.patient_image, text="")
        # TODO: add choose and save image option

        self.name_entry = CTk.CTkEntry(self.home_patient_info_frame, placeholder_text="Nhập tên bệnh nhân",
                                       height=40, width=240, font=("Arial", 18))

        self.age_entry = CTk.CTkEntry(self.home_patient_info_frame, placeholder_text="Nhập tuổi bệnh nhân",
                                      height=40, width=240, font=("Arial", 18))

        self.location_entry = CTk.CTkEntry(self.home_patient_info_frame, placeholder_text="Nhập tỉnh thành bệnh nhân sinh sống",
                                           height=40, width=240, font=("Arial", 18))

        self.gender_options = CTk.CTkOptionMenu(
            self.home_patient_info_frame, values=genders, font=("Arial", 18))

        self.submit_button = CTk.CTkButton(
            self.home_patient_info_frame, text="Gửi", font=("Arial", 18), command=self.submit)

        # Recorder entry field
        self.recording_facility_name_entry = CTk.CTkEntry(self.home_recorder_info_frame, placeholder_text="Nhập tên đơn vị thu",
                                                          height=40, width=240, font=("Arial", 18))
        self.recording_device_name_entry = CTk.CTkEntry(self.home_recorder_info_frame, placeholder_text="Nhập tên thiết bị thu",
                                                        height=40, width=240, font=("Arial", 18))
        # Widget layout assignment
        self.home_connection_frame.grid(
            row=0, column=0, rowspan=5, sticky="nsew")
        self.home_connection_frame_label.grid(
            row=0, column=0, columnspan=1, sticky="n", pady=(30, 0))
        self.eeg_connection_switch.grid(row=1, column=0, columnspan=1)
        self.vr_connection.grid(row=2, column=0, columnspan=1)

        self.home_info_frame.grid(
            row=0, column=1, sticky="nsew")
        self.home_patient_info_frame.grid(row=0, column=0, sticky="nsew")
        self.home_recorder_info_frame.grid(row=1, column=0, sticky="nsew")

        self.home_patient_info_frame_label.grid(
            row=0, column=0, columnspan=2, sticky="n", pady=(30, 0))
        self.patient_image_label.grid(row=1, column=0, rowspan=4, sticky="e")
        self.name_entry.grid(row=1, column=1, columnspan=1)
        self.age_entry.grid(row=2, column=1, columnspan=1)
        self.location_entry.grid(row=3, column=1, columnspan=1)
        self.gender_options.grid(row=4, column=1, columnspan=1)
        self.submit_button.grid(row=5, column=1, columnspan=1)

        self.home_recorder_info_frame_label.grid(
            row=0, column=0, sticky="n", pady=(30, 0))
        self.recording_facility_name_entry.grid(row=1, column=0, sticky="n")
        self.recording_device_name_entry.grid(row=2, column=0, sticky="n")

        # ----------------------Recording----------------------#
        # Layout
        self.recording_setting_frame = CTk.CTkFrame(
            master=self.recording, fg_color="azure")
        self.recording_setting_frame_label = CTk.CTkLabel(
            master=self.recording_setting_frame, text="Cài đặt phiên thu", font=("Arial", 24))
        self.current_recording_setting = CTk.StringVar(value="Custom")
        self.recording_setting_frame.grid_columnconfigure(0, weight=1)
        self.recording_setting_frame.grid_rowconfigure(0, weight=1)
        self.recording_setting_frame.grid_rowconfigure(1, weight=1)
        self.recording_setting_frame.grid_rowconfigure(2, weight=1)
        self.recording_setting_frame.grid_rowconfigure(3, weight=1)
        self.recording_setting_frame.grid_rowconfigure(4, weight=4)

        self.recording_duration_config_frame = CTk.CTkFrame(
            master=self.recording, fg_color="light blue")
        self.recording_duration_config_frame_label = CTk.CTkLabel(
            master=self.recording_duration_config_frame, text="Thiết lập thời gian", font=("Arial", 24))
        self.recording_duration_config_frame.grid_columnconfigure(0, weight=3)
        self.recording_duration_config_frame.grid_columnconfigure(1, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(0, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(1, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(2, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(3, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(4, weight=1)
        self.recording_duration_config_frame.grid_rowconfigure(5, weight=5)

        self.recording_scheme_config_frame = CTk.CTkFrame(
            master=self.recording, fg_color="aquamarine")
        self.recording_scheme_config_frame_label = CTk.CTkLabel(
            master=self.recording_scheme_config_frame, text="Thiết lập kịch bản", font=("Arial", 24))
        self.recording_scheme_config_frame.grid_columnconfigure(0, weight=1)
        self.recording_scheme_config_frame.grid_columnconfigure(1, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(0, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(1, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(2, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(3, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(4, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(5, weight=1)
        self.recording_scheme_config_frame.grid_rowconfigure(6, weight=4)

        self.recording_operation_frame = CTk.CTkFrame(
            master=self.recording, fg_color="khaki")
        self.recording_operation_frame_label = CTk.CTkLabel(
            master=self.recording_operation_frame, text="Thu dữ liệu", font=("Arial", 24))
        self.recording_operation_frame.grid_columnconfigure(0, weight=1)
        self.recording_operation_frame.grid_columnconfigure(1, weight=1)
        self.recording_operation_frame.grid_rowconfigure(0, weight=1)
        self.recording_operation_frame.grid_rowconfigure(1, weight=1)
        self.recording_operation_frame.grid_rowconfigure(2, weight=1)
        self.recording_operation_frame.grid_rowconfigure(3, weight=1)
        self.recording_operation_frame.grid_rowconfigure(4, weight=6)

        # Run configuration stage:
        self.calibration_scheme = []
        self.recording_scheme_per_run = []
        self.recording_setting_pointer_option = CTk.CTkRadioButton(
            master=self.recording_setting_frame, text="Bài thu con trỏ", font=("Arial", 18),
            command=self.get_setting, variable=self.current_recording_setting, value="Pointer"
        )
        self.recording_setting_character_option = CTk.CTkRadioButton(
            master=self.recording_setting_frame, text="Bài thu kí tự", font=("Arial", 18),
            command=self.get_setting, variable=self.current_recording_setting, value="Character"
        )
        self.recording_setting_custom_option = CTk.CTkRadioButton(
            master=self.recording_setting_frame, text="Tùy chỉnh bài thu", font=("Arial", 18),
            command=self.get_setting, variable=self.current_recording_setting, value="Custom"
        )

        self.rest_duration_label = CTk.CTkLabel(
            self.recording_duration_config_frame, text="Thời gian nghỉ (giây):", wraplength=200, font=("Arial", 18))
        self.rest_duration_entry = CTk.CTkEntry(
            self.recording_duration_config_frame, placeholder_text="2", height=40, font=("Arial", 18))
        self.rest_duration = 0

        self.cue_duration_label = CTk.CTkLabel(
            self.recording_duration_config_frame, text="Thời gian gợi ý (giây):", wraplength=200, font=("Arial", 18))
        self.cue_duration_entry = CTk.CTkEntry(
            self.recording_duration_config_frame, placeholder_text="2", height=40, font=("Arial", 18))
        self.cue_duration = 0

        self.action_duration_label = CTk.CTkLabel(
            self.recording_duration_config_frame, text="Thời gian thực hiện (giây):", wraplength=250, font=("Arial", 18))
        self.action_duration_entry = CTk.CTkEntry(
            self.recording_duration_config_frame, placeholder_text="2", height=40, font=("Arial", 18))
        self.action_duration = 0

        self.calibration_duration_label = CTk.CTkLabel(
            self.recording_duration_config_frame, text="Thời gian căn chỉnh (giây):", wraplength=250, font=("Arial", 18))
        self.calibration_duration_entry = CTk.CTkEntry(
            self.recording_duration_config_frame, placeholder_text="2", height=40, font=("Arial", 18))
        self.calibration_duration = 0

        self.action_type_label = CTk.CTkLabel(
            self.recording_scheme_config_frame, text="Hành động tiếp theo:", wraplength=180, font=("Arial", 18))
        self.action_type_combo_box = CTk.CTkComboBox(self.recording_scheme_config_frame, values=[
                                                     "Nghỉ", "Gợi ý", "Tay trái", "Tay phải", "Chân trái", "Chân phải",
                                                     "Nhìn trái", "Nhìn phải", "Nháy mắt", "Đóng/Mở miệng",
                                                     "Gật đầu", "Lắc đầu", "Nắm/Mở tay trái", "Nắm/Mở tay phải", "Lưỡi", "Cộng", "Nhân"], font=("Arial", 18), width=100)

        self.calibration_flag = CTk.StringVar(value="no")
        self.calibrate_label = CTk.CTkLabel(
            self.recording_scheme_config_frame, text="Căn chỉnh:", wraplength=180, font=("Arial", 18))
        self.calibrate_check_box = CTk.CTkCheckBox(self.recording_scheme_config_frame, text="",
                                                   command=self.add_calibration, variable=self.calibration_flag, onvalue="yes", offvalue="no")

        self.add_action_to_run_button = CTk.CTkButton(self.recording_scheme_config_frame, text="Thêm", font=(
            "Arial", 18),  command=self.add_action, height=40, width=100)
        self.remove_action_to_run_button = CTk.CTkButton(self.recording_scheme_config_frame, text="Bớt", font=(
            "Arial", 18),  command=self.remove_action, height=40, width=100)

        self.scheme_config_text = tkinter.Text(
            self.recording_scheme_config_frame, font=("Arial", 10), height=5, width=10)
        
        self.scheme_config_scrollbar = CTk.CTkScrollbar(
            self.recording_scheme_config_frame, command=self.scheme_config_text.yview
        )
        self.scheme_config_text.configure(yscrollcommand=self.scheme_config_scrollbar.set)
        
        self.repeated_runs_label = CTk.CTkLabel(
            self.recording_scheme_config_frame, text="Số lần lặp lại kịch bản:", wraplength=180, font=("Arial", 18))
        self.repeated_runs_entry = CTk.CTkEntry(
            self.recording_scheme_config_frame, placeholder_text="1", height=40, font=("Arial", 18))
        self.repeated_runs = 0
        # Recording stage:
        self.sampling_frequency = 128

        self.eeg_thread = None

        self.trial_button = CTk.CTkButton(self.recording_operation_frame, text="Thu thử", font=(
            "Arial", 18), command=lambda: self.init_cue_window(), height=40, width=100)
        self.recording_button = CTk.CTkButton(self.recording_operation_frame, text="Bắt đầu thu", font=(
            "Arial", 18), command=self.start_recording, height=40, width=100)

        self.stop_recording_button = CTk.CTkButton(self.recording_operation_frame, text="Dừng thu", font=(
            "Arial", 18), command=self.stop_recording, height=40, width=100)

        self.recording_progress_label = CTk.CTkLabel(
            self.recording_operation_frame, text="", font=("Arial", 18))

        # Widget layout assignment
        self.recording_setting_frame.grid(
            row=0, column=0, sticky="nsew"
        )
        self.recording_setting_frame_label.grid(row=0, column=0)
        self.recording_setting_pointer_option.grid(
            row=1, column=0, sticky="w", padx=(20, 0))
        self.recording_setting_character_option.grid(
            row=2, column=0, sticky="w", padx=(20, 0))
        self.recording_setting_custom_option.grid(
            row=3, column=0, sticky="w", padx=(20, 0))

        self.recording_duration_config_frame.grid(
            row=0, column=1, sticky="nsew")
        self.recording_duration_config_frame_label.grid(
            row=0, column=0, columnspan=2, sticky="n", pady=(30, 0))
        self.rest_duration_label.grid(
            row=1, column=0, columnspan=1, sticky="nsew")
        self.rest_duration_entry.grid(row=1, column=1, columnspan=1)
        self.cue_duration_label.grid(
            row=2, column=0, columnspan=1, sticky="nsew")
        self.cue_duration_entry.grid(row=2, column=1, columnspan=1)
        self.action_duration_label.grid(
            row=3, column=0, columnspan=1, sticky="nsew")
        self.action_duration_entry.grid(row=3, column=1, columnspan=1)
        self.calibration_duration_label.grid(
            row=4, column=0, columnspan=1, sticky="nsew")
        self.calibration_duration_entry.grid(row=4, column=1, columnspan=1)

        self.recording_scheme_config_frame.grid(
            row=0, column=2, sticky="nsew")
        self.recording_scheme_config_frame_label.grid(
            row=0, column=0, columnspan=2, sticky="n", pady=(30, 0))
        self.action_type_label.grid(row=1, column=0, columnspan=1)
        self.action_type_combo_box.grid(row=1, column=1, columnspan=1)
        self.calibrate_label.grid(row=2, column=0, columnspan=1)
        self.calibrate_check_box.grid(row=2, column=1, columnspan=1)
        self.add_action_to_run_button.grid(row=3, column=0, columnspan=1)
        self.remove_action_to_run_button.grid(row=3, column=1, columnspan=1)
        self.scheme_config_text.grid(row=4, column=0, columnspan=1, sticky="nsew")
        self.scheme_config_scrollbar.grid(row=4, column=1, sticky="ns")
        self.repeated_runs_label.grid(
            row=5, column=0, columnspan=1, sticky="nsew")
        self.repeated_runs_entry.grid(row=5, column=1, columnspan=1)

        self.recording_operation_frame.grid(row=0, column=3, sticky="nsew")
        self.recording_operation_frame_label.grid(
            row=0, column=0, columnspan=2, sticky="n", pady=(30, 0))
        self.trial_button.grid(row=1, column=0, columnspan=2, sticky="")
        self.recording_button.grid(
            row=2, column=0, columnspan=1, padx=10, pady=(23, 0), sticky="n")
        self.stop_recording_button.grid(
            row=2, column=1, columnspan=1, padx=10, pady=(23, 0), sticky="n")
        self.recording_progress_label.grid(row=3, column=0, columnspan=2)
        # add_border(self.recording, 3, 8)

        # ---------------------Cue Window---------------------#
        self.cue_window = None

        # ---------------------Settings---------------------#
        self.display_mode_flag = CTk.IntVar(value=0)
        self.display_mode_switch = CTk.CTkSwitch(self.settings, text="Chế độ tối", font=("Arial", 18),
                                                 command=self.switch_display_mode, variable=self.display_mode_flag,
                                                 onvalue=1, offvalue=0,
                                                 switch_width=48, switch_height=27)
        self.display_mode_switch.grid(row=0, column=0, sticky="n")

        self.get_latest_scheme_config()

    def toggle_eeg_connection(self):
        if self.eeg_connection_flag.get() == 0:
            self.eeg_stream = None
            self.inlet = None
            self.eeg_connection_switch.configure(
                text="Kết nối thiết bị Emotiv | Ngắt kết nối", font=("Arial", 18))
        else:
            print("Looking for a stream...")
            self.eeg_stream = resolve_stream('type', 'EEG')
            # self.inlet = StreamInlet(self.eeg_stream[0], max_buflen=1)
            # print(self.inlet)
            # print(self.inlet.pull_sample())
            self.eeg_connection_switch.configure(
                text="Kết nối thiết bị Emotiv | Đã kết nối", font=("Arial", 18))

    def handle_client_connection(client_socket):
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
            client_handler = threading.Thread(
                target=self.handle_client_connection, args=(client_socket,))
            client_handler.start()
        server_socket.close()

    def start_server_thread(self):
        if self.server_thread is None or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(
                target=self.start_server, daemon=True)
            self.server_thread.start()

    def toggle_vr_connection(self):
        global server_running
        if self.vr_connection_flag.get() == 1:
            print(f"Initializing TCP connection...")
            server_running = True
            self.start_server_thread()
            self.vr_connection.configure(
                text="Kết nối kính VR | Đã kết nối", font=("Arial", 18))
        elif self.vr_connection_flag.get() == 0:
            server_running = False
            self.vr_connection.configure(
                text="Kết nối kính VR | Đã ngắt kết nối", font=("Arial", 18))

    def submit(self):  # Implement to send messages through TCP connection for character selection
        pass

        # add_border(self.home, 2, 6)

    def get_setting(self):
        print("Getting settings...")
        if self.current_recording_setting.get() == "Pointer":
            self.set_pointer_setting()
        elif self.current_recording_setting.get() == "Character":
            self.set_character_setting()
        elif self.current_recording_setting.get() == "Custom":
            self.set_custom_setting()

    # TODO: define each setting according to the recording scheme video
    def set_pointer_setting(self):
        widgets = self.get_childrens(self.recording_duration_config_frame) + \
            self.get_childrens(self.recording_scheme_config_frame)
        self.enable_entries_and_buttons(widgets)
        self.reset_entries(widgets)
        self.rest_duration = 2
        self.cue_duration = 2
        self.action_duration = 4
        self.calibration_duration = 0
        self.repeated_runs = 3

        self.calibration_flag.set("no")
        self.calibrate_check_box.deselect()
        self.calibration_scheme = []

        self.recording_scheme_per_run = [
            [Action.R, self.rest_duration],
            [Action.C, self.cue_duration],
            [Action.RH, self.action_duration],
            [Action.R, self.rest_duration],
            [Action.C, self.cue_duration],
            [Action.LH, self.action_duration],
            [Action.R, self.rest_duration],
            [Action.C, self.cue_duration],
            [Action.RF, self.action_duration],
            [Action.R, self.rest_duration],
            [Action.C, self.cue_duration],
            [Action.LF, self.action_duration],
        ]

        self.update_setting_label()
        print(self.recording_scheme_per_run)
        self.disable_entries_and_buttons(widgets)

    def set_character_setting(self):
        widgets = self.get_childrens(self.recording_duration_config_frame) + \
            self.get_childrens(self.recording_scheme_config_frame)
        self.enable_entries_and_buttons(widgets)
        self.reset_entries(widgets)
        self.rest_duration = 5
        self.cue_duration = 0
        self.action_duration = 3
        self.calibration_duration = 5
        self.repeated_runs = 1

        self.calibration_flag.set("yes")
        self.calibrate_check_box.select()
        self.calibration_scheme = [[Action.PTL, self.calibration_duration],
                                   [Action.PTR, self.calibration_duration],
                                   [Action.B, self.calibration_duration],
                                   [Action.OCM, self.calibration_duration],
                                   [Action.NH, self.calibration_duration],
                                   [Action.SH, self.calibration_duration]]

        self.recording_scheme_per_run = [
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.LH, self.action_duration],
            [Action.RH, self.action_duration],
            [Action.LHOC, self.action_duration],
            [Action.RHOC, self.action_duration],
            [Action.LF, self.action_duration],
            [Action.RF, self.action_duration],
            [Action.T, self.action_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.LH, self.action_duration],
            [Action.RH, self.action_duration],
            [Action.LHOC, self.action_duration],
            [Action.RHOC, self.action_duration],
            [Action.LF, self.action_duration],
            [Action.RF, self.action_duration],
            [Action.T, self.action_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.LH, self.action_duration],
            [Action.RH, self.action_duration],
            [Action.LHOC, self.action_duration],
            [Action.RHOC, self.action_duration],
            [Action.LF, self.action_duration],
            [Action.RF, self.action_duration],
            [Action.T, self.action_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.A, self.action_duration],
            [Action.A, self.action_duration],
            [Action.A, self.action_duration],
            [Action.A, self.action_duration],
            [Action.A, self.action_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.M, self.action_duration],
            [Action.M, self.action_duration],
            [Action.M, self.action_duration],
            [Action.M, self.action_duration],
            [Action.M, self.action_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.A, self.action_duration],
            [Action.A, self.action_duration],
            [Action.A, self.action_duration],
            [Action.A, self.action_duration],
            [Action.A, self.action_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.R, self.rest_duration],
            [Action.M, self.action_duration],
            [Action.M, self.action_duration],
            [Action.M, self.action_duration],
            [Action.M, self.action_duration],
            [Action.M, self.action_duration],
        ]

        print(self.recording_scheme_per_run)
        self.update_setting_label()
        self.disable_entries_and_buttons(widgets)

    def set_custom_setting(self):
        widgets = self.get_childrens(self.recording_duration_config_frame) + \
            self.get_childrens(self.recording_scheme_config_frame)
        self.enable_entries_and_buttons(widgets)
        self.get_latest_scheme_config()

    def add_calibration(self):
        if self.calibration_flag.get() == "yes":
            self.calibration_scheme = [[Action.PTL, self.calibration_duration],
                                       [Action.PTR, self.calibration_duration],
                                       [Action.B, self.calibration_duration],
                                       [Action.OCM, self.calibration_duration],
                                       [Action.NH, self.calibration_duration],
                                       [Action.SH, self.calibration_duration]]
        else:
            self.calibration_scheme = []
        self.update_run_config()

    def add_action(self):
        action_type = None

        value = self.action_type_combo_box.get()
        match value:
            case "Nghỉ":
                action_type = Action.R
                duration = self.rest_duration
            case "Gợi ý":
                action_type = Action.C
                duration = self.cue_duration
            case "Tay trái":
                action_type = Action.LH
                duration = self.action_duration
            case "Tay phải":
                action_type = Action.RH
                duration = self.action_duration
            case "Chân trái":
                action_type = Action.LF
                duration = self.action_duration
            case "Chân phải":
                action_type = Action.RF
                duration = self.action_duration
            case "Nhìn trái":
                action_type = Action.PTL
                duration = self.calibration_duration
            case "Nhìn phải":
                action_type = Action.PTR
                duration = self.calibration_duration
            case "Nháy mắt":
                action_type = Action.B
                duration = self.calibration_duration
            case "Đóng/Mở miệng":
                action_type = Action.OCM
                duration = self.calibration_duration
            case "Gật đầu":
                action_type = Action.NH
                duration = self.calibration_duration
            case "Lắc đầu":
                action_type = Action.SH
                duration = self.calibration_duration
            case "Nắm/Mở tay trái":
                action_type = Action.LHOC
                duration = self.action_duration
            case "Nắm/Mở tay phải":
                action_type = Action.RHOC
                duration = self.action_duration
            case "Lưỡi":
                action_type = Action.T
                duration = self.action_duration
            case "Cộng":
                action_type = Action.A
                duration = self.action_duration
            case "Nhân":
                action_type = Action.M
                duration = self.action_duration
            
        if (duration != ""):
            action = [action_type, duration]
            self.recording_scheme_per_run.append(action)
            self.update_run_config()  # add the last action added to the representition string
        else:
            self.show_error_message(
                "Thời lượng thực hiện hành động không xác định")

    def remove_action(self):
        if len(self.recording_scheme_per_run) != 0:
            self.recording_scheme_per_run.pop()
            self.update_run_config()
        else:
            return

    def update_run_config(self):
        self.rest_duration = int(self.rest_duration_entry.get())
        self.cue_duration = int(self.cue_duration_entry.get())
        self.action_duration = int(self.action_duration_entry.get())
        self.calibration_duration = int(self.calibration_duration_entry.get())
        self.repeated_runs = int(self.repeated_runs_entry.get())

        self.update_setting_label()
        self.update_last_scheme_config()

    def update_setting_label(self):
        widgets = self.get_childrens(self.recording)
        self.reset_entries(widgets)
        if (self.rest_duration_entry.get() == ""):
            self.rest_duration_entry.insert(0, str(self.rest_duration))
        if (self.cue_duration_entry.get() == ""):
            self.cue_duration_entry.insert(0, str(self.cue_duration))
        if (self.action_duration_entry.get() == ""):
            self.action_duration_entry.insert(0, str(self.action_duration))
        if (self.calibration_duration_entry.get() == ""):
            self.calibration_duration_entry.insert(
                0, str(self.calibration_duration))
        if (self.repeated_runs_entry.get() == ""):
            self.repeated_runs_entry.insert(0, str(self.repeated_runs))

        cur_action_names = ""
        for action in self.calibration_scheme + self.recording_scheme_per_run:
            action_name = ""
            match action[0]:
                case Action.R:
                    action_name = "Nghỉ"
                    action[1] = self.rest_duration
                case Action.C:
                    action_name = "Gợi ý"
                    action[1] = self.cue_duration
                case Action.LH:
                    action_name = "Tay trái"
                    action[1] = self.action_duration
                case Action.RH:
                    action_name = "Tay phải"
                    action[1] = self.action_duration
                case Action.LF:
                    action_name = "Chân trái"
                    action[1] = self.action_duration
                case Action.RF:
                    action_name = "Chân phải"
                    action[1] = self.action_duration
                case Action.PTL:
                    action_name = "Nhìn trái"
                    action[1] = self.calibration_duration
                case Action.PTR:
                    action_name = "Nhìn phải"
                    action[1] = self.calibration_duration
                case Action.B:
                    action_name = "Nháy mắt"
                    action[1] = self.calibration_duration
                case Action.OCM:
                    action_name = "Đóng/Mở miệng"
                    action[1] = self.calibration_duration
                case Action.NH:
                    action_name = "Gật đầu"
                    action[1] = self.calibration_duration
                case Action.SH:
                    action_name = "Lắc đầu"
                    action[1] = self.calibration_duration
                case Action.LHOC:
                    action_name = "Nắm/Mở tay trái"
                    action[1] = self.action_duration
                case Action.RHOC:
                    action_name = "Nắm/Mở tay phải"
                    action[1] = self.action_duration
                case Action.T:
                    action_name = "Lưỡi"
                    action[1] = self.action_duration
                case Action.A:
                    action_name = "Cộng"
                    action[1] = self.action_duration
                case Action.M:
                    action_name = "Nhân"
                    action[1] = self.action_duration
            cur_action_names = action_name + " (" + str(action[1]) + ")" if (cur_action_names == "") else (
                cur_action_names + ", " + action_name + " (" + str(action[1]) + ")")
        print("Calibration:" + self.calibration_flag.get())
        print(self.recording_scheme_per_run)
        self.scheme_config_text.insert(
            tkinter.END, cur_action_names)

    def update_last_scheme_config(self):
        scheme = []
        for action in self.recording_scheme_per_run:
            scheme.append(action[0].value)
        last_config = {
            "rest_duration": self.rest_duration,
            "cue_duration": self.cue_duration,
            "action_duration": self.action_duration,
            "calibration_duration": self.calibration_duration,
            "calibrated": self.calibration_flag.get(),
            "scheme": scheme,
            "repeated_runs": self.repeated_runs
        }
        with open(f"last_config.json", "w") as file:
            json.dump(last_config, file)

    def get_latest_scheme_config(self):
        if os.path.exists(f"last_config.json"):
            with open(f"last_config.json", "r") as file:
                last_config = json.load(file)
                print(last_config)
                widgets = self.get_childrens(self.recording)
                self.reset_entries(widgets)
                self.recording_scheme_per_run = []
                self.rest_duration = last_config["rest_duration"]
                self.cue_duration = last_config["cue_duration"]
                self.action_duration = last_config["action_duration"]
                self.calibration_duration = last_config["calibration_duration"]
                self.repeated_runs = last_config["repeated_runs"]
                self.calibration_flag.set(last_config["calibrated"])

                if (self.calibration_flag.get() == "yes"):
                    self.calibration_scheme = [[Action.PTL, self.calibration_duration],
                                               [Action.PTR, self.calibration_duration],
                                               [Action.B, self.calibration_duration],
                                               [Action.OCM, self.calibration_duration],
                                               [Action.NH, self.calibration_duration],
                                               [Action.SH, self.calibration_duration]]

                cur_action_names = ""
                for action_index in last_config["scheme"]:
                    duration = 0
                    match action_index:
                        case 1: duration = self.rest_duration
                        case 2: duration = self.cue_duration
                        case 7: duration = self.calibration_duration
                        case 8: duration = self.calibration_duration
                        case 9: duration = self.calibration_duration
                        case 10: duration = self.calibration_duration
                        case 11: duration = self.calibration_duration
                        case 12: duration = self.calibration_duration
                        case _: duration = self.action_duration
                    self.recording_scheme_per_run.append(
                        [Action(action_index), duration])

            self.update_setting_label()
            print(self.recording_scheme_per_run)
        else:
            last_config = {
                "rest_duration": self.rest_duration,
                "cue_duration": self.cue_duration,
                "action_duration": self.action_duration,
                "calibration_duration": self.calibration_duration,
                "calibrated": "no",
                "scheme": [],
                "repeated_runs": self.repeated_runs
            }
            with open(f"last_config.json", "w") as file:
                json.dump(last_config, file)

    def generate_setting_file(self):
        setting = {
            "duration": {
                "Action.R": self.rest_duration,
                "Action.C":  self.cue_duration,
                "Action.RH": self.action_duration,
                "Action.LH": self.action_duration,
                "Action.RF": self.action_duration,
                "Action.LF": self.action_duration,
                "Action.PTL": self.calibration_duration,
                "Action.PTR": self.calibration_duration,
                "Action.B": self.calibration_duration,
                "Action.OCM": self.calibration_duration,
                "Action.NH": self.calibration_duration,
                "Action.SH": self.calibration_duration,
                "Action.RHOC": self.action_duration,
                "Action.LHOC": self.action_duration,
                "Action.T": self.action_duration,
                "Action.A": self.action_duration,
                "Action.M": self.action_duration,
            },
            "calibrated": self.calibration_flag.get(),
            "num_of_runs": self.repeated_runs
        }
        with open(f"{self.get_file_path('json')}", "w") as file:
            json.dump(setting, file)

    def generate_label_file(self):  # Call when recording is finished
        with open(f"{self.get_file_path('txt')}", "w") as file:
            for i in range(0, self.repeated_runs):
                for action in self.calibration_scheme + self.recording_scheme_per_run:
                    file.write(f"{action[0].value}" + '\n')

    def generate_data_file(self, data):
        data = np.array(data)
        df = pd.DataFrame(data)
        df.to_csv(f"{self.get_file_path('csv')}", index=False)

    # TODO: sync sample pull with system clock with the lowest error margin possible (<1ms)
    def pull_eeg_data(self):
        self.inlet = StreamInlet(self.eeg_stream[0], max_buflen=1)
        print(self.inlet)
        self.update_run_config()
        self.inlet.open_stream()
        data = []
        global recording_in_progress
        # self.inlet.open_stream()
        # Calibration scheme loop
        if (self.calibration_flag.get() == "yes"):
            cur_action_index = 0
            sample_count = 0
            trial_first_sample_timestamp = 0  # used for testing
            while recording_in_progress and cur_action_index < len(self.calibration_scheme):
                sample, timestamp = self.inlet.pull_sample()
                if timestamp != None:  # Depends on the mapping of electrodes on the EEG devices
                    data.append(sample[3:(len(sample)-2)])
                    sample_count += 1

                    # used for testing sync between UI and sample pull
                    if trial_first_sample_timestamp == 0:
                        trial_first_sample_timestamp = timestamp
                        print("Timestamp of first sample for this action: " +
                              str(trial_first_sample_timestamp))
                    # print(timestamp)

                # All samples of an action recorded
                if sample_count == self.calibration_scheme[cur_action_index][1] * self.sampling_frequency:
                    sample_count = 0
                    cur_action_index = cur_action_index + 1
                    print("Timestamp of last sample for this action: " +
                          str(timestamp))
                    print("Duration between first and last sample: " +
                          str(trial_first_sample_timestamp - timestamp))
                    trial_first_sample_timestamp = 0
        # Recording scheme loop
        for i in range(0, self.repeated_runs):
            cur_action_index = 0
            sample_count = 0
            trial_first_sample_timestamp = 0  # used for testing

            while recording_in_progress and cur_action_index < len(self.recording_scheme_per_run):
                sample, timestamp = self.inlet.pull_sample()
                if timestamp != None:  # Depends on the mapping of electrodes on the EEG devices
                    data.append(sample[3:(len(sample)-2)])
                    sample_count += 1

                    # used for testing sync between UI and sample pull
                    if trial_first_sample_timestamp == 0:
                        trial_first_sample_timestamp = timestamp
                        print("Timestamp of first sample for this action: " +
                              str(trial_first_sample_timestamp))
                    # print(timestamp)

                # All samples of an action recorded
                if sample_count == self.recording_scheme_per_run[cur_action_index][1] * self.sampling_frequency:
                    sample_count = 0
                    cur_action_index = cur_action_index + 1
                    print(cur_action_index)

                    print("Timestamp of last sample for this action: " +
                          str(timestamp))
                    print("Duration between first and last sample: " +
                          str(trial_first_sample_timestamp - timestamp))
                    trial_first_sample_timestamp = 0

        self.generate_label_file()
        self.generate_data_file(data)
        self.generate_setting_file()
        self.recording_progress_label.configure(text="Hoàn thành thu dữ liệu")

        # self.inlet.close_stream()
        self.stop_recording()
        data = []

    def start_eeg_thread(self):
        if self.eeg_thread is None or not self.eeg_thread.is_alive():
            self.eeg_thread = threading.Thread(
                target=self.pull_eeg_data, daemon=True)
            self.eeg_thread.start()

    def start_recording(self):
        global recording_in_progress
        if self.eeg_connection_flag.get() == 0:
            self.show_error_message("Không có kết nối với mũ thu EEG")
        else:
            if self.name_entry.get() != "" and self.location_entry.get() != "" and self.recording_device_name_entry.get() != "":
                recording_in_progress = True

                self.init_cue_window()
                self.start_eeg_thread()
                self.recording_progress_label.configure(
                    text="Đang thu dữ liệu...", font=("Arial", 18))
            else:
                self.show_error_message(
                    "Chưa có đủ các trường dữ liệu: Tên, Địa điểm, Máy thu")

    def stop_recording(self):
        global recording_in_progress
        recording_in_progress = False
        self.inlet.close_stream()
        self.inlet = None
        print(self.eeg_thread)
        del (self.eeg_thread)
        self.eeg_thread = None

    # ----------------------Settings----------------------#
    # Light and Dark Mode switch

    def switch_display_mode(self):
        if self.display_mode_flag.get() == 0:
            CTk.set_appearance_mode("light")
        elif self.display_mode_flag.get() == 1:
            CTk.set_appearance_mode("dark")

    # ----------------------Utils----------------------#
    def get_childrens(self, window):
        lst = window.winfo_children()

        for item in lst:
            if item.winfo_children():
                lst.extend(item.winfo_children())
        return lst

    def reset_entries(self, widgets):
        for widget in widgets:
            if isinstance(widget, CTk.CTkEntry):
                widget.delete(0, "end")
            if isinstance(widget, tkinter.Text):
                widget.delete('1.0', tkinter.END)
        print("Entry and text reset for window")

    def disable_entries_and_buttons(self, widgets):
        for widget in widgets:
            if isinstance(widget, CTk.CTkEntry) or isinstance(widget, CTk.CTkButton) or isinstance(widget, CTk.CTkCheckBox) or isinstance(widget, tkinter.Text):
                widget.configure(state="disabled")
        print("Entry and button disabled")

    def enable_entries_and_buttons(self, widgets):
        for widget in widgets:
            if isinstance(widget, CTk.CTkEntry) or isinstance(widget, CTk.CTkButton) or isinstance(widget, CTk.CTkCheckBox) or isinstance(widget, tkinter.Text):
                widget.configure(state="normal")
        print("Entry and button enabled")

    def show_error_message(self, error_message):
        error_window = CTk.CTkToplevel(self)
        error_window.title("Error")
        error_window.geometry("300x200")
        error_window.attributes("-topmost", True)

        error_label = CTk.CTkLabel(
            error_window, text="Lỗi", font=("Arial", 18), fg_color="red")

        message_label = CTk.CTkLabel(
            error_window, text=error_message, font=("Arial", 18),  fg_color="red")

        ok_button = CTk.CTkButton(error_window, text="OK", font=(
            "Arial", 18), command=error_window.destroy)

        error_label.grid(row=1, column=1, columnspan=2)
        message_label.grid(row=2, column=1, columnspan=2)
        ok_button.grid(row=3, column=1, columnspan=2)

        # def get_data_folder_path(): #TODO: allow users to pick data folder
        #     folder_selected = filedialog.askdirectory()
        #     if folder_selected:
        #         return f"{folder_selected}"

    # TODO: get the folder directory that the user chooses
    # TODO: add location and recording device name to folder tree
    def get_file_path(self, file_type):
        if self.name_entry.get() != "" and self.location_entry.get() != "" and self.recording_device_name_entry.get() != "":

            dir_path = "data/" + datetime.now().strftime("%d_%B_%Y") + "/" + self.current_recording_setting.get() + \
                "/" + self.name_entry.get()
            if os.path.isdir(dir_path) == False:
                os.makedirs(dir_path)
                print("Directory created")
            file_path = dir_path + "/" + self.name_entry.get() + "_" + \
                datetime.now().strftime("%d_%B_%Y_%H_%M_%S") + "_" + self.location_entry.get() + \
                "_" + self.recording_device_name_entry.get() + "." + file_type
            return file_path
        else:
            self.show_error_message(
                "Chưa có đủ các trường dữ liệu: Tên, Địa điểm, Máy thu")

    def init_cue_window(self):
        self.update_run_config()
        window = CTk.CTkToplevel(self)
        window.title("Gợi ý")

        w, h = 1280, 720
        ws = user32.GetSystemMetrics(0)
        hs = user32.GetSystemMetrics(1)
        x = int(((ws-w)/2)/window._get_window_scaling())
        y = int(((hs-h)/2)/window._get_window_scaling())
        print(w, h, x, y)

        # Main app configuration
        window.title("VR-BCI")
        window.resizable(False, False)
        window.geometry('%dx%d+%d+%d' % (w, h, x, y))
        window.attributes("-topmost", True)

        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=14)
        window.grid_rowconfigure(2, weight=1)

        if (len(self.recording_scheme_per_run) == 0):
            self.show_error_message(error_message="Hãy nhập kịch bản thu")
        else:
            self.cue_window = CueWindow(
                window, self.calibration_scheme, self.recording_scheme_per_run, self.repeated_runs)

            self.cue_window.root = window
            if self.cue_window.timer_flag == False:
                self.cue_window.label.grid(row=0, sticky="n")
                self.cue_window.image.grid(row=1, sticky="swen")
                self.cue_window.instruction.grid(row=1, sticky="we")
                self.cue_window.timer_flag = True


class CueWindow:
    def __init__(self, root, calibration_scheme, main_recording_scheme, nums_of_runs) -> None:
        self.root = root
        self.recording_scheme = []
        self.recording_scheme += calibration_scheme
        for i in range(0, nums_of_runs):
            self.recording_scheme += main_recording_scheme

        print(self.recording_scheme)
        self.sound_path = ""
        self.voice_thread = None

        # Initiallize timer variables
        self.seconds = 0
        self.timer_flag = False
        self.cue_flag = False
        self.counter = 0

        self.total_nums_of_actions = len(self.recording_scheme)

        # Create a countdown clock to display the timer
        self.label = CTk.CTkLabel(
            self.root, text='00:00', font=("Helvetica", 48))

        # load cue images
        # TODO: add images for additional actions
        self.images = [CTk.CTkImage(light_image=Image.open(
            "assets/images/arrow_left_foot.png"), size=(900, 550)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/arrow_right_foot.png"), size=(900, 550)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/arrow_left_hand.png"), size=(900, 550)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/arrow_right_hand.png"), size=(900, 550)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/blink_eyes.png"), size=(1000, 400)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/look_right.png"), size=(900, 450)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/look_left.png"), size=(900, 450)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/nod_head.png"), size=(600, 400)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/open_left_hand.png"), size=(900, 550)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/open_mouth.png"), size=(900, 400)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/open_right_hand.png"), size=(900, 550)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/shake_head.png"), size=(500, 600)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/tongue.png"), size=(900, 550)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/calculate_add.png"), size=(850, 550)),
            CTk.CTkImage(light_image=Image.open(
                "assets/images/calculate_multiply.png"), size=(800, 550)),]
        self.image = CTk.CTkLabel(self.root, image=None, text="")
        self.instruction = CTk.CTkLabel(
            self.root, text="", font=("Helvetica", 48))
        # Update the timer display
        self.voice_thread = threading.Thread(target=self.play_sound, args=(
            Action.R, ),  daemon=True).start()
        self.set(self.recording_scheme[0][1])
        print(self.seconds)
        self.update()

    def stop(self):
        self.counter = 0
        self.timer_flag = 0  # stop timer
        self.root.destroy()
        return

    def calculate(self):
        minutes = self.seconds // 60
        seconds = self.seconds % 60
        time_str = f"{minutes:02}:{seconds:02}"
        print(time_str)
        return time_str

    def update(self):
        if self.timer_flag:
            if (self.counter >= len(self.recording_scheme)):
                self.stop()
            time_str = self.calculate()
            self.label.configure(text=time_str)
            action = self.recording_scheme[self.counter][0]
            duration = self.recording_scheme[self.counter][1]

            if self.seconds != 0:
                if (self.seconds == duration):
                    if (action != Action.R):
                        self.image.grid(row=1, sticky="we")
                        self.get_image(actionType=action)
                    self.instruction.grid(row=2, sticky="we")
                    self.get_instruction(actionType=action)
                    match action:
                        case Action.C:
                            action = self.recording_scheme[self.counter+1][0]
                            self.get_image(action)
                            self.get_instruction(action)
                            self.voice_thread = threading.Thread(target=self.play_sound, args=(
                                action, ),  daemon=True).start()
                        case _:
                            if self.counter-1 >= 0 and self.recording_scheme[self.counter-1][0] != Action.C and self.recording_scheme[self.counter-1][0] != action:
                                self.voice_thread = threading.Thread(target=self.play_sound, args=(
                                    action, ),  daemon=True).start()

                    # self.voice_thread = threading.Thread(target=self.play_sound, args=(
                    #     action, ),  daemon=True).start()
                self.seconds -= 1
            else:
                self.counter += 1
                if self.counter != self.total_nums_of_actions:
                    if self.recording_scheme[self.counter][0] == Action.R:
                        self.image.grid_forget()
                    self.set(self.recording_scheme[self.counter][1])
                    self.root.after(0, self.update)
                    return
                else:
                    self.stop()
        self.root.after(1000, self.update)
    # TODO: get cue image for addtional actions

    def get_image(self, actionType):
        print("Getting image...")
        if actionType == Action.LF:
            self.image.configure(image=self.images[0])
        elif actionType == Action.RF:
            self.image.configure(image=self.images[1])
        elif actionType == Action.LH:
            self.image.configure(image=self.images[2])
        elif actionType == Action.RH:
            self.image.configure(image=self.images[3])
        elif actionType == Action.PTL:
            self.image.configure(image=self.images[6])
        elif actionType == Action.PTR:
            self.image.configure(image=self.images[5])
        elif actionType == Action.B:
            self.image.configure(image=self.images[4])
        elif actionType == Action.OCM:
            self.image.configure(image=self.images[9])
        elif actionType == Action.NH:
            self.image.configure(image=self.images[7])
        elif actionType == Action.SH:
            self.image.configure(image=self.images[11])
        elif actionType == Action.LHOC:
            self.image.configure(image=self.images[8])
        elif actionType == Action.RHOC:
            self.image.configure(image=self.images[10])
        elif actionType == Action.T:
            self.image.configure(image=self.images[12])
        elif actionType == Action.A:
            self.image.configure(image=self.images[13])
        elif actionType == Action.M:
            self.image.configure(image=self.images[14])
            
        self.image.configure(image=None)

    def get_instruction(self, actionType):
        if actionType == Action.R:
            self.instruction.configure(text="Nghỉ ngơi")
        if actionType == Action.LF:
            self.instruction.configure(text="Nâng chân trái")
        if actionType == Action.RF:
            self.instruction.configure(text="Nâng chân phải")
        if actionType == Action.LH:
            self.instruction.configure(text="Nâng tay trái")
        if actionType == Action.RH:
            self.instruction.configure(text="Nâng tay phải")
        if actionType == Action.PTL:
            self.instruction.configure(text="Nhìn sang trái")
        if actionType == Action.PTR:
            self.instruction.configure(text="Nhìn sang phải")
        if actionType == Action.B:
            self.instruction.configure(text="Nháy mắt")
        if actionType == Action.OCM:
            self.instruction.configure(text="Đóng/Mở miệng")
        if actionType == Action.NH:
            self.instruction.configure(text="Gật đầu")
        if actionType == Action.SH:
            self.instruction.configure(text="Lắc đầu")
        if actionType == Action.LHOC:
            self.instruction.configure(text="Nắm/mở tay trái")
        if actionType == Action.RHOC:
            self.instruction.configure(text="Nắm/mở tay phải")
        if actionType == Action.T:
            self.instruction.configure(text="Chuyển động lưỡi")
        if actionType == Action.A:
            self.instruction.configure(text="Thực hiện phép cộng")
        if actionType == Action.M:
            self.instruction.configure(text="Thực hiện phép nhân")

    def set(self, amount):
        self.seconds = amount

    # TODO:add audio file for each
    def play_sound(self, actionType):
        match actionType:
            case Action.R: self.sound_path = u"assets/sounds/beep.mp3"
            case Action.LH: self.sound_path = u"assets/sounds/left_hand.mp3"
            case Action.RH: self.sound_path = u"assets/sounds/right_hand.mp3"
            case Action.LF: self.sound_path = u"assets/sounds/left_leg.mp3"
            case Action.RF: self.sound_path = u"assets/sounds/right_leg.mp3"
            case Action.PTL: self.sound_path = u"assets/sounds/look_left.mp3"
            case Action.PTR: self.sound_path = u"assets/sounds/look_right.mp3"
            case Action.B: self.sound_path = u"assets/sounds/blink.mp3"
            case Action.OCM: self.sound_path = u"assets/sounds/open_mouth.mp3"
            case Action.NH: self.sound_path = u"assets/sounds/nod_head.mp3"
            case Action.SH: self.sound_path = u"assets/sounds/shake_head.mp3"
            case Action.LHOC: self.sound_path = u"assets/sounds/open_left_hand.mp3"
            case Action.RHOC: self.sound_path = u"assets/sounds/open_right_hand.mp3"
            case Action.T: self.sound_path = u"assets/sounds/tongue.mp3"
            case _: return
        playsound(self.sound_path)

# Main loop
app = App()
app.mainloop()
