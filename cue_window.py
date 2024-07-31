from utils import Action
from playsound import playsound
import customtkinter as CTk
from PIL import Image
import threading

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
            self.recording_scheme[0][0], ),  daemon=True).start()
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