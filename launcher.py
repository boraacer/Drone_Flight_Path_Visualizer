from multiprocessing import Manager
import time
import tkinter as tk
from tkinter import ttk, StringVar
from tkinter import *
from tkinter import messagebox
import tkinter.filedialog as FD
from PIL import Image, ImageOps, ImageTk


TITLE_FONT = ("Verdana", 24)
LARGE_FONT = ("Verdana", 12)
SMALL_FONT = ("TIMES NEW ROMAN", 11)

backGround = "black"
windowSizeX = 360
windowSizeY = 600


DEBUG = "Visualizer: "


def on_closing():
    if visualizer.running:
        if messagebox.askokcancel("Exit", "Open Proccess, do you really want to exit?"):
            visualizer.stop_visualizer()
            app.destroy()
    else:
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
        joystick=0,
        filter_threshold=0.05,
        filter_factor=0.9,
        serialport="COM3",
    ):
        self.filename = filename

        # Visualizer settings
        self.fps = fps
        self.resolution = resolution
        self.fullscreen = fullscreen

        # Joystick settings
        self.joystick = joystick
        self.filter_threshold = filter_threshold
        self.filter_factor = filter_factor
        
        # Radio settings
        self.serialport = serialport
        self.power_level = 23

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
                    elif line.startswith("JOYSTICK="):
                        self.joystick = int(line.split("=")[1].strip())
                    elif line.startswith("FILTER_THRESHOLD="):
                        self.filter_threshold = float(line.split("=")[1].strip())
                    elif line.startswith("FILTER_FACTOR="):
                        self.filter_factor = float(line.split("=")[1].strip())
                    elif line.startswith("SERIALPORT="):
                        self.serialport = line.split("=")[1].strip()
                    elif line.startswith("POWERLEVEL="):
                        self.power_level = int(line.split("=")[1].strip())

            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error loading config: {e}")
            return False

    def save_to_file(self):
        """Save the current settings to the config file."""
        try:
            with open(self.filename, "w") as f:
                f.write("# Config file for the Visualizer\n")
                f.write(f"FPS={self.fps}\n")
                f.write(f"RESOLUTION={self.resolution[0]}x{self.resolution[1]}\n")
                f.write(f"FULLSCREEN={'true' if self.fullscreen else 'false'}\n")
                f.write(f"JOYSTICK={self.joystick}\n")
                f.write(f"FILTER_THRESHOLD={self.filter_threshold}\n")
                f.write(f"FILTER_FACTOR={self.filter_factor}\n")
                f.write(f"SERIALPORT={self.serialport}\n")
                f.write(f"POWERLEVEL={self.power_level}\n")
                # If you have more settings, you can add them here
        except Exception as e:
            print(f"Error saving config: {e}")

    def _generate_default_file(self):
        with open(self.filename, "w") as f:
            f.write("# Config file for the Visualizer\n")
            f.write(f"FPS={self.fps}\n")
            f.write(f"RESOLUTION={self.resolution[0]}x{self.resolution[1]}\n")
            f.write(f"FULLSCREEN={'true' if self.fullscreen else 'false'}\n")
            f.write(f"JOYSTICK=0\n")
            f.write(f"FILTER_THRESHOLD={self.filter_threshold}\n")
            f.write(f"FILTER_FACTOR={self.filter_factor}\n")
            f.write(f"SERIALPORT={self.serialport}\n")
            f.write(f"POWERLEVEL={self.power_level}\n")


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
        for F in (StartPage, Settings, visualizerSettings, JoystickSettings, RadioSettings):
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

        joystick_button_text = tk.StringVar()
        joystick_button_text.set("Start Joystick")

        def toggle_joystick():
            
            if joystick.running:
                joystick_button_text.set("Start Joystick")
                joystick.stop_joystick()

            else:
                joystick_button_text.set("Stop Joystick")
                joystick.run_joystick(config)

        button1 = ttk.Button(
            self,
            textvariable=joystick_button_text,
            command=lambda: toggle_joystick(),
            style="Dark.TButton",
        )
        button1.pack()

        # Radio 
        
        radio_button_text = tk.StringVar()
        radio_button_text.set("Start Radio Service")

        def toggle_radio():
            if visualizer.running:
                radio_button_text.set("Start Radio Service")
                visualizer.stop_visualizer()
            else:
                radio_button_text.set("Stop Radio Service")
                visualizer.run_visualizer(config, joystick)

        button4 = ttk.Button(
            self,
            textvariable=radio_button_text,
            command=toggle_radio,
            style="Dark.TButton",
        )
        button4.pack()

        visualizer_button_text = tk.StringVar()
        visualizer_button_text.set("Start Visualizer")

        def toggle_visualizer():
            if visualizer.running:
                visualizer_button_text.set("Start Visualizer")
                visualizer.stop_visualizer()
            else:
                visualizer_button_text.set("Stop Visualizer")
                visualizer.run_visualizer(config, joystick)

        button3 = ttk.Button(
            self,
            textvariable=visualizer_button_text,
            command=toggle_visualizer,
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
            text="Back",
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

        button3 = ttk.Button(
            self,
            text="Joystick Settings",
            command=lambda: controller.show_frame("JoystickSettings"),
            style="Dark.TButton",
        )
        button3.pack()
        
        button4 = ttk.Button(
            self,
            text="Radio Settings",
            command=lambda: controller.show_frame("RadioSettings"),
            style="Dark.TButton",
        )
        button4.pack()


class visualizerSettings(tk.Frame):
    """Visualizer Settings"""

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="black")
        self.FolderName = tk.StringVar()
        self.FolderName.set("")

        label = tk.Label(
            self, text="Visualizer Settings", font=TITLE_FONT, fg="#ffffff", bg="black"
        )
        label.grid(row=0, column=0, columnspan=2, pady=10)

        # FPS Setting
        fps_label = tk.Label(
            self, text="FPS:", font=SMALL_FONT, fg="#ffffff", bg="black"
        )
        fps_label.grid(row=1, column=0, pady=5, sticky="e")
        self.fps_entry = tk.Entry(self, width=5)
        self.fps_entry.grid(row=1, column=1, pady=5, padx=20, sticky="w")

        # Resolution Setting
        resolution_label = tk.Label(
            self, text="Resolution:", font=SMALL_FONT, fg="#ffffff", bg="black"
        )
        resolution_label.grid(row=2, column=0, pady=5, sticky="e")
        self.resolutions = [
            "1280×800 (16:10)",
            "1920×1200 (16:10)",
            "2560x1600 (16:10)",
        ]
        self.resolution_combobox = ttk.Combobox(self, values=self.resolutions)
        self.resolution_combobox.grid(row=2, column=1, pady=5, padx=20, sticky="w")

        # Fullscreen Setting
        self.fullscreen_var = tk.BooleanVar()
        fullscreen_checkbutton = tk.Checkbutton(
            self,
            text="Fullscreen",
            variable=self.fullscreen_var,
            bg="black",
            fg="#ffffff",
        )
        fullscreen_checkbutton.grid(row=3, column=0, columnspan=2, pady=5)

        save_button = ttk.Button(self, text="Save Settings", command=self.save_settings)
        save_button.grid(row=5, column=0, columnspan=2, pady=10)
        back_button = ttk.Button(
            self, text="Back", command=lambda: controller.show_frame("Settings")
        )
        back_button.grid(row=5, column=1, columnspan=2, pady=10)

        # Centering the grid in the frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.load_settings()

    def save_settings(self):
        fps = int(self.fps_entry.get())
        resolution_str = self.resolution_combobox.get()

        # Map the resolution string to a tuple using if statements
        if resolution_str == "1280×800 (16:10)":
            resolution = (1280, 800)
        elif resolution_str == "1920×1200 (16:10)":
            resolution = (1920, 1200)
        elif resolution_str == "2560x1600 (16:10)":
            resolution = (2560, 1600)
        else:
            resolution = (0, 0)  # Default value

        fullscreen = self.fullscreen_var.get()

        config.fps = fps
        config.resolution = resolution
        config.fullscreen = fullscreen

        config.save_to_file()

    def load_settings(self):
        self.fps_entry.insert(0, str(config.fps))

        # Convert the tuple back to the string format using if statements
        resolution_tuple = config.resolution
        if resolution_tuple == (1280, 800):
            resolution_str = "1280×800 (16:10)"
        elif resolution_tuple == (1920, 1200):
            resolution_str = "1920×1200 (16:10)"
        elif resolution_tuple == (2560, 1600):
            resolution_str = "2560x1600 (16:10)"
        else:
            resolution_str = ""  # Default value

        self.resolution_combobox.set(resolution_str)
        self.fullscreen_var.set(config.fullscreen)


class JoystickSettings(tk.Frame):
    """Joystick Settings"""

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="black")
        self.joystick_list = []
        self.joystick_names = []

        self.config = config

        label = tk.Label(
            self, text="Joystick Settings", font=TITLE_FONT, fg="#ffffff", bg="black"
        )
        label.grid(row=0, column=0, columnspan=3, pady=10)

        # Joystick Selection
        joystick_label = tk.Label(
            self, text="Select Joystick:", font=SMALL_FONT, fg="#ffffff", bg="black"
        )
        joystick_label.grid(row=1, column=0, pady=5, sticky="e")
        self.refresh_joystick_list()

        self.joystick_combobox = ttk.Combobox(self, values=self.joystick_names)
        self.joystick_combobox.grid(row=1, column=1, pady=5, padx=20, sticky="w")
        try:
            self.joystick_combobox.set(self.joystick_name[config.joystick])
            self.joystick_combobox["values"] = self.joystick_name
        except Exception as e:
            print("Error setting joystick values:", e)

        refresh_button = ttk.Button(
            self, text="Refresh", command=self.refresh_joystick_list
        )
        refresh_button.grid(row=1, column=2, pady=5, padx=10)

        # Filter Threshold
        filter_threshold_label = tk.Label(
            self,
            text="Filter Threshold:",
            font=SMALL_FONT,
            fg="#ffffff",
            bg="black",
        )
        filter_threshold_label.grid(row=2, column=0, pady=5, sticky="e")

        self.filter_threshold_entry = tk.Entry(self, width=5)

        self.filter_threshold_entry.insert(0, str(config.filter_threshold))

        self.filter_threshold_entry.grid(row=2, column=1, pady=5, padx=20, sticky="w")

        # Filter Factor
        filter_factor_label = tk.Label(
            self,
            text="Filter Factor:",
            font=SMALL_FONT,
            fg="#ffffff",
            bg="black",
        )
        filter_factor_label.grid(row=3, column=0, pady=5, sticky="e")

        self.filter_factor_entry = tk.Entry(self, width=5)

        self.filter_factor_entry.insert(0, str(config.filter_factor))

        self.filter_factor_entry.grid(row=3, column=1, pady=5, padx=20, sticky="w")

        # Save and Back Buttons

        save_button = ttk.Button(self, text="Save", command=self.save_settings)
        save_button.grid(row=4, column=0, columnspan=3, pady=10)

        back_button = ttk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("Settings"),
        )
        back_button.grid(row=4, column=1, columnspan=3, pady=10)

        # Centering the grid in the frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(3, weight=1)

    def save_settings(self):
        selected_index = self.joystick_combobox.current()
        if selected_index == -1:
            messagebox.showerror("Error", "Please select a joystick.")
            return
        print(selected_index)
        self.config.joystick = selected_index

        self.config.filter_threshold = float(self.filter_threshold_entry.get())
        self.config.filter_factor = float(self.filter_factor_entry.get())

        self.config.save_to_file()
        messagebox.showinfo("Success", "Settings saved successfully!")

    def refresh_joystick_list(self):
        from joystick_service import get_joystick_list

        self.joystick_list = get_joystick_list()
        self.joystick_name = []
        for i in self.joystick_list:
            self.joystick_name.append(i["name"])

