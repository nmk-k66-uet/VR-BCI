import customtkinter as CTk

CTk.set_appearance_mode("System")
CTk.set_default_color_theme("green")

# Init main app
app = CTk.CTk()

# Calulate window position
w, h = 1280, 720
ws = app.winfo_screenwidth()
hs = app.winfo_screenheight()
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)

# Main app configuration
app.title("VR-BCI")
app.resizable(False, False)
app.geometry('%dx%d+%d+%d'% (w, h, x, y))
app.iconbitmap("assets/icon/cat_icon.ico")
butt1 = CTk.CTkButton(app, text="Hello")
butt1.pack(pady = 80)

app.mainloop()
