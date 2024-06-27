from tkinter import *
import customtkinter as CTk
import os

CTk.set_appearance_mode("dark")  # Modes: system (default), light, dark
CTk.set_default_color_theme("green")  # Themes: blue (default), dark-blue, green

#root = Tk()
root = CTk.CTk()
print(os.getcwd())
# os.chdir("assets/themes")
# print(os.getcwd())

root.title('Tkinter.com - CTK Custom Color Themes')
# root.iconbitmap('images/codemy.ico')
root.geometry('700x550')

mode = "dark"

def change_colors(choice):
	path = "D:/IOT/EEG-ATCNet/assets/themes/" + choice + ".json"
	print(path)
	CTk.set_default_color_theme(path)
	# CTk.set_default_color_theme(choice)

def change():
	global mode
	if mode == "dark":
		CTk.set_appearance_mode("light")
		mode = "light"
		# Clear text box
		my_text.delete(0.0, END)
		my_text.insert(END, "This is Light Mode...")
	else:
		CTk.set_appearance_mode("dark")
		mode = "dark"
		# Clear text box
		my_text.delete(0.0, END)
		my_text.insert(END, "This is Dark Mode...")


my_text = CTk.CTkTextbox(root, width=600, height=300)
my_text.pack(pady=20)

my_button = CTk.CTkButton(root, text="Change Light/Dark", command=change)
my_button.pack(pady=20)

colors = ["Anthracite", "Blue", "Cobalt", "DaynNight", "GhostTrain", "Greengage",
           "GreyGhost", "Hades", "Harlequin", "MoonlitSky", "NeonBanana", "NightTrain",
           "Oceanix", "Sweetkind", "TestCard", "TrojanBlue"]
my_option = CTk.CTkOptionMenu(root, values=colors, command=change_colors)
my_option.pack(pady=10)

my_progress = CTk.CTkProgressBar(root, orientation="horizontal")
my_progress.pack(pady=20)

root.mainloop()