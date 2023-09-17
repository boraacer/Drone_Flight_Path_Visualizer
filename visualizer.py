import json
import math
import time
from pygame.locals import *
import pygame
from PIL import Image
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluPerspective
import websocket
import threading
import argparse


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
    def __init__(self):
        self.fps = 30
        self.resolution = (1920, 1200)
        self.fullscreen = False
        self.launcher_host = "localhost:5128"

    def parse_command_line_args(self):
        parser = argparse.ArgumentParser(
            description="Configuration options for your program"
        )

        # Define command-line arguments
        parser.add_argument("--fps", type=int, default=30, help="Frames per second")
        parser.add_argument(
            "--resolution",
            type=str,
            default="1920x1200",
            help="Screen resolution in the format WIDTHxHEIGHT",
        )
        parser.add_argument(
            "--fullscreen", action="store_true", help="Enable fullscreen mode"
        )
        parser.add_argument(
            "--launcher-host",
            type=str,
            default="localhost:5128",
            help="Launcher host address",
        )

        args = parser.parse_args()

        # Update instance variables with command-line arguments
        self.fps = args.fps
        width, height = map(int, args.resolution.split("x"))
        self.resolution = (width, height)
        self.fullscreen = args.fullscreen
        self.launcher_host = args.launcher_host

    def __str__(self):
        return f"FPS={self.fps}\nRESOLUTION={self.resolution[0]}x{self.resolution[1]}\nFULLSCREEN={'true' if self.fullscreen else 'false'}\nLAUNCHER_HOST={self.launcher_host}"


if __name__ == "__main__":
    config = Config()
    config.parse_command_line_args()
    print(config)


class WebSocketClient:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.connected = False
        self.message = ""

    def data(self):
        return json.loads(self.message)

    def on_open(self, ws):
        self.connected = True
        print("WebSocket connection opened")

    def on_message(self, ws, message):
        print(f"Received message: {message}")
        self.message = message

    def on_error(self, ws, error):
        print(f"Error occurred: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        print(f"WebSocket connection closed with code {close_status_code}: {close_msg}")

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

    def send_message(self, message):
        if self.connected:
            self.ws.send(message)
        else:
            print("WebSocket is not connected. Cannot send message.")

    def close(self):
        if self.connected:
            self.ws.close()

    def ping(self):
        if self.connected:
            start_time = time.time()
            self.ws.send("ping")
            while not self.ping_time:
                time.sleep(0.001)
            ping_time = time.time() - start_time
            self.ping_time = 0
            return f"{int(ping_time)} ms"
        else:
            return "ERROR"


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
        draw_horizontal_line(line_position)

        draw_vertical_line(0.4, display[1], 0.2 * display[0])

        PITCH = 30
        ROLL = 20
        YAW = 45

        # Render the artificial horizon
        draw_artificial_horizon(
            (display[0] // 2) - 200,
            int(0.2 * display[1]) + 30,
            textures,
            roll_angle=ROLL,
            pitch_angle=PITCH,
            yaw_angle=YAW,
            radius=150,
        )

        # Control Dials

        # Pitch Slider
        draw_vertical_slider(
            0.75 * display[0], 0.2 * display[1], PITCH, width=40, height=300
        )

        # Roll Slider
        draw_horizontal_slider(
            0.6 * display[0], 0.15 * display[1], ROLL, width=300, height=40
        )

        # Yaw Slider
        draw_horizontal_slider(
            0.6 * display[0], 0.25 * display[1], YAW, width=300, height=40
        )

        # Display each text entry in the list
        for text_entry in text_list:
            x, y, text, color = text_entry

            render_text(x, y, text, color)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


def draw_horizontal_line(y_position):
    glColor3f(1, 1, 1)  # Set line color to white
    glBegin(GL_LINES)
    glVertex2f(0, y_position)
    glVertex2f(display[0], y_position)
    glEnd()


def draw_vertical_line(stop_percentage, window_height, x_position):
    """
    Draws a vertical line that starts at the bottom of the screen and stops
    at a specified percentage up the screen.

    Args:
    - stop_percentage (float): The percentage up the screen where the line should stop. In this case, 0.4 for 40%.
    - window_height (int): The height of the window or screen.
    - x_position (int): The x position where the line should be drawn.
    """
    start_y = 0  # Start at the bottom of the screen
    end_y = window_height * stop_percentage  # Calculate end point based on percentage

    # OpenGL commands to draw the line
    glColor3f(1, 1, 1)  # White color
    glBegin(GL_LINES)
    glVertex2f(x_position, start_y)
    glVertex2f(x_position, end_y)
    glEnd()


def draw_artificial_horizon(
    x, y, textures, roll_angle, pitch_angle, yaw_angle, radius=100
):
    """
    Draw the textures for frame, interior, and ring with pitch transformations applied to the interior.
    The scale_factor is used to scale up the Interior texture.
    """

    # Ensure textures are provided
    if (
        not textures
        or "Frame" not in textures
        or "Interior" not in textures
        or "Ring" not in textures
    ):
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

    glBindTexture(GL_TEXTURE_2D, textures["Interior"])
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(-radius, -radius)
    glTexCoord2f(1, 0)
    glVertex2f(radius, -radius)
    glTexCoord2f(1, 1)
    glVertex2f(radius, radius)
    glTexCoord2f(0, 1)
    glVertex2f(-radius, radius)
    glEnd()
    glPopMatrix()

    # Render the Frame with roll transformation
    glPushMatrix()
    glTranslatef(x, y, 0)
    glRotatef(roll_angle, 0, 0, 1)

    glBindTexture(GL_TEXTURE_2D, textures["Frame"])
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(-radius, -radius)
    glTexCoord2f(1, 0)
    glVertex2f(radius, -radius)
    glTexCoord2f(1, 1)
    glVertex2f(radius, radius)
    glTexCoord2f(0, 1)
    glVertex2f(-radius, radius)
    glEnd()
    glPopMatrix()

    # Render the Ring without any transformations
    glBindTexture(GL_TEXTURE_2D, textures["Ring"])
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(x - radius, y - radius)
    glTexCoord2f(1, 0)
    glVertex2f(x + radius, y - radius)
    glTexCoord2f(1, 1)
    glVertex2f(x + radius, y + radius)
    glTexCoord2f(0, 1)
    glVertex2f(x - radius, y + radius)
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


def draw_vertical_slider(x, y, pitch_angle, width=20, height=240):
    """
    Draw the pitch slider next to the artificial horizon with static numbers based on a fixed pitch range (-100 to 100).
    Additionally, display the current pitch_angle value above the slider.
    """
    # Draw slider background
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_QUADS)
    glVertex2f(x - width, y - height / 2)
    glVertex2f(x, y - height / 2)
    glVertex2f(x, y + height / 2)
    glVertex2f(x - width, y + height / 2)
    glEnd()

    # Calculate the slider's vertical position based on pitch_angle
    font = pygame.font.Font(None, 24)
    spacing = (
        height / 20
    )  # Divided by 20 since there are 20 intervals (from -100 to 100 in steps of 10)
    slider_position_y = y + (pitch_angle * spacing / 10)

    # Draw slider position (centered) based on pitch_angle
    glColor3f(1, 0, 0)  # Red color for the slider position
    glRectf(x - width, slider_position_y - 5, x, slider_position_y + 5)

    # Draw static numbered indicators, with fixed range from -100 to 100
    for i in range(-100, 110, 10):  # 110 is used so 100 is included
        pos_y = y + (i * spacing / 10)

        # Draw the line indicator
        glBegin(GL_LINES)
        glVertex2f(x - width, pos_y)
        glVertex2f(x - width + 10, pos_y)
        glEnd()

        # Draw the number
        text_surface = font.render(str(i), True, (255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)

        # Enable blending for text rendering
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

    # Display the current pitch_angle value above the slider
    pitch_angle_str = "{:.2f}".format(pitch_angle)

    # Color based on the value of pitch_angle
    if pitch_angle > 0:
        text_color = (0, 255, 0)  # Green
    elif pitch_angle < 0:
        text_color = (255, 0, 0)  # Red
    else:
        text_color = (0, 255, 255)  # Blue

    pitch_angle_surface = font.render(pitch_angle_str, True, text_color)
    pitch_angle_data = pygame.image.tostring(pitch_angle_surface, "RGBA", True)

    # Calculate position for the text
    text_x = (x - width - pitch_angle_surface.get_width() / 2) + 20
    text_y = (y + height / 2) + 5

    # Render the outline by drawing the text multiple times with slight offsets
    outline_color = (0, 0, 0)  # Black for the outline
    offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    for offset_x, offset_y in offsets:
        outline_surface = font.render(pitch_angle_str, True, outline_color)
        outline_data = pygame.image.tostring(outline_surface, "RGBA", True)

        glRasterPos2f(text_x + offset_x, text_y + offset_y)
        glDrawPixels(
            pitch_angle_surface.get_width(),
            pitch_angle_surface.get_height(),
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            outline_data,
        )

    # Render the main text over the outline
    glRasterPos2f(text_x, text_y)
    glDrawPixels(
        pitch_angle_surface.get_width(),
        pitch_angle_surface.get_height(),
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        pitch_angle_data,
    )

    glDisable(GL_BLEND)


def draw_horizontal_slider(x, y, pitch_angle, width=240, height=20):
    """
    Draw the horizontal pitch slider next to the artificial horizon with numbers based on pitch angle.
    """
    # Ensure pitch_angle is clamped between -100 and 100
    pitch_angle = max(-100, min(100, pitch_angle))

    # Draw slider background
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_QUADS)
    glVertex2f(x - width / 2, y - height)
    glVertex2f(x + width / 2, y - height)
    glVertex2f(x + width / 2, y)
    glVertex2f(x - width / 2, y)
    glEnd()

    # Calculate position for the red bar based on pitch_angle
    pos_x = x + (pitch_angle * (width / 2) / 100)

    # Draw slider position (centered)
    glColor3f(1, 0, 0)  # Red color for the slider position
    glRectf(pos_x - 5, y - height, pos_x + 5, y)

    # Draw numbered indicators
    font = pygame.font.Font(None, 24)
    spacing = width / 10  # Adjust as needed for intervals of 20

    for i in range(-100, 120, 20):  # From -100 to 100 in steps of 20
        pos_x_indicator = x + (i * width / 200)
        glBegin(GL_LINES)
        glVertex2f(pos_x_indicator, y - height)
        glVertex2f(pos_x_indicator, y - height + 10)
        glEnd()

        text_surface = font.render(str(i), True, (255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)

        # Enable blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glRasterPos2f(
            pos_x_indicator - text_surface.get_width() / 2,
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

    # Display the current pitch_angle value above the slider
    pitch_angle_str = "{:.2f}".format(pitch_angle)
    if pitch_angle > 0:
        text_color = (0, 255, 0)  # Green
    elif pitch_angle < 0:
        text_color = (255, 0, 0)  # Red
    else:
        text_color = (0, 255, 255)  # Blue

    pitch_angle_surface = font.render(pitch_angle_str, True, text_color)
    pitch_angle_data = pygame.image.tostring(pitch_angle_surface, "RGBA", True)

    # Calculate position for the text (above the slider)
    text_x = x - pitch_angle_surface.get_width() / 2
    text_y = (y - height - pitch_angle_surface.get_height() - 10) + 75

    # Render the text
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glRasterPos2f(text_x, text_y)
    glDrawPixels(
        pitch_angle_surface.get_width(),
        pitch_angle_surface.get_height(),
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        pitch_angle_data,
    )
    glDisable(GL_BLEND)


from OpenGL.GLUT import GLUT_BITMAP_8_BY_13


def render_text(x, y, text, color):
    glColor3f(*color)
    glRasterPos2f(x, y)
    for character in text:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(character))


def status_text(renderer, textures, clock, connection):
    def status_color(status):
        if status == "ERROR":
            return (255, 0, 0)  # Red
        return (0, 255, 0)  # Green

    Status_X_Pos = int(0.35 * display[1]) + 37
    text_entries = [
        (10, Status_X_Pos - 0, "Launcher Connection:", (255, 255, 255)),
        (300, Status_X_Pos - 0, connection.ping(), status_color(connection.ping())),
        (10, Status_X_Pos - 15, "   Joystick Connection: ", (255, 255, 255)),
        (300, Status_X_Pos - 15, "OK", status_color("OK")),
        (10, Status_X_Pos - 30, "   Radio Service Connection:", (255, 255, 255)),
        (300, Status_X_Pos - 30, "OK", status_color("OK")),
        (10, Status_X_Pos - 45, "       Drone Connection:", (255, 255, 255)),
        (300, Status_X_Pos - 45, "OK", status_color("OK")),
    ]

    text_entries.append(
        (10, display[1] - 20, f"FPS: {clock.get_fps():.2f}", (0, 255, 0))
    )
    renderer.render(text_entries, textures)


def main():
    pygame.init()
    pygame.display.set_icon(pygame.image.load("assets/Visualizer_Icon.png"))

    config = Config()
    config.parse_command_line_args()
    
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

    # Create a WebSocketClient object to connect to the launcher
    launcherConnection = WebSocketClient(f"ws://{config.launcher_host}/client")
    running = True
    opengl_viewport.render()
    while running:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        status_text(text_renderer, textures, clock, launcherConnection)

        pygame.display.flip()

        # Limit the frame rate
        clock.tick(target_fps)


main()
