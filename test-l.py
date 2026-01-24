#Тестовий лаунчер який я зробив по приколу
import os
import sys
import subprocess

try:
    import customtkinter as ctk
except Exception:
    raise RuntimeError("Please install customtkinter: python -m pip install customtkinter")

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Time Slash Launcher")
root.geometry("480x200")
root.resizable(False, False)

root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=0)
root.grid_columnconfigure(0, weight=1)

title = ctk.CTkLabel(root, text="TIME SLASH", font=("Arial", 28, "bold"))
title.grid(row=0, column=0, sticky="nsew")

def launch_game():
    script = os.path.join(os.path.dirname(__file__), "prototype-0.py")
    python = sys.executable or "python"
    try:
        subprocess.Popen([python, script], cwd=os.path.dirname(script))
    except Exception as e:
        print("Failed to launch:", e)

play_btn = ctk.CTkButton(root, text="PLAY", width=120, height=40, command=launch_game)
play_btn.grid(row=1, column=0, sticky="w", padx=12, pady=12)

root.mainloop()
