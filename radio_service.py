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


class Connection:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 1
        self.ser = serial.Serial()

        self.open()

    def open(self):
        self.ser.port = self.port
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




