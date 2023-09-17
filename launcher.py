import asyncio
import os
import signal
import tkinter as tk
from tkinter import ttk, StringVar
from tkinter import *
from tkinter import messagebox
import tkinter.filedialog as FD
from PIL import Image, ImageOps, ImageTk
import time
import subprocess


TITLE_FONT = ("Verdana", 24)
LARGE_FONT = ("Verdana", 12)
SMALL_FONT = ("TIMES NEW ROMAN", 11)

backGround = "black"
windowSizeX = 360
windowSizeY = 600


def on_closing():
    if visualizer.running:
        if messagebox.askokcancel("Exit", "Open Proccess, do you really want to exit?"):
            visualizer.stop_visualizer()
            app.destroy()
    app.destroy()


def invert_image_color(image_path):
    """Inverts the colors of an image."""
    img = Image.open(image_path)

    original_mode = img.mode

    # Convert to RGB for inversion
    if original_mode != "RGB":
        img = img.convert("RGB")

    inverted_img = ImageOps.invert(img)

    # If original was RGBA, convert back to RGBA and copy alpha channel
    if original_mode == "RGBA":
        alpha_channel = Image.open(image_path).split()[3]  # Splitting to get alpha (A)
        inverted_img.putalpha(alpha_channel)

    return inverted_img


def combine_funcs(*funcs):
    def combined_func(*args, **kwargs):
        for f in funcs:
            f(*args, **kwargs)

    return combined_func


class Config:
    def __init__(
        self,
        filename="config.txt",
        fps=30,
        resolution=(1920, 1200),
        fullscreen=False,
        launcher_host="localhost:5128",
    ):
        self.filename = filename
        self.fps = fps
        self.resolution = resolution
        self.fullscreen = fullscreen
        self.launcher_host = launcher_host

        # Read from file or generate a new file if it doesn't exist
        if not self._load_from_file():
            self._generate_default_file()

    def _load_from_file(self):
        try:
            with open(self.filename, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("FPS="):
                        self.fps = int(line.split("=")[1].strip())
                    elif line.startswith("RESOLUTION="):
                        res = line.split("=")[1].strip().split("x")
                        self.resolution = (int(res[0]), int(res[1]))
                    elif line.startswith("FULLSCREEN="):
                        self.fullscreen = line.split("=")[1].strip().lower() == "true"
                    elif line.startswith("LAUNCHER_HOST="):
                        self.launcher_host = line.split("=")[1].strip()
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error loading config: {e}\n Connecting to localhost:5128")
            return False

    def _generate_default_file(self):
        with open(self.filename, "w") as f:
            f.write(f"FPS={self.fps}\n")
            f.write(f"RESOLUTION={self.resolution[0]}x{self.resolution[1]}\n")
            f.write(f"FULLSCREEN={'true' if self.fullscreen else 'false'}\n")
            f.write(f"LAUNCHER_HOST={self.launcher_host}\n")


class Visualizer_Process:
    def __init__(
        self,
        fps=30,
        resolution=(1920, 1200),
        fullscreen=False,
        launcher_host="localhost:5128",
    ):
        self.fps = fps
        self.resolution = resolution
        self.fullscreen = fullscreen
        self.launcher_host = launcher_host
        self.script_path = "visualizer.py"
        self.process = None
        self.running = False

    def run_visualizer(self, config):
        if not self.running:
            try:
                # Create the string with a condition for --fullscreen
                self.formatted_string = f"--fps {self.fps} --resolution {self.resolution[0]}x{self.resolution[1]} --launcher-host {self.launcher_host}"
                if self.fullscreen:
                    self.formatted_string += " --fullscreen"

                # Split the formatted string into a list of arguments
                self.script_args = self.formatted_string.split()

                command = ["python", self.script_path] + self.script_args

                # Start the visualizer script as a new process and detach it
                self.process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    close_fds=True,
                    start_new_session=True,
                )
                self.running = True
            except Exception as e:
                print(f"Error starting visualizer: {e}")

    def stop_visualizer(self):
        if self.running and self.process:
            try:
                # Send a termination signal to the process
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process = None
                self.running = False
            except ProcessLookupError:
                self.process = None
                self.running = False
                pass  # The process might have already terminated


class Controller(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand=True)
        self.geometry(str(windowSizeY) + "x" + str(windowSizeX))  # Size 360p
        self.title("Drone Controller")
        self.tk.call(
            "wm", "iconphoto", Tk._w, PhotoImage(file="assets/Launcher_Icon.png")
        )
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (StartPage, Settings, visualizerSettings):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("StartPage")
        self.resizable(width=True, height=True)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class StartPage(ttk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=backGround)
        label = tk.Label(
            self, text="Drone Controller", font=TITLE_FONT, fg="#FFFFFF", bg=backGround
        )
        label.pack(pady=10, padx=10)

        # Using the "clam" theme which is more receptive to custom styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TButton",
            background=backGround,
            foreground="#FFFFFF",
            relief="flat",
            borderwidth=0,
        )

        button = ttk.Button(
            self,
            text="Start Joystick Service",
            command=lambda: controller.show_frame("EncryptorText"),
            style="Dark.TButton",
        )
        button.pack()

        button2 = ttk.Button(
            self,
            text="Start Radio Service",
            command=lambda: controller.show_frame("DecryptorText"),
            style="Dark.TButton",
        )
        button2.pack()

        visualizer_button_text = tk.StringVar()
        visualizer_button_text.set("Start Visualizer")

        def toggle_button():
            if visualizer.running:
                visualizer_button_text.set("Start Visualizer")
                visualizer.stop_visualizer()
            else:
                visualizer_button_text.set("Stop Visualizer")
                visualizer.run_visualizer(config)

        button3 = ttk.Button(
            self,
            textvariable=visualizer_button_text,
            command=toggle_button,
            style="Dark.TButton",
        )
        button3.pack()

        inverted_gear_image = invert_image_color("assets/gear.png")
        resized_gear_image = inverted_gear_image.resize(
            (inverted_gear_image.width * 2, inverted_gear_image.height * 2)
        )
        self.settingsIcon = ImageTk.PhotoImage(resized_gear_image)

        # Style for the gear button (using the same style for simplicity)
        button5 = ttk.Button(
            self,
            image=self.settingsIcon,
            command=lambda: controller.show_frame("Settings"),
            style="Dark.TButton",
        )
        button5.pack(side="bottom")


class Settings(tk.Frame):
    """Settings"""

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="black")
        self.FolderName = tk.StringVar()
        self.FolderName.set("")

        # Using the "clam" theme which is more receptive to custom styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TButton",
            background=backGround,
            foreground="#FFFFFF",
            relief="flat",
            borderwidth=0,
        )

        inverted_gear_image = invert_image_color("assets/gear.png")
        resized_gear_image = inverted_gear_image.resize(
            (inverted_gear_image.width * 2, inverted_gear_image.height * 2)
        )
        self.settingsIcon = ImageTk.PhotoImage(resized_gear_image)

        label = tk.Label(
            self, image=self.settingsIcon, font=LARGE_FONT, fg="#000000", bg="black"
        )
        label.pack()
        labe2 = tk.Label(self, text="", font=SMALL_FONT, bg="black")
        labe2.pack(pady=1, padx=1)

        button1 = ttk.Button(
            self,
            text="Save",
            command=lambda: controller.show_frame("StartPage"),
        )
        button1.pack(side="bottom")

        button2 = ttk.Button(
            self,
            text="Visualizer Settings",
            command=lambda: controller.show_frame("visualizerSettings"),
            style="Dark.TButton",
        )
        button2.pack()


class visualizerSettings(tk.Frame):
    """Visualizer Settings"""

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="black")
        self.FolderName = tk.StringVar()
        self.FolderName.set("")

        label = tk.Label(
            self, text="Visualizer Settings", font=TITLE_FONT, fg="#ffffff", bg="black"
        )
        label.pack()
        labe2 = tk.Label(self, text="", font=SMALL_FONT, bg="black")
        labe2.pack(pady=1, padx=1)

        button1 = ttk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("Settings"),
        )
        button1.pack(side="bottom")


if __name__ == "__main__":
    config = Config()

    app = Controller()
    app.resizable(False, False)
    app.rowconfigure(index=3, weight=1)

    visualizer = Visualizer_Process()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()