class RadioSettings(tk.Frame):
    """Joystick Settings"""

    def __init__(self, parent, controller):
        
        def refresh_serial_list():
            from radio_service import find_serial

            self.serial_list = find_serial()
            self.serial_name = []
            for i in self.serial_list:
                self.serial_name.append(i)
            self.serial_combobox["values"] = self.serial_name
        
        tk.Frame.__init__(self, parent, bg="black")
        self.serial_list = []
        self.serial_name = []

        self.config = config

        label = tk.Label(
            self, text="Radio Settings", font=TITLE_FONT, fg="#ffffff", bg="black"
        )
        label.grid(row=0, column=0, columnspan=3, pady=10)

        # Joystick Selection
        radio_label = tk.Label(
            self, text="Select USB Device:", font=SMALL_FONT, fg="#ffffff", bg="black"
        )
        radio_label.grid(row=1, column=0, pady=5, sticky="e")

        self.serial_combobox = ttk.Combobox(self, values=self.serial_name)
        self.serial_combobox.grid(row=1, column=1, pady=5, padx=20, sticky="w")
        
        refresh_serial_list()

        try:
            self.serial_combobox.set(config.serialport)
            self.serial_combobox["values"] = self.serial_name
        except Exception as e:
            print("Error setting radio value:", e)

        refresh_button = ttk.Button(
            self, text="Refresh", command=refresh_serial_list
        )
        refresh_button.grid(row=1, column=2, pady=5, padx=10)

        # Filter Threshold
        power_level_label = tk.Label(
            self,
            text="Power Level (5 - 23):",
            font=SMALL_FONT,
            fg="#ffffff",
            bg="black",
        )
        power_level_label.grid(row=2, column=0, pady=5, sticky="e")

        self.power_level_entry = tk.Entry(self, width=5)

        self.power_level_entry.insert(0, str(config.power_level))

        self.power_level_entry.grid(row=2, column=1, pady=5, padx=20, sticky="w")


        # Save and Back Buttons

        save_button = ttk.Button(self, text="Save", command=self.save_settings)
        save_button.grid(row=4, column=0, columnspan=3, pady=10)

        back_button = ttk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("Settings"),
        )
        back_button.grid(row=4, column=1, columnspan=3, pady=10)

        # Centering the grid in the frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(3, weight=1)
        

            
    def save_settings(self):
        selected_index = self.serial_combobox.current()
        if selected_index == -1:
            messagebox.showerror("Error", "Please select a Radio.")
            return
        print(selected_index)
        self.config.serialport =  self.serial_name[selected_index]
        self.config.power_level = int(self.power_level_entry.get())


        self.config.save_to_file()
        messagebox.showinfo("Success", "Settings saved successfully!")




if __name__ == "__main__":
    import Worker_Runner

    print(DEBUG + "Starting Launcher")
    config = Config()


    visualizer = Worker_Runner.Visualizer_Process()
    
    manager = Manager()
    
    joystick_process = manager.Namespace()
    joystick = Worker_Runner.Joystick_Process()
    
    app = Controller()
    app.resizable(False, False)
    app.rowconfigure(index=3, weight=1)

    app.protocol("WM_DELETE_WINDOW", on_closing)

    app.mainloop()
