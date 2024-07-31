from enum import Enum
import re
import customtkinter as CTk
import tkinter
import random

# Actions include: Rest, Cue, Right Hand, Left Hand, Right Feet, Left Feet,
# Pupil to Left, Pupil to Right, Blink, Open/Close Mouth, Nod head, Shake head,
# Left Hand Open/Close, Right Hand Open/Close, Tongue, Add, Multiply

Action = Enum("Action", ["R", "C", "RH", "LH", "RF",
              "LF", "PTL", "PTR", "B", "OCM", "NH", "SH", "LHOC", "RHOC", "T", "A", "M"])
genders = ["Nam", "Nữ"]
def normalize_string(s):
    # Remove punctuation
    s = re.sub(r'[^\w\s]', '', s)

    # Remove extra whitespace
    s = re.sub(r'\s+', ' ', s).strip()

    return s


def get_childrens(window):
    lst = window.winfo_children()

    for item in lst:
        if item.winfo_children():
            lst.extend(item.winfo_children())
    return lst


def reset_entries(widgets):
    for widget in widgets:
        if isinstance(widget, CTk.CTkEntry):
            widget.delete(0, "end")
        if isinstance(widget, tkinter.Text):
            widget.delete('1.0', tkinter.END)
    print("Entry and text reset for window")


def disable_entries_and_buttons(widgets):
    for widget in widgets:
        if isinstance(widget, CTk.CTkEntry) or isinstance(widget, CTk.CTkButton) or isinstance(widget, CTk.CTkCheckBox) or isinstance(widget, tkinter.Text):
            widget.configure(state="disabled")
    print("Entry and button disabled")


def enable_entries_and_buttons(widgets):
    for widget in widgets:
        if isinstance(widget, CTk.CTkEntry) or isinstance(widget, CTk.CTkButton) or isinstance(widget, CTk.CTkCheckBox) or isinstance(widget, tkinter.Text):
            widget.configure(state="normal")
    print("Entry and button enabled")

def generate_random_exercise(self, nums_of_exercises):
        exercises = []
        for i in range(0, nums_of_exercises):
            exercises.append(random.randint(0,1))
        return exercises
    
def show_error_message(self, error_message):
    error_window = CTk.CTkToplevel(self.root.winfo_toplevel())
    error_window.title("Error")
    error_window.geometry("300x200")
    error_window.attributes("-topmost", True)

    error_label = CTk.CTkLabel(
        error_window, text="Lỗi", font=("Arial", 18), fg_color="red")

    message_label = CTk.CTkLabel(
        error_window, text=error_message, font=("Arial", 18),  fg_color="red", wraplength=300)

    ok_button = CTk.CTkButton(error_window, text="OK", font=(
        "Arial", 18), command=error_window.destroy)

    error_label.grid(row=1, column=1, columnspan=2)
    message_label.grid(row=2, column=1, columnspan=2)
    ok_button.grid(row=3, column=1, columnspan=2)