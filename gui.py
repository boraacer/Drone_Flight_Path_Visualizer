import math
from pygame.locals import *
import pygame
from PIL import Image
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluPerspective

display = (1920, 1200)


def load_texture(filename):
    """
    Load an image file as an OpenGL texture.
    """
    image = Image.open(filename)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)

    # Create a new OpenGL texture
    tex_id = glGenTextures(1)

    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        GL_RGBA,
        image.width,
        image.height,
        0,
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        image.tobytes("raw", "RGBA"),
    )
    glBindTexture(GL_TEXTURE_2D, 0)

    return tex_id


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

    def render(self, text_list, textures):
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
        draw_artificial_horizon(
            display[0] // 2,
            int(0.2 * display[1]),
            textures,
            roll_angle=0,
            pitch_angle=0,
            yaw_angle=0,
            radius=150,
        )

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


def draw_artificial_horizon(
    x, y, textures, roll_angle, pitch_angle, yaw_angle, radius=100
):
    """
    Draw the textures for frame, interior, and ring with pitch transformations applied to the interior.
    The scale_factor is used to scale up the Interior texture.
    """

    # Ensure textures are provided
    if not textures or 'Frame' not in textures or 'Interior' not in textures or 'Ring' not in textures:
        raise ValueError("Provide textures for Frame, Interior, and Ring")

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_DEPTH_TEST)

    # Set up the stencil buffer
    glEnable(GL_STENCIL_TEST)
    glClear(GL_STENCIL_BUFFER_BIT)

    # Draw the masking shape (circle)
    glStencilFunc(GL_ALWAYS, 1, 0xFF)
    glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
    glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)

    glBegin(GL_POLYGON)
    for i in range(360):
        angle = i
        dx = x + radius * math.cos(math.radians(angle))
        dy = y + radius * math.sin(math.radians(angle))
        glVertex2f(dx, dy)
    glEnd()

    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    # Adjust pitch translation based on scaling and radius
    adjusted_pitch = -1 * pitch_angle * (radius / 100.0) * 1.35

    # Render the Interior image with pitch transformation and masking
    glStencilFunc(GL_EQUAL, 1, 0xFF)
    glStencilMask(0x00)

    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(2, 2, 1)
    glTranslatef(0, adjusted_pitch, 0)

    glBindTexture(GL_TEXTURE_2D, textures['Interior'])
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(-radius, -radius)
    glTexCoord2f(1, 0); glVertex2f(radius, -radius)
    glTexCoord2f(1, 1); glVertex2f(radius, radius)
    glTexCoord2f(0, 1); glVertex2f(-radius, radius)
    glEnd()
    glPopMatrix()

    # Render the Frame with roll transformation
    glPushMatrix()
    glTranslatef(x, y, 0)
    glRotatef(roll_angle, 0, 0, 1)

    glBindTexture(GL_TEXTURE_2D, textures['Frame'])
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(-radius, -radius)
    glTexCoord2f(1, 0); glVertex2f(radius, -radius)
    glTexCoord2f(1, 1); glVertex2f(radius, radius)
    glTexCoord2f(0, 1); glVertex2f(-radius, radius)
    glEnd()
    glPopMatrix()

    # Render the Ring without any transformations
    glBindTexture(GL_TEXTURE_2D, textures['Ring'])
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x - radius, y - radius)
    glTexCoord2f(1, 0); glVertex2f(x + radius, y - radius)
    glTexCoord2f(1, 1); glVertex2f(x + radius, y + radius)
    glTexCoord2f(0, 1); glVertex2f(x - radius, y + radius)
    glEnd()

    glBindTexture(GL_TEXTURE_2D, 0)  # Unbind texture

    # Disable the stencil test
    glDisable(GL_STENCIL_TEST)

    draw_yaw_slider(x, y - radius - 30, yaw_angle)
    draw_pitch_slider(x - radius - 30, y, pitch_angle)


def draw_pitch_slider(x, y, pitch_angle, width=20, height=240):
    """
    Draw the pitch slider next to the artificial horizon with moving numbers based on pitch angle.
    """
    # Draw slider background
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_QUADS)
    glVertex2f(x - width, y - height / 2)
    glVertex2f(x, y - height / 2)
    glVertex2f(x, y + height / 2)
    glVertex2f(x - width, y + height / 2)
    glEnd()

    # Draw slider position (centered)
    glColor3f(1, 0, 0)  # Red color for the slider position
    glRectf(x - width, y - 5, x, y + 5)

    # Draw numbered indicators, moving based on pitch
    font = pygame.font.Font(None, 24)
    spacing = height / 6  # Adjust as needed

    # Calculate the starting and ending values based on the pitch angle
    start_val = int((pitch_angle - 2.5 * spacing) // 10) * 10  # Adjusted for 5 numbers
    end_val = int((pitch_angle + 2.5 * spacing) // 10) * 10  # Adjusted for 5 numbers

    for i in range(start_val, end_val + 10, 10):
        pos_y = y + (i - pitch_angle) * spacing / 10
        if y - height / 2 - spacing < pos_y < y + height / 2 + spacing:
            glBegin(GL_LINES)
            glVertex2f(x - width, pos_y)
            glVertex2f(x - width + 10, pos_y)
            glEnd()

            text_surface = font.render(str(i), True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)

            # Enable blending
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            glRasterPos2f(
                x - width - text_surface.get_width() - 5,
                pos_y - text_surface.get_height() / 2,
            )
            glDrawPixels(
                text_surface.get_width(),
                text_surface.get_height(),
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                text_data,
            )

            # Disable blending
            glDisable(GL_BLEND)


def draw_yaw_slider(x, y, yaw_angle, width=240, height=20):
    """
    Draw the yaw slider below the artificial horizon with moving numbers based on yaw angle.
    """
    # Draw slider background
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_QUADS)
    glVertex2f(x - width / 2, y - height)
    glVertex2f(x + width / 2, y - height)
    glVertex2f(x + width / 2, y)
    glVertex2f(x - width / 2, y)
    glEnd()

    # Draw slider position (centered)
    glColor3f(1, 0, 0)  # Red color for the slider position
    glRectf(x - 5, y - height, x + 5, y)

    # Draw numbered indicators, moving based on yaw
    font = pygame.font.Font(None, 24)
    spacing = width / 6  # Adjust as needed

    # Calculate the starting and ending values based on the yaw angle
    start_val = int((yaw_angle - 2.5 * spacing) // 10) * 10  # Adjusted for 5 numbers
    end_val = int((yaw_angle + 2.5 * spacing) // 10) * 10  # Adjusted for 5 numbers

    for i in range(start_val, end_val + 10, 10):
        pos_x = x + (i - yaw_angle) * spacing / 10
        if x - width / 2 - spacing < pos_x < x + width / 2 + spacing:
            glBegin(GL_LINES)
            glVertex2f(pos_x, y - height)
            glVertex2f(pos_x, y - height + 10)
            glEnd()

            text_surface = font.render(str(i), True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)

            # Enable blending
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            glRasterPos2f(
                pos_x - text_surface.get_width() / 2,
                y - height - text_surface.get_height() - 5,
            )
            glDrawPixels(
                text_surface.get_width(),
                text_surface.get_height(),
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                text_data,
            )

            # Disable blending
            glDisable(GL_BLEND)


def render_text(x, y, text):
    glColor3f(1, 1, 1)  # Set color to white
    glRasterPos2f(x, y)
    for character in text:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(character))


def main():
    config = Config()
    display = config.resolution

    pygame.display.gl_set_attribute(
        pygame.GL_STENCIL_SIZE, 8
    )  # Requesting 8-bit stencil buffer

    if config.fullscreen:
        pygame.display.set_mode(
            display,
            DOUBLEBUF | OPENGL | FULLSCREEN | pygame.OPENGLBLIT | pygame.DOUBLEBUF,
        )
    else:
        pygame.display.set_mode(
            display, DOUBLEBUF | OPENGL | pygame.OPENGLBLIT | pygame.DOUBLEBUF
        )
    pygame.font.init()

    # Load textures from the assets folder
    textures = {
        "Frame": load_texture("assets/Frame.png"),
        "Interior": load_texture("assets/Interior.png"),
        "Ring": load_texture("assets/Ring.png"),
    }

    opengl_viewport = OpenGLViewport(display)
    text_renderer = TextRenderer(display)

    # Create a Clock object to limit and measure the frame rate
    clock = pygame.time.Clock()
    target_fps = config.fps

    while True:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
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
        text_renderer.render(text_entries, textures)

        pygame.display.flip()

        # Limit the frame rate
        clock.tick(target_fps)
