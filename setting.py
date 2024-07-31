import customtkinter as CTk
class Settings:
    def __init__(self, root):
        self.display_mode_flag = CTk.IntVar(value=0)
        self.display_mode_switch = CTk.CTkSwitch(root, text="Chế độ tối", font=("Arial", 18),
                                                 command=self.switch_display_mode, variable=self.display_mode_flag,
                                                 onvalue=1, offvalue=0,
                                                 switch_width=48, switch_height=27)
        self.display_mode_switch.grid(row=0, column=0, sticky="n")

        
   
    def switch_display_mode(self):
        if self.display_mode_flag.get() == 0:
            CTk.set_appearance_mode("light")
        elif self.display_mode_flag.get() == 1:
            CTk.set_appearance_mode("dark")