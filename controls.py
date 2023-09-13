import pygame

# Constants for filtering joystick input
FILTER_THRESHOLD = 0.05
FILTER_FACTOR = 0.9  # Adjust this value for stronger/weaker filtering

pygame.init()
controller = pygame.joystick.Joystick(0)
controller.init()

# Initialize a dictionary to store the filtered axis values
filtered_axis_values = {}

while True:
    for event in pygame.event.get():
        if event.type == pygame.JOYAXISMOTION:
            axis = event.axis
            raw_value = event.value

            # Apply filtering to reduce small fluctuations (stick drift)
            if abs(raw_value) < FILTER_THRESHOLD:
                filtered_value = 0.0
            else:
                if axis not in filtered_axis_values:
                    filtered_axis_values[axis] = raw_value
                else:
                    filtered_axis_values[axis] = (
                        FILTER_FACTOR * filtered_axis_values[axis]
                        + (1 - FILTER_FACTOR) * raw_value
                    )
                filtered_value = filtered_axis_values[axis]

                print("Axis {} value: {:.2f}".format(axis, filtered_value))

        elif event.type == pygame.JOYBUTTONDOWN:
            print("Button {} down".format(event.button))
        elif event.type == pygame.JOYBUTTONUP:
            print("Button {} up".format(event.button))
