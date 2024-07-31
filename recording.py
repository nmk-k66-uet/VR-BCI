import customtkinter as CTk
import tkinter
from utils import Action, get_childrens, normalize_string, reset_entries, disable_entries_and_buttons, enable_entries_and_buttons, show_error_message
import json
import os
import threading
import numpy as np
import pandas as pd
from pylsl import StreamInlet
import ctypes
from cue_window import CueWindow


user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

class Recording:
    def __init__(self, root):
        self.root = root
        # region Layout
        self.root = root
        self.recording_setting_frame = CTk.CTkFrame(
            master=root, fg_color="azure")
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
            master=root, fg_color="light blue")
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
            master=root, fg_color="aquamarine")
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
            master=root, fg_color="khaki")
        self.recording_operation_frame_label = CTk.CTkLabel(
            master=self.recording_operation_frame, text="Thu dữ liệu", font=("Arial", 24))
        self.recording_operation_frame.grid_columnconfigure(0, weight=1)
        self.recording_operation_frame.grid_columnconfigure(1, weight=1)
        self.recording_operation_frame.grid_rowconfigure(0, weight=1)
        self.recording_operation_frame.grid_rowconfigure(1, weight=1)
        self.recording_operation_frame.grid_rowconfigure(2, weight=1)
        self.recording_operation_frame.grid_rowconfigure(3, weight=1)
        self.recording_operation_frame.grid_rowconfigure(4, weight=6)
        # endregion
        # region Run configuration stage:
        self.calibration_scheme = []
        self.recording_scheme_per_run = []
        self.latest_run_duration = 0
        self.recording_setting_pointer_option = CTk.CTkRadioButton(
            master=self.recording_setting_frame, text="Bài thu con trỏ", font=("Arial", 18),
            command=self.get_recording_setting, variable=self.current_recording_setting, value="Pointer"
        )
        self.recording_setting_character_option = CTk.CTkRadioButton(
            master=self.recording_setting_frame, text="Bài thu kí tự", font=("Arial", 18),
            command=self.get_recording_setting, variable=self.current_recording_setting, value="Character"
        )
        self.recording_setting_custom_option = CTk.CTkRadioButton(
            master=self.recording_setting_frame, text="Tùy chỉnh bài thu", font=("Arial", 18),
            command=self.get_recording_setting, variable=self.current_recording_setting, value="Custom"
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
        self.scheme_config_text.configure(
            yscrollcommand=self.scheme_config_scrollbar.set)

        self.repeated_runs_label = CTk.CTkLabel(
            self.recording_scheme_config_frame, text="Số lần lặp lại kịch bản:", wraplength=180, font=("Arial", 18))
        self.repeated_runs_entry = CTk.CTkEntry(
            self.recording_scheme_config_frame, placeholder_text="1", height=40, font=("Arial", 18))
        self.repeated_runs = 0
        # endregion
        # region Recording stage:
        self.sampling_frequency = 128

        self.eeg_thread = None
        self.cue_window = None

        self.trial_button = CTk.CTkButton(self.recording_operation_frame, text="Thu thử", font=(
            "Arial", 18), command=lambda: self.init_cue_window(), height=40, width=100)
        self.start_recording_button = CTk.CTkButton(self.recording_operation_frame, text="Bắt đầu thu", font=(
            "Arial", 18), command=self.start_recording, height=40, width=100)

        self.stop_recording_button = CTk.CTkButton(self.recording_operation_frame, text="Dừng thu", font=(
            "Arial", 18), command=self.stop_recording, height=40, width=100)

        self.recording_progress_label = CTk.CTkLabel(
            self.recording_operation_frame, text="", font=("Arial", 18))
        # endregion
        # region Widget layout assignment
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
        self.scheme_config_text.grid(
            row=4, column=0, columnspan=1, sticky="nsew")
        self.scheme_config_scrollbar.grid(row=4, column=1, sticky="ns")
        self.repeated_runs_label.grid(
            row=5, column=0, columnspan=1, sticky="nsew")
        self.repeated_runs_entry.grid(row=5, column=1, columnspan=1)

        self.recording_operation_frame.grid(row=0, column=3, sticky="nsew")
        self.recording_operation_frame_label.grid(
            row=0, column=0, columnspan=2, sticky="n", pady=(30, 0))
        self.trial_button.grid(row=1, column=0, columnspan=2, sticky="")
        self.start_recording_button.grid(
            row=2, column=0, columnspan=1, padx=10, pady=(23, 0), sticky="n")
        self.stop_recording_button.grid(
            row=2, column=1, columnspan=1, padx=10, pady=(23, 0), sticky="n")
        self.recording_progress_label.grid(row=3, column=0, columnspan=2)
        # add_border(root, 3, 8)
        # endregion
    def get_recording_setting(self):
        print("Getting settings...")
        if self.current_recording_setting.get() == "Pointer":
            self.set_pointer_setting()
        elif self.current_recording_setting.get() == "Character":
            self.set_character_setting()
        elif self.current_recording_setting.get() == "Custom":
            self.set_custom_setting()

    def set_pointer_setting(self):
        widgets = get_childrens(self.recording_duration_config_frame) + \
            get_childrens(self.recording_scheme_config_frame)
        enable_entries_and_buttons(widgets)
        reset_entries(widgets)
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
        disable_entries_and_buttons(widgets)

    def set_character_setting(self):
        widgets = get_childrens(self.recording_duration_config_frame) + \
            get_childrens(self.recording_scheme_config_frame)
        enable_entries_and_buttons(widgets)
        reset_entries(widgets)
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
        disable_entries_and_buttons(widgets)

    def set_custom_setting(self):
        widgets = get_childrens(self.recording_duration_config_frame) + \
            get_childrens(self.recording_scheme_config_frame)
        enable_entries_and_buttons(widgets)
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
            show_error_message(self,
                "Thời lượng thực hiện hành động không xác định")

    def remove_action(self):
        if len(self.recording_scheme_per_run) != 0:
            self.recording_scheme_per_run.pop()
            self.update_run_config()
        else:
            return

    def update_run_config(self):
        if (self.rest_duration_entry.get() == "" or
            self.cue_duration_entry.get() == "" or
            self.action_duration_entry.get() == "" or
            self.calibration_duration_entry.get() == "" or
            self.repeated_runs_entry.get()):
            show_error_message(self, "Thời lượng thực hiện chưa đầy đủ")
        else:
            self.rest_duration = int(self.rest_duration_entry.get())
            self.cue_duration = int(self.cue_duration_entry.get())
            self.action_duration = int(self.action_duration_entry.get())
            self.calibration_duration = int(self.calibration_duration_entry.get())
            self.repeated_runs = int(self.repeated_runs_entry.get())

            self.update_setting_label()
            self.update_last_scheme_config()

    def update_setting_label(self):
        widgets = get_childrens(self.root)
        reset_entries(widgets)
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
                widgets = get_childrens(self.root)
                reset_entries(widgets)
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
        with open(f"{self.get_data_file_path('json')}", "w") as file:
            json.dump(setting, file)

    def generate_label_file(self):  # Call when recording is finished
        with open(f"{self.get_data_file_path('txt')}", "w") as file:
            for action in self.calibration_scheme:
                file.write(f"{action[0].value}" + '\n')
            for i in range(0, self.repeated_runs):
                for action in self.recording_scheme_per_run:
                    file.write(f"{action[0].value}" + '\n')

    def generate_data_file(self, data):
        data = np.array(data)
        df = pd.DataFrame(data)
        df.to_csv(f"{self.get_data_file_path('csv')}", index=False)

    # TODO: sync sample pull with system clock with the lowest error margin possible (<1ms)
    def pull_eeg_data(self):
        print(self.inlet)
        self.update_run_config()
        self.inlet.open_stream()
        data = []
        first_sample_timestamp = 0
        last_sample_timestamp = 0

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
                    if first_sample_timestamp == 0:
                        first_sample_timestamp = timestamp
                        print("Update first sample timestamp")
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

                    if first_sample_timestamp == 0:
                        first_sample_timestamp = timestamp
                        print("Update first sample timestamp")
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
                    if cur_action_index == len(self.recording_scheme_per_run):
                        last_sample_timestamp = timestamp
                        print("Update last sample_timestamp")
                    print(cur_action_index)

                    print("Timestamp of last sample for this action: " +
                          str(timestamp))
                    print("Duration between first and last sample: " +
                          str(trial_first_sample_timestamp - timestamp))
                    trial_first_sample_timestamp = 0

        self.latest_run_duration = last_sample_timestamp - first_sample_timestamp
        print("Run duration: " + str(self.latest_run_duration))
        self.generate_label_file()
        self.generate_data_file(data)
        self.generate_setting_file()
        self.recording_progress_label.configure(text="Hoàn thành thu dữ liệu")

        first_sample_timestamp = 0
        last_sample_timestamp = 0
        # self.inlet.close_stream()
        data = []
        self.stop_recording()

    def start_eeg_thread(self):
        if self.eeg_thread is None or not self.eeg_thread.is_alive():
            self.eeg_thread = threading.Thread(
                target=self.pull_eeg_data, daemon=True)
            self.eeg_thread.start()

    def start_recording(self):
        global recording_in_progress
        if self.eeg_connection_flag.get() == 0:
            show_error_message(self, "Không có kết nối với mũ thu EEG")
        else:
            if self.name_entry.get() != "" and self.location_entry.get() != "" and self.recording_device_name_entry.get() != "":
                recording_in_progress = True

                self.init_cue_window()
                self.inlet = StreamInlet(self.eeg_stream[0], max_buflen=1)
                self.start_eeg_thread()
                self.recording_progress_label.configure(
                    text="Đang thu dữ liệu...", font=("Arial", 18))
            else:
                show_error_message(self, 
                    "Chưa có đủ các trường dữ liệu: Tên, Địa điểm, Máy thu")

    def stop_recording(self):
        global recording_in_progress
        recording_in_progress = False
        self.inlet.close_stream()
        self.inlet = None
        print(self.eeg_thread)
        del(self.eeg_thread)
        self.eeg_thread = None
        return
    
    def get_run_duration(self):
        run_duration = 0
        for action in self.calibration_scheme:
            run_duration += action[1]
        for action in self.recording_scheme_per_run:
            run_duration += action[1] * self.repeated_runs
        return run_duration

    def containsArtifact(self):
        dif = abs(self.get_run_duration() - self.latest_run_duration)
        print("Dif between real recording time and scheme time: " + str(dif))
        if (dif >= 1.5):
            return "Artifact_"
        return ""

    def init_cue_window(self):
        self.update_run_config()
        window = CTk.CTkToplevel(self.root.winfo_toplevel())
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
            show_error_message(self, error_message="Hãy nhập kịch bản thu")
        else:
            self.cue_window = CueWindow(
                window, self.calibration_scheme, self.recording_scheme_per_run, self.repeated_runs)

            self.cue_window.root = window
            if self.cue_window.timer_flag == False:
                self.cue_window.label.grid(row=0, sticky="n")
                self.cue_window.image.grid(row=1, sticky="swen")
                self.cue_window.instruction.grid(row=1, sticky="we")
                self.cue_window.timer_flag = True
    # endregion