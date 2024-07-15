import serial
from serial.tools import list_ports
import threading
import time,datetime

COMMAND_BUFFER_MAX = 5
event = threading.Event()
command_buffer = 0

ser = serial.Serial("/dev/cu.wchusbserial120", 115200) 
ser.timeout = 1
ser.write_timeout = 1

if __name__ == '__main__':
    ser.write(bytes("G28\r",'utf-8'))
    