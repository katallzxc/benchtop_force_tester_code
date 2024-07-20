'''
Script to test whether a serial connection with the Pico microcontroller that controls the motor can be established.
'''
import sys
import os
import time
import numpy as np

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from devices import ControllerConnection
from helpers.constants import MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD

mcu = ControllerConnection(MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD)

def test_exists():
    if mcu is None:
        print("True")
    assert mcu is not None

def test_connected():
    sent_successfully = mcu.send("")
    assert sent_successfully == True

def test_return():
    mcu.send("2+2")
    returned = mcu.receive()
    assert returned == "4"

def test_exchange_speed(num_exchanges=1000):
    time_records = np.empty((num_exchanges,2))
    for i in range(0,num_exchanges):
        start = time.time()
        mcu.send("2+2")
        sent_time = time.time()
        time_records[i,0] = sent_time - start
        mcu.receive()
        time_records[i,1] = time.time() - sent_time
    time_avg = np.average(time_records,axis=0)
    print("Average send time in s: {0}\nAverage receive time in s: {1}".format(*time_avg))

def test_function_call():
    mcu.receive()
    sent_successfully = mcu.send("LED_blink(verbose=False)")
    assert sent_successfully == True

def test_closed():
    mcu.close()
    try:
        sent_successfully = mcu.send("test")
    except:
        sent_successfully = False
    assert sent_successfully == False

def motor_connection():
    test_exists()
    test_connected()
    test_return()
    test_exchange_speed()
    test_function_call()
    test_closed()
    print("SUCCESS: motor_connection testing passed")

if __name__ == "__main__":
    motor_connection()