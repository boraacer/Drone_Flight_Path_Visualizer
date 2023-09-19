import multiprocessing
import pygame
from launcher import Config

pygame.joystick.init()


class Joystick_Position:
    def __init__(self, joystick_id, FILTER_THRESHOLD=0.05, FILTER_FACTOR=0.9):
        self.joystick_id = joystick_id
        self.FILTER_THRESHOLD = FILTER_THRESHOLD
        self.FILTER_FACTOR = FILTER_FACTOR
        self.controller = pygame.joystick.Joystick(self.joystick_id)
        self.controller.init()
        print(
            f"Filter threshold: {self.FILTER_THRESHOLD}, filter factor: {self.FILTER_FACTOR}"
        )
        self.filtered_axis_values = {}
        self.data = {
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

    def get_axis(
        self,
        axis,
    ):
        raw_value = self.controller.get_axis(axis)
        if abs(raw_value) < self.FILTER_THRESHOLD:
            filtered_value = 0.0
        else:
            if axis not in self.filtered_axis_values:
                self.filtered_axis_values[axis] = raw_value
            else:
                self.filtered_axis_values[axis] = (
                    self.FILTER_FACTOR * self.filtered_axis_values[axis]
                    + (1 - self.FILTER_FACTOR) * raw_value
                )
            filtered_value = self.filtered_axis_values[axis]

        # Store the filtered value in self.data
        self.data[f"axis_{axis}"] = filtered_value
        return self.data

    def get_button(self, button):
        if self.controller.get_button(button) == 1:
            button_state = True
        elif self.controller.get_button(button) == 0:
            button_state = False
        button_state
        self.data[f"button_{button}"] = button_state
        return self.data


def main(config, data, lock):
    joystick_position = Joystick_Position(
        joystick_id=config.joystick,
        FILTER_THRESHOLD=config.filter_threshold,
        FILTER_FACTOR=config.filter_factor,
    )

    # Initialize the Pygame event system
    pygame.init()

    temp = {
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
    while True:
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                temp = joystick_position.get_axis(event.axis)
            if event.type == pygame.JOYBUTTONDOWN:
                temp = joystick_position.get_button(event.button)

            if event.type == pygame.JOYBUTTONUP:
                temp = joystick_position.get_button(event.button)
        with lock:
            data.clear()
            data.update(temp.copy())


def get_joystick_list():
    joystick_list = []

    # Check for joysticks
    joystick_count = pygame.joystick.get_count()
    if joystick_count == 0:
        print("Error, no joysticks found")
    else:
        for i in range(joystick_count):
            js = pygame.joystick.Joystick(0)
            js.init()
            # Now you can use joystick functions
            name = js.get_name()
            joystick_list.append({"id": i, "name": name})
    print(joystick_list)
    return joystick_list


if __name__ == "__main__":
    multiprocessing.freeze_support()
