import os
import serial


def find_serial():
    filtered_list = []
    if os.name == "posix" and os.uname().sysname == "Darwin":  # Check if it's a Mac
        path = "/dev/"

        try:
            dir_list = os.listdir(path)
            filtered_list = [item for item in dir_list if item.startswith("tty.")]
            print(filtered_list)

        except PermissionError:
            print(f"Permission denied for directory: {path}")

    else:  # For Windows or other OS
        print("Windows or other OS detected which is not supported yet.")
    return filtered_list


class Radio_Data:
    def __init__(self):
        self.pitch = 0
        self.roll = 0
        self.yaw = 0
        self.throttle = 0

    def set(self, pitch, roll, yaw, throttle):
        self.pitch = pitch
        self.roll = roll
        self.yaw = yaw
        self.throttle = throttle

    def __str__(self) -> str:
        return f"Pitch: {self.pitch}, Roll: {self.roll}, Yaw: {self.yaw}, Throttle: {self.throttle}"


class Connection:
    def __init__(self, config, baudrate=9600):
        self.port = config.serialport
        self.baudrate = baudrate
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 1
        self.ser = serial.Serial()

        self.open()

    def open(self):
        if os.name == "posix" and os.uname().sysname == "Darwin":
            self.ser.port = f"/dev/{self.port}"
        else: 
            print("Windows or other OS detected which is not supported yet.")

        self.ser.baudrate = self.baudrate
        self.ser.bytesize = self.bytesize
        self.ser.parity = self.parity
        self.ser.stopbits = self.stopbits
        self.ser.timeout = self.timeout

        self.ser.open()

        if self.ser.is_open:
            print("Serial connection is open!")
        else:
            print("Failed to open the serial connection.")

    def close(self):
        self.ser.close()

    def send(self, data):
        self.ser.write(data.encode("utf-8") + b"\r\n")
        print(f"Sent: {data}")

    def receive(self):
        data = self.ser.readline()
        print(f"Received: {data}")
        return data


def main(config, data, lock):
    radio = Connection(config)

    while True:
        with lock:
            radio.send(data.get_axis())
            data["radio"] = radio.receive()
            print(data)
