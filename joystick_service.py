import os
from pygame import joystick

# Initialize joystick subsystem
joystick.init()


def get_joystick_list():
    joystick_list = []

    # Check for joysticks
    joystick_count = joystick.get_count()
    if joystick_count == 0:
        print("Error, no joysticks found")
    else:
        for i in range(joystick_count):
            js = joystick.Joystick(0)
            os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
            js.init()
            # Now you can use joystick functions
            name = js.get_name()
            joystick_list.append({"id": i, "name": name})
    print(joystick_list)
    return joystick_list


