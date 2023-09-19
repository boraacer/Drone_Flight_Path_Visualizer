import multiprocessing
import os
import signal
import time
from launcher import Config
import visualizer
import joystick_service as joystick


class Visualizer_Process:
    def __init__(self):
        self.process = None
        self.running = False

    def visualizer_function(self, config):
        # This function will be run in the new process
        # Here, you'll need to call the main function or equivalent of visualizer.py
        # For this example, I'm assuming visualizer.py has a function called run_visualizer_script
        visualizer.main(config)

    def run_visualizer(self, config):
        if not self.running:
            try:
                # Start the visualizer script as a new process
                self.process = multiprocessing.Process(
                    target=self.visualizer_function,
                    args=(
                        config,
                        self.data,
                    ),
                )
                self.process.start()
                self.running = True
            except Exception as e:
                print(f"Error starting visualizer: {e}")

    def stop_visualizer(self):
        if self.running and self.process:
            try:
                # Terminate the process
                self.process.terminate()
                self.process.join()  # Wait for the process to finish
                self.process = None
                self.running = False
            except Exception as e:
                print(f"Error stopping visualizer: {e}")

    def retrieve_data(self):
        while not self.queue.empty():
            print(self.queue.get())

    def send_data(self, data):
        self.queue.put(data)


class Joystick_Process:
    def __init__(self):
        self.process = None
        self.running = False
        manager = multiprocessing.Manager()
        self.data = manager.dict()
        self.data.update(
            {
                "axis_0": 0.0,
                "axis_1": 0.0,
                "axis_2": 0.0,
                "axis_3": 0.0,
                "axis_4": 0.0,
                "axis_5": 0.0,
                "button_0": False,
                "button_1": False,
                "button_2": False,
                "button_3": False,
                "button_4": False,
                "button_5": False,
                "button_6": False,
                "button_7": False,
                "button_8": False,
                "button_9": False,
                "button_10": False,
                "button_11": False,
                "button_12": False,
                "button_13": False,
                "button_14": False,
                "button_15": False,
                "button_16": False,
            }
        )

        self.lock = manager.Lock()

    def get_data(self):
        with self.lock:
            return self.data["axis_0"]

    def joystick_function(self, config, data, lock):
        # This function will be run in the new process
        # Here, you'll need to call the main function or equivalent of visualizer.py
        # For this example, I'm assuming visualizer.py has a function called run_visualizer_script
        joystick.main(config, data, lock)

    def run_joystick(self, config):
        print("Starting joystick process")
        if not self.running:
            try:
                # Start the visualizer script as a new process
                self.process = multiprocessing.Process(
                    target=self.joystick_function,
                    args=(
                        config,
                        self.data,
                        self.lock,
                    ),
                )
                self.process.start()
                self.running = True
            except Exception as e:
                print(f"Error starting joystick process: {e}")

    def stop_joystick(self):
        print("Stopping joystick process")
        if self.running and self.process:
            try:
                # Send a SIGINT signal to the process
                os.kill(self.process.pid, signal.SIGINT)
                self.stop_retrieve_data_thread()
                self.process.join()  # Wait for the process to finish
                self.process = None
                self.running = False
            except Exception as e:
                print(f"Error stopping joystick process: {e}")

    def monitor_data(self):
        while True:
            time.sleep(0.1)  # Monitor at a different interval
            with self.lock:
                print(self.data)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    joystick_process = Joystick_Process()

    print("Starting worker runner")
    config = Config()
    visualizer_process = Visualizer_Process()
    # visualizer_process.run_visualizer(config)

    joystick_process.run_joystick(config)

    joystick_process.monitor_data()
