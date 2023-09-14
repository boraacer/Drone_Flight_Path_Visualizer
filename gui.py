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
            int(0.2 * self.resolution[1]),
            self.resolution[0],
            int(0.8 * self.resolution[1]),
        )
        gluPerspective(45, (self.resolution[0] / (0.8 * self.resolution[1])), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)

    def render(self):
        glRotatef(1, 3, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_cube(0.5)


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
        line_position = int(0.2 * display[1])
        draw_line(line_position)
        
        # Display each text entry in the list
        for text_entry in text_list:
            x, y, text = text_entry
            render_text(x, y, text)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


def draw_cube(scale_factor=1.0):
    # Define vertices for a cube
    vertices = (
        (1, -1, -1),
        (1, 1, -1),
        (-1, 1, -1),
        (-1, -1, -1),
        (1, -1, 1),
        (1, 1, 1),
        (-1, -1, 1),
        (-1, 1, 1),
    )

    # Define edges that connect the vertices to form the cube
    edges = (
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    )
    glPushMatrix()  # Save the current matrix state

    # Apply the scaling transformation
    glScalef(scale_factor, scale_factor, scale_factor)

    # Original cube drawing code
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()

    glPopMatrix()


def draw_line(y_position):
    glColor3f(1, 1, 1)  # Set line color to white
    glBegin(GL_LINES)
    glVertex2f(0, y_position)
    glVertex2f(display[0], y_position)
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
