import pygame

pygame.init()

# Get the number of connected joysticks
joystick_count = pygame.joystick.get_count()

# Print the number of connected joysticks
print("Number of joysticks detected: {}".format(joystick_count))

# Initialize the first joystick
if joystick_count > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print("Joystick ID: {}".format(joystick.get_id()))
else:
    print("No joysticks detected.")