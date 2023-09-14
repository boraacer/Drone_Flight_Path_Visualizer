import math
from pygame.locals import *
import pygame
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluPerspective

display = (1920, 1200)


class Config:
    def __init__(self, filename="config.txt"):
        # Default values
        self.fps = 60
        self.resolution = (1920, 1200)
        self.fullscreen = True

        # Read from file
        self._load_from_file(filename)

    def _load_from_file(self, filename):
        try:
            with open(filename, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("FPS="):
                        self.fps = int(line.split("=")[1].strip())
                    elif line.startswith("RESOLUTION="):
                        res = line.split("=")[1].strip().split("x")
                        self.resolution = (int(res[0]), int(res[1]))
                    elif line.startswith("FULLSCREEN="):
                        self.fullscreen = line.split("=")[1].strip().lower() == "true"
        except Exception as e:
            print(f"Error loading config: {e}")


class OpenGLViewport:
    def __init__(self, resolution):
        self.resolution = resolution
        # Adjust the OpenGL viewport to use only the top 80% of the window
        glViewport(
            0,
            int(0 * self.resolution[1]),
            self.resolution[0],
            int(1 * self.resolution[1]),
        )
        gluPerspective(45, (self.resolution[0] / (1 * self.resolution[1])), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)

    def render(self):
        glRotatef(1, 3, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        



class TextRenderer:
    def __init__(self, resolution):
        self.resolution = resolution

    def render(self, text_list):
        # Render text using OpenGL
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.resolution[0], 0, self.resolution[1], -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw the line 60% down the screen
        line_position = int(0.4 * display[1])
        draw_line(line_position)
        
        # Render the artificial horizon
        draw_artificial_horizon(display[0] // 2, int(0.2 * display[1]), roll_angle=0, pitch_angle=0)


        
        # Display each text entry in the list
        for text_entry in text_list:
            x, y, text = text_entry
            render_text(x, y, text)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)




def draw_line(y_position):
    glColor3f(1, 1, 1)  # Set line color to white
    glBegin(GL_LINES)
    glVertex2f(0, y_position)
    glVertex2f(display[0], y_position)
    glEnd()

def draw_artificial_horizon(x, y, roll_angle, pitch_angle, radius=100):
    """
    Draw an accurate artificial horizon with the ball rotating and pitch markings.
    """
    # Calculate the y offset for pitch
    pitch_offset = pitch_angle * (radius / 30)

    # Set up rotation and translation
    glPushMatrix()
    glTranslatef(x, y, 0)
    glRotatef(roll_angle, 0, 0, 1)  # Rotate around Z-axis

    # Draw sky (blue half)
    glColor3f(0.53, 0.808, 0.980)
    glBegin(GL_POLYGON)
    for i in range(0, 181):
        angle = i
        dx = radius * math.cos(math.radians(angle))
        dy = radius * math.sin(math.radians(angle)) + pitch_offset
        glVertex2f(dx, dy)
    glEnd()

    # Draw ground (brown half)
    glColor3f(0.545, 0.271, 0.075)
    glBegin(GL_POLYGON)
    for i in range(180, 361):
        angle = i
        dx = radius * math.cos(math.radians(angle))
        dy = radius * math.sin(math.radians(angle)) + pitch_offset
        glVertex2f(dx, dy)
    glEnd()

    # Draw pitch markings
    glColor3f(1, 1, 1)
    for offset in range(0, radius+1, int(radius / 30)):  # Every 1 degree
        length = radius * 0.05 if offset % (2*int(radius / 30)) else radius * 0.1  # Longer lines every 2 degrees
        glBegin(GL_LINES)
        glVertex2f(-length, offset)
        glVertex2f(length, offset)
        glVertex2f(-length, -offset)
        glVertex2f(length, -offset)
        glEnd()

    glPopMatrix()

    # Draw outer boundary circle
    glColor3f(1, 1, 1)
    glBegin(GL_LINE_LOOP)
    for i in range(360):
        dx = radius * math.cos(math.radians(i))
        dy = radius * math.sin(math.radians(i))
        glVertex2f(x + dx, y + dy)
    glEnd()

    # Draw central aircraft marker
    glBegin(GL_LINES)
    glVertex2f(x - radius * 0.1, y)
    glVertex2f(x + radius * 0.1, y)
    glVertex2f(x, y - radius * 0.1)
    glVertex2f(x, y + radius * 0.1)
    glEnd()







def render_text(x, y, text):
    glColor3f(1, 1, 1)  # Set color to white
    glRasterPos2f(x, y)
    for character in text:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(character))


def main():
    config = Config()
    display = config.resolution

    if config.fullscreen:
        pygame.display.set_mode(display, DOUBLEBUF | OPENGL | FULLSCREEN)
    else:
        pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.font.init()

    opengl_viewport = OpenGLViewport(display)
    text_renderer = TextRenderer(display)

    # Create a Clock object to limit and measure the frame rate
    clock = pygame.time.Clock()
    target_fps = config.fps

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        opengl_viewport.render()

        # Create a list of text entries: (x, y, text)
        text_entries = [
            (10, int(0.1 * display[1]), "Sample Data Here"),
            (10, display[1] - 20, f"FPS: {clock.get_fps():.2f}"),
        ]
        text_renderer.render(text_entries)

        pygame.display.flip()

        # Limit the frame rate
        clock.tick(target_fps)
