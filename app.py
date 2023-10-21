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

filterCallSigns = False
callsigns = []

currentLatLong = [34.87664,82.36091]
satMap = None

log_file = "log.txt"

commandHistory = [""]
selectedCommand = 0

ser = None
CONNECTION = False

if not os.path.isfile(log_file):
    with open(log_file, "w") as file:
        pass

callsignSetup = True

while callsignSetup:

    print("")

    if not filterCallSigns:
        promptInput = input("Would you like to filter data by callsign? (y/n): ")
    else:
        promptInput = input("Would you like to add another callsign to the filter? (y/n): ")

    if "n" in promptInput:

        callsignSetup = False

    elif "y" in promptInput:

        filterCallSigns = True

        callsignInput = input("Please enter a callsign (case sensitive): ")
        callsigns.append(callsignInput)

    else:

        print("ENTRY NOT UNDERSTOOD")

print("")

# Main Application Class
class UI(QMainWindow):

    # Displays key data points
    def key_data_display(self, data):

        self.altitudeDisplay.setText(str(data.GPS.Altitude) + " M")
        self.speedDisplay.setText(str(data.GPS.Speed) + " m/s")

        self.temperatureDisplay.setText(str(data.ALTIMETER.Temperature) + " °C")

    # Decodes Received Data
    def data_decode(self):

        if CONNECTION:

            try:

                data = AVIONICSDATA(None, None, None, None, None, None, None, None, None, None)

                try:

                    packet = ser.read(960)

                except:

                    packet = b''

                if packet != b'':

                    temp_byte_data = str(packet)
                    self.byteData.append(temp_byte_data + "\n")

                    callsign_length = 0

                    try:

                        for i in range(0, len(packet)):

                            try:
                                temp_callsign = packet[0:i].decode("ascii")
                            except:
                                print(packet[0:i].decode("ascii"))
                                break

                            if temp_callsign[-1:] == " ":
                                break

                            callsign_length += 1

                    except:

                        callsign_length = callsign_length - 2

                    callsign = packet[0:callsign_length].decode("ascii")
                    print("Call: " + callsign + "\n")

                    if not filterCallSigns or callsign.replace(" ", "") in callsigns:

                        packet = packet[callsign_length:]

                        if len(packet) == 98:

                            # Date & Time
                            if (int.from_bytes(packet[0:2], "big", signed=True)) != 0:

                                data.TIME = datetime(int.from_bytes(packet[0:2], "big", signed=True),
                                                     int.from_bytes(packet[2:3], "big", signed=True),
                                                     int.from_bytes(packet[3:4], "big", signed=True),
                                                     int.from_bytes(packet[4:5], "big", signed=True),
                                                     int.from_bytes(packet[5:6], "big", signed=True),
                                                     int.from_bytes(packet[6:7], "big", signed=True))

                            else:

                                data.TIME = int.from_bytes(packet[0:7], "big", signed=True)

                            # GPS
                            data.GPS = GPS((int.from_bytes(packet[7:11], "big", signed=True))/10000000,
                                           (int.from_bytes(packet[11:15], "big", signed=True))/10000000,
                                           (int.from_bytes(packet[15:19], "big", signed=True))/100,
                                           (int.from_bytes(packet[19:22], "big", signed=True))/100,
                                           (int.from_bytes(packet[22:23], "big", signed=True)),
                                           (int.from_bytes(packet[23:25], "big", signed=True))/100)

                            # Altimeter
                            data.ALTIMETER = ALTIMETER((int.from_bytes(packet[25:29], "big", signed=True))/100,
                                                       (int.from_bytes(packet[29:31], "big", signed=True))/100,
                                                       (int.from_bytes(packet[31:34], "big", signed=True))/100,
                                                       (int.from_bytes(packet[34:36], "big", signed=True))/100,
                                                       (int.from_bytes(packet[36:38], "big", signed=True))/100)

                            # Accelerometer
                            data.ACCELEROMETER = ACCELEROMETER((int.from_bytes(packet[38:40], "big", signed=True))/100,
                                                               (int.from_bytes(packet[40:42], "big", signed=True))/100,
                                                               (int.from_bytes(packet[42:44], "big", signed=True))/100)

                            # Gyroscope
                            data.GYROSCOPE = GYROSCOPE((int.from_bytes(packet[44:46], "big", signed=True))/100,
                                                       (int.from_bytes(packet[46:48], "big", signed=True))/100,
                                                       (int.from_bytes(packet[48:50], "big", signed=True))/100)

                            # Magnetometer
                            data.MAGNETOMETER = MAGNETOMETER((int.from_bytes(packet[50:52], "big", signed=True)) / 100,
                                                             (int.from_bytes(packet[52:54], "big", signed=True)) / 100,
                                                             (int.from_bytes(packet[54:56], "big", signed=True)) / 100)

                            # Power Draw
                            data.POWERDRAW = POWER((int.from_bytes(packet[56:58], "big", signed=True))/1000,
                                                   (int.from_bytes(packet[58:60], "big", signed=True))/1000,
                                                   (int.from_bytes(packet[60:62], "big", signed=True))/1000)

                            # Solar Panel
                            data.SOLARPANEL = SOLARPANEL(POWER((int.from_bytes(packet[62:64], "big", signed=True))/1000,
                                                               (int.from_bytes(packet[64:66], "big", signed=True))/1000,
                                                               (int.from_bytes(packet[66:68], "big", signed=True))/1000),
                                                         POWER((int.from_bytes(packet[68:70], "big", signed=True))/1000,
                                                               (int.from_bytes(packet[70:72], "big", signed=True))/1000,
                                                               (int.from_bytes(packet[72:74], "big", signed=True))/1000),
                                                         POWER((int.from_bytes(packet[74:76], "big", signed=True))/1000,
                                                               (int.from_bytes(packet[76:78], "big", signed=True))/1000,
                                                               (int.from_bytes(packet[78:80], "big", signed=True))/1000))

                            # Battery
                            data.BATTERY = BATTERY(((int.from_bytes(packet[80:82], "big", signed=True))/100),
                                                   ((int.from_bytes(packet[82:84], "big", signed=True))/100))

                            # Analog
                            data.ANALOG = ANALOG(((int.from_bytes(packet[84:86], "big", signed=True))/100),
                                                 ((int.from_bytes(packet[86:88], "big", signed=True))/100),
                                                 ((int.from_bytes(packet[88:90], "big", signed=True))/100),
                                                 ((int.from_bytes(packet[90:92], "big", signed=True))/100),
                                                 ((int.from_bytes(packet[92:94], "big", signed=True))/100),
                                                 ((int.from_bytes(packet[94:96], "big", signed=True))/100),
                                                 ((int.from_bytes(packet[96:98], "big", signed=True))/100))

                            temp_processed_data = "Callsign: " + callsign + "\n" + str(data) + "\n"

                            self.processedData.append(temp_processed_data)

                            now = datetime.now()
                            current_time = now.strftime("%H:%M:%S")

                            # Open the file in append mode
                            with open(log_file, "a") as log:
                                log.write(f'{current_time} - [Received] {str(temp_processed_data)}\n')  # Write content to the file

                            self.terminal.append("[Received] {Data Packet}")

                            self.key_data_display(data)

                        else:

                            temp_beacon_data = callsign + " " + str(packet.decode("ascii")) + "\n"
                            self.processedData.append(temp_beacon_data)

                            self.terminal.append("[Received] " + str(packet.decode("ascii")))

                            now = datetime.now()
                            current_time = now.strftime("%H:%M:%S")

                            # Open the file in append mode
                            with open(log_file, "a") as log:
                                log.write(f'{current_time} - [Received] {str(packet.decode("ascii"))}\n')  # Write content to the file

                            print(current_time + " - " + str(packet.decode("ascii")) + "\n")

            except Exception as e:

                print(e)

    # Commands/Built-in Functions
    def command_send(self):

        if str(self.commandInput.text()) != "":

            if not CONNECTION:  # Checks if Connection is False

                self.terminal.append(f'[Unsent] {self.commandInput.text()}')

                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")

                # Open the file in append mode
                with open(log_file, "a") as log:
                    log.write(f'{current_time} - [Unsent] {self.commandInput.text()}\n')  # Write content to the file

                self.commandInput.setText("")

                return  # Breaks if False

            else:

                self.terminal.append(f'[Sent] {self.commandInput.text()}')

                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")

                # Open the file in append mode
                with open(log_file, "a") as log:
                    log.write(f'{current_time} - [Sent] {self.commandInput.text()}\n')  # Write content to the file

            command = self.commandInput.text()
            commandHistory.append(command)

            self.commandInput.setText("")

            ser.write(str(command).encode("ascii"))

    def connect(self):

        global ser
        global CONNECTION

        port = "COM4"

        available_ports = list(serial.tools.list_ports.comports())
        
        for port in available_ports:
            
            if "Silicon Labs CP210x USB to UART Bridge" in str(port):
                port = port.device

        try:

            if port is not None:

                ser = serial.Serial(port, 9600, timeout=0.5, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)

                self.terminal.append("~~~ Connection Made '" + str(port) + "' ~~~\n")

                CONNECTION = True

            else:

                self.terminal.append("~~~ Error Connecting Device ~~~\n")

        except Exception as e:

            self.terminal.append("~~~ Error Connecting Device ~~~\n")
            print("Connection Error: " + str(e))

            clock.sleep(5)

    # Main UI Function for Display
    def __init__(self):

        super(UI, self).__init__()

        # Load the ui file
        uic.loadUi("large.ui", self)

        # Define the widgets

        # Buttons
        self.sendButton = self.findChild(QPushButton, "SendButton")
        self.statsButton = self.findChild(QPushButton, "Statistics")
        self.connectButton = self.findChild(QPushButton, "ConnectButton")
        self.imagesButton = self.findChild(QPushButton, "Images")
        self.dataButton = self.findChild(QPushButton, "Data")

        # Received Data Display
        self.processedData = self.findChild(QTextEdit, "ByteData")
        self.processedData.setReadOnly(True)
        self.processedData.setAlignment(QtCore.Qt.AlignCenter)
        self.processedData.setTextColor(QColor(250, 125, 80))
        self.processedData.setFont(QFont("Andale Mono", 8))
        self.byteData = self.findChild(QTextEdit, "ProcessedData")
        self.byteData.setAlignment(QtCore.Qt.AlignCenter)
        self.byteData.setReadOnly(True)
        self.byteData.setTextColor(QColor(230, 85, 175))
        self.byteData.setFont(QFont("Andale Mono", 8))

        # Status
        self.temperatureStatus = self.findChild(QTextEdit, "DistanceStatus")
        self.temperatureStatus.setReadOnly(True)
        self.temperatureDisplay = self.findChild(QLabel, "DistanceDisplay")  # Use this to update the number
        self.temperatureDisplay.setAlignment(QtCore.Qt.AlignCenter)
        self.temperatureDisplay.setFont(QFont('Inter', 15))
        self.temperatureDisplay.setText("0 °C")

        self.altitudeStatus = self.findChild(QTextEdit, "AltitudeStatus")
        self.altitudeStatus.setReadOnly(True)
        self.altitudeDisplay = self.findChild(QLabel, "AltitudeDisplay")  # Use this to update the number
        self.altitudeDisplay.setAlignment(QtCore.Qt.AlignCenter)
        self.altitudeDisplay.setFont(QFont('Inter', 15))
        self.altitudeDisplay.setText("0 M")

        self.speedStatus = self.findChild(QTextEdit, "SpeedStatus")
        self.speedStatus.setReadOnly(True)
        self.speedDisplay = self.findChild(QLabel, "SpeedDisplay")  # Use this to update the number
        self.speedDisplay.setAlignment(QtCore.Qt.AlignCenter)
        self.speedDisplay.setFont(QFont('Inter', 15))
        self.speedDisplay.setText("0 m/s")

        # Terminal
        self.terminal = self.findChild(QTextEdit, "Terminal")
        self.terminal.setReadOnly(True)
        self.terminal.setTextColor(QColor(41, 242, 20))
        self.terminal.setFont(QFont("Andale Mono", 10))

        # Text Inputs
        self.commandInput = self.findChild(QLineEdit, "Commands")

        # Send Command
        self.sendButton.clicked.connect(self.command_send)

        # Connect Command
        self.connectButton.clicked.connect(self.connect)

        # set the title
        self.setWindowTitle("Ground Station V2.6")

        self.setWindowIcon(QtGui.QIcon('IEO_Small.png'))

        # Show the Application
        self.show()

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.data_decode)
        self.timer.start()

    def keyPressEvent(self, event):

        global selectedCommand

        if event.key() == Qt.Key_Return:
            self.command_send()

        elif event.key() == Qt.Key_Escape:
            selectedCommand = 0
            self.commandInput.setText("")

        elif event.key() == Qt.Key_Up:

            selectedCommand -= 1

            if selectedCommand > 0:
                selectedCommand = 0

            elif selectedCommand < -1 * (len(commandHistory) - 1):
                selectedCommand = -1 * (len(commandHistory) - 1)

            self.commandInput.setText(commandHistory[selectedCommand])

        elif event.key() == Qt.Key_Down:

            selectedCommand += 1

            if selectedCommand > 0:
                selectedCommand = 0

            elif selectedCommand < -1 * (len(commandHistory) - 1):
                selectedCommand = -1 * (len(commandHistory) - 1)

            self.commandInput.setText(commandHistory[selectedCommand])

app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()
