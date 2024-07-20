'''
Script to test options for forcing a stop to a Pico process over serial.
'''
import time
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import devices
import move
import main

import motor_connection

PORT = 'COM5'
BAUD = 115200

def initialize():
    motor_connection.motor_connection()
    global mcu
    mcu = devices.ControllerConnection(PORT,BAUD)
    main.setup_devices(mcu)

def test_call():
    move.talk_to_actuator(mcu,"X")

def test_stop():
    print("Moving gauge back to clear sample stage.")
    move.move_gauge_backward_dist(mcu,4000,wait_for_completion=False)
    print("out of move function.")
    time.sleep(5)
    #move.talk_to_actuator(mcu,"X")

def serial_stop():
    initialize()
    test_call()
    mcu.close()
    print("SUCCESS: motor stop passed")

if __name__ == "__main__":
    serial_stop()