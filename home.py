import customtkinter as CTk
from PIL import Image
from utils import genders, normalize_string
from config import HOST, PORT
import json
from pylsl import StreamInlet, resolve_stream
import time
import socket
import threading
from data_puller import DataPuller
class Home:
    def __init__(self, root, data_puller):
        self.home_connection_frame = CTk.CTkFrame(
            master=root, fg_color="light blue")
        self.home_connection_frame_label = CTk.CTkLabel(
            master=self.home_connection_frame,  text="Thiết lập kết nối", font=("Arial", 24))
        self.home_connection_frame.grid_rowconfigure(0, weight=1)
        self.home_connection_frame.grid_rowconfigure(1, weight=1)
        self.home_connection_frame.grid_rowconfigure(2, weight=1)
        self.home_connection_frame.grid_rowconfigure(3, weight=4)
        self.home_connection_frame.grid_columnconfigure(0, weight=1)

        self.home_info_frame = CTk.CTkFrame(
            master=root, fg_color="SpringGreen2")

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
        # endregion
        # EEG Stream connection
        # self.eeg_stream = None  # LSL Stream for emotiv connection
        # self.inlet = None  # InletStream
        self.data_puller = data_puller

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

        # region Patient entry field
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
        self.patient_information_submitted = False
        self.patient_information_sent = False
        # Recorder entry field
        self.recording_facility_name_entry = CTk.CTkEntry(self.home_recorder_info_frame, placeholder_text="Nhập tên đơn vị thu",
                                                          height=40, width=240, font=("Arial", 18))
        self.recording_device_name_entry = CTk.CTkEntry(self.home_recorder_info_frame, placeholder_text="Nhập tên thiết bị thu",
                                                        height=40, width=240, font=("Arial", 18))
        # endregion
        # region Widget layout assignment
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
        # endregion
        
    def toggle_eeg_connection(self):
        if self.eeg_connection_flag.get() == 0:
            self.data_puller.data_stream.start_stream()
            self.eeg_connection_switch.configure(
                text="Kết nối thiết bị Emotiv | Ngắt kết nối", font=("Arial", 18))
        else:
            self.data_puller.data_stream.close_stream()
            self.eeg_connection_switch.configure(
                text="Kết nối thiết bị Emotiv | Đã kết nối", font=("Arial", 18))

    # TODO: create module to handle message sending for each catergory
    def handle_client_connection(self, client_socket):
        message = ""
        last_message = ""
        while True:
            try:
                # Get the required message
                if (self.patient_information_submitted and not self.patient_information_sent):
                    message = self.get_patient_information_message()
                if (self.patient_information_sent):
                    if (self.current_exercise.get() == ""):
                        message = self.get_current_exercise_message()
                    else:
                        message = self.infer()

                # Send the message
                if (message != "" and message != last_message):
                    client_socket.send(bytes(message, 'utf-8'))
                    print("Sending " + message)
                    if (len(message) == 2):
                        self.patient_information_sent = True
                    last_message = message
                time.sleep(2)
            except ConnectionResetError:
                print(ConnectionResetError)
                break
        client_socket.close()

    def get_patient_information_message(self):
        message = ""
        gender = self.gender_options.get()
        if gender == "Nam":
            message += "M"  # Male
        elif gender == "Nữ":
            message += "F"

        age = int(self.age_entry.get())
        if age > 50:
            message += "O"
        else:
            message += "Y"
        # Final patient info message should be MY, MO, FY, FO
        if len(message) == 2:
            return message
        else:
            return ""

    # TODO: change to get_current_exercise_scheme for making a one-time selection of the training environment, exercises and app training tab UI
    # TODO: Parse this message in Unity interface to get the exercise
    def get_current_exercise_message(self):
        if self.current_exercise.get() == "Hands":
            return "HH"
        elif self.current_exercise.get() == "Left Hand Right Foot":
            return "HF"
        elif self.current_exercise.get() == "Right Hand Left Foot":
            return "FH"
        return ""

    def start_server(self):
        global server_running
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Server started and listening on port {PORT}")
        print(server_running)
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

    def submit(self):
        # Handle information need for character selection and file save
        if self.name_entry.get() != "" and self.age_entry.get() != "" and self.location_entry.get() != "" and self.gender_options.get() != "":
            self.generate_user_file()
            self.patient_information_submitted = True

    def generate_user_file(self):
        user = {
            "Name": self.name_entry.get(),
            "Age": self.age_entry.get(),
            "Gender": self.gender_options.get(),
            "Location": self.location_entry.get()
        }
        with open(f"{self.get_user_file_path()}", "w") as file:
            json.dump(user, file)
            
    def get_user_file_path(self):
        file_path = "user/" + normalize_string(self.name_entry.get()) + "_" + (
            "M" if self.gender_options.get() == "Nam" else "F") + "_" + normalize_string(self.age_entry.get()) + ".json"
        return file_path
    # endregion