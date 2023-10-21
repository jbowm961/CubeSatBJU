import os
import sys
import serial
import time as clock
from PyQt5 import uic
from PyQt5 import QtGui
from PyQt5 import QtCore
from guiThreading import *
from datetime import datetime
from avionicsClasses import *
import serial.tools.list_ports

port = "COM4"

available_ports = list(serial.tools.list_ports.comports())

print([comport.device for comport in serial.tools.list_ports.comports()])

if port is not None:

    ser = serial.Serial(port, 9600, timeout=0.5, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)

    self.terminal.append("~~~ Connection Made '" + str(port) + "' ~~~\n")
    print("~~~ Connection Made '" + str(port) + "' ~~~\n")
    CONNECTION = True
