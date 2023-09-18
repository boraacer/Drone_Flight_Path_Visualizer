import multiprocessing
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
                    target=self.visualizer_function, args=(config,)
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

    def joystick_function(self, config):
        # This function will be run in the new process
        # Here, you'll need to call the main function or equivalent of visualizer.py
        # For this example, I'm assuming visualizer.py has a function called run_visualizer_script
        joystick.main(config)

    def run_joystick(self, config):
        if not self.running:
            try:
                # Start the visualizer script as a new process
                self.process = multiprocessing.Process(
                    target=self.joystick_function, args=(config,)
                )
                self.process.start()
                self.running = True
            except Exception as e:
                print(f"Error starting joystick process: {e}")

    def stop_visualizer(self):
        if self.running and self.process:
            try:
                # Terminate the process
                self.process.terminate()
                self.process.join()  # Wait for the process to finish
                self.process = None
                self.running = False
            except Exception as e:
                print(f"Error stopping joystick process: {e}")

    def retrieve_data(self):
        while not self.queue.empty():
            print(self.queue.get())

    def send_data(self, data):
        self.queue.put(data)


if __name__ == "__main__":
    print("Starting worker runner")
    config = Config()
    visualizer_process = Visualizer_Process()
    # visualizer_process.run_visualizer(config)

    joystick_process = Joystick_Process()
    joystick_process.run_joystick(config)
