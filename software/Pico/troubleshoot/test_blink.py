''' TEST_BLINK v1.1 - Katherine Allison

Created: 2022-11-15
Updated: 2023-11-15

Simple test cases that blink LEDs with or without external input to harmlessly verify microcontroller function.
'''

from machine import Pin
from helpers.pin_operations import config_pin,set_pin,pulse_pin
import time

def LED_blink(led1_pin=25,led2_pin=25,cycles=3,verbose=True):
    led1 = config_pin(led1_pin,"OUT","","")
    led2 = config_pin(led2_pin,"OUT","","")
    if verbose:
        print("pins configured")

    for i in range(0,cycles):
        pulse_pin(led1,0.25,0.5)
        pulse_pin(led2,0.25,0.5)
        if verbose:
            print("Now in cycle "+str(i)+" of "+str(cycles))

def button_blink(led_pin=25,button_pin=18,delay=100):
    led = Pin(led_pin, Pin.OUT)
    button = Pin(button_pin, Pin.IN, Pin.PULL_UP)

    while True:
        print(button.value())
        if button.value():
            led.value(1)
        else:
            led.value(0)
        time.sleep_ms(delay)

def print_test():
    print("print_test function entered successfully")
    return True