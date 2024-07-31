import customtkinter as CTk
from PIL import Image
import numpy as np
from pylsl import StreamInlet
import threading
from utils import show_error_message

#TODO: Finish Training tab setup to communicate with VR interface
class Training:
    def __init__(self, root):
         # region Layout
        self.training_setting_frame = CTk.CTkFrame(
            master=root, fg_color="lavender")
        self.current_exercise = CTk.StringVar(value="")
        self.training_setting_frame.grid_rowconfigure(0, weight=1)
        self.training_setting_frame.grid_rowconfigure(1, weight=1)
        self.training_setting_frame.grid_rowconfigure(2, weight=1)
        self.training_setting_frame.grid_rowconfigure(3, weight=1)
        self.training_setting_frame.grid_columnconfigure(0, weight=4)
        self.training_setting_frame.grid_columnconfigure(1, weight=1)

        self.training_info_frame = CTk.CTkFrame(
            master=root, fg_color="floral white"
        )
        self.training_info_frame.grid_columnconfigure(0, weight=1)
        self.training_info_frame.grid_columnconfigure(1, weight=4)
        self.training_info_frame.grid_rowconfigure(0, weight=1)
        self.training_info_frame.grid_rowconfigure(1, weight=3)
        # endregion
        # region Training setting widget
        self.training_setting_frame_label = CTk.CTkLabel(
            master=self.training_setting_frame,  text="Lựa chọn bài tập", font=("Arial", 24))
        self.hands_exercise_image = CTk.CTkImage(light_image=Image.open(
            "assets/images/hands_exercise.png"), size=(200, 200))
        self.hands_exercise_image_label = CTk.CTkLabel(
            self.training_setting_frame, image=self.hands_exercise_image, text="")
        self.hands_exercise_option = CTk.CTkRadioButton(
            master=self.training_setting_frame, command=self.get_exercise_scheme,
            variable=self.current_exercise, value="Hands", text=""
        )
        self.left_hand_right_foot_exercise_image = CTk.CTkImage(light_image=Image.open(
            "assets/images/left_hand_right_foot_exercise.png"), size=(200, 200))
        self.left_hand_right_foot_exercise_image_label = CTk.CTkLabel(
            self.training_setting_frame, image=self.left_hand_right_foot_exercise_image, text="")
        self.left_hand_right_foot_exercise_option = CTk.CTkRadioButton(
            master=self.training_setting_frame, command=self.get_exercise_scheme,
            variable=self.current_exercise, value="Left Hand Right Foot", text=""
        )

        self.right_hand_left_foot_exercise_image = CTk.CTkImage(light_image=Image.open(
            "assets/images/right_hand_left_foot_exercise.png"), size=(200, 200))
        self.right_hand_left_foot_exercise_image_label = CTk.CTkLabel(
            self.training_setting_frame, image=self.right_hand_left_foot_exercise_image, text="")
        self.right_hand_left_foot_exercise_option = CTk.CTkRadioButton(
            master=self.training_setting_frame, command=self.get_exercise_scheme,
            variable=self.current_exercise, value="Right Hand Left Foot", text=""
        )
        # endregion

        # region Training info widget
        self.data_buffer = []
        # self.figure, self.ax = None, None 
        self.figure = None

        # self.EEG_canvas = FigureCanvasTkAgg(
        #     self.figure, master=self.training_info_frame)
        self.start_training_button = CTk.CTkButton(self.training_info_frame, text="Bắt đầu luyện tập", font=(
            "Arial", 18), command=self.start_training_session, height=40, width=100)
        self.stop_training_button = CTk.CTkButton(self.training_info_frame, text="Kết thúc luyện tập", font=(
            "Arial", 18), command=self.stop_training_session, height=40, width=100)

        self.time_window = 10
        self.plot_update_rate = 1

        self.info = None
        self.raw = None
        self.is_training = False
        
        self.data_thread = None
        self.plotting_thread = None
        self.exercises_list = []

        # endregion

        # region Widget layout assignment
        self.training_setting_frame.grid(row=0, column=0, sticky="nsew")
        self.training_info_frame.grid(row=0, column=1, sticky="nswe")
        
        self.training_setting_frame_label.grid(row=0, column=0, columnspan=2)
        self.hands_exercise_image_label.grid(row=1, column=0, sticky="we")
        self.hands_exercise_option.grid(row=1, column=1)
        self.left_hand_right_foot_exercise_image_label.grid(
            row=2, column=0, sticky="we")
        self.left_hand_right_foot_exercise_option.grid(row=2, column=1)
        self.right_hand_left_foot_exercise_image_label.grid(
            row=3, column=0, sticky="we")
        self.right_hand_left_foot_exercise_option.grid(row=3, column=1)

        # self.EEG_canvas.get_tk_widget().grid(row=0, column=0, columnspan=2, sticky="nwe")
        self.start_training_button.grid(row=1, column=0, sticky="new")
        self.stop_training_button.grid(row=1, column=0, sticky="sew")
        # endregion
        # endregion
      
    def get_exercise_scheme(self):
            print("Getting exercise...")
            if self.current_exercise.get() == "Hands":
                self.set_hands_exercise()
            elif self.current_exercise.get() == "Left Hand Right Foot":
                self.set_left_hand_right_foot_exercise()
            elif self.current_exercise.get() == "Right Hand Left Foot":
                self.set_right_hand_left_foot_exercise()
    # TODO : Send command to VR interface to change the exercise environment
    def set_hands_exercise(self):
        pass

    def set_left_hand_right_foot_exercise(self):
        pass

    def set_right_hand_left_foot_exercise(self):
        pass

    def start_training_session(self):
        # On starting a training session:
        #   - Send training scheme to Unity interface
        #   - Start pulling EEG samples from LSL
        #       + Plot these datas in a 10 second time window, updating every second
        #       + Create a randomized training scheme for the session, consisting of 0 and 1, corresponding to left and right
        #       + Infer from 12 4.5s overlapping windows, with an interval of 0.5s and see which result are more likely
        #   - Continue for the entire training scheme or until stopped (stop_trainin_session)
        self.patient_information_sent = True ##dummy
        if (self.patient_information_sent == False):
            show_error_message(self, "Hãy nhập và gửi thông tin người bệnh!")
        elif (self.current_exercise.get() == ""):
            show_error_message(self, "Hãy chọn bài tập!")
        else:
            self.is_training = True
            self.inlet = StreamInlet(self.eeg_stream[0], max_buflen=1)
            self.data_buffer = np.zeros(
                (self.time_window * self.sampling_frequency, self.inlet.channel_count - 5))
            # self.info = mne.create_info(ch_names=["Fz", "FC3", "FC1", "C5", "C3", "C1", "Cz", "CP3", "CP1",
            #                             "P1", "Pz", "FCz", "FC2", "FC4", "C2", "C4", "C6", "CP4", "CP2", "CPz", "P2", "POz"], sfreq=self.sampling_frequency, ch_types="eeg")
            # self.raw = mne.io.RawArray(self.data_buffer, self.info)
            # self.figure = self.raw.plot(show=False, block=False)
            self.exercises_list = self.generate_random_exercise(10)
            # self.start_plotting_thread()
        # self.update_data_buffer()

    def stop_training_session(self):
        self.is_training = False

    def update_plot(self):
        while self.is_training:
            self.update_data_buffer()
            # self.update_raw()
            
            # self.figure = self.raw.plot(show=False, block=False)
            
            # self.EEG_canvas.draw()
            print(self.data_buffer)
            # plt.pause(self.plot_update_rate) ## error?

    def update_data_buffer(self):
        for _ in range(int(self.plot_update_rate * self.sampling_frequency)):
            sample, timestamp = self.inlet.pull_sample(timeout=1.0)
            if timestamp:
                sample = np.array(sample[3:len(sample)-2])
                # Update data buffer
                self.data_buffer = np.roll(self.data_buffer, -1, axis=0)
                self.data_buffer[-1, :] = sample[:]

    def update_raw(self):
        self.raw._data = self.data_buffer

    def infer_from_buffer(self):
        pass

    # def start_data_thread(self):
    #     pass

    def start_plotting_thread(self):
        if self.plotting_thread is None or not self.plotting_thread.is_alive():
            self.plotting_thread = threading.Thread(
                target=self.update_plot, daemon=True
            )
            self.plotting_thread.start()
    # endregion