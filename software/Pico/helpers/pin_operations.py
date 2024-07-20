''' PIN_OPERATIONS v1.0 - Katie Allison
Hatton Lab force testing platform microcontroller operations to read and set GPIO pins
for the Raspberry Pi Pico motor control circuit.

Created: 2022-11-16
Updated: 2024-07-04

Contains pin operation functions to configure, read, set, and pulse pins.
Some pin setting inputs are hard-coded as strings (and should match those in motor_setup.py).

NOTE: This module and the motor_setup.py module are the only modules in this project that
use the machine package (which means the microcontroller/firmware used can be swapped out
by altering pin_operations.py and motor_setup.py without changing the other modules).
'''

from machine import Pin
from time import sleep
from helpers.constants import LOGIC_LOW,LOGIC_HIGH

def config_pin(pin_num,pin_dirn,pin_pull=None,pin_val=None):
    """Sets up pin as input or output with pull-up/-down resistors as needed.
    Does not currently implement interrupt handlers--this must be done in main code.

    Args:
        pin_num (int): GPIO pin number.
        pin_dirn (str): specifies either "IN" or "OUT" (for input or output mode, respectively).
        pin_pull (str, optional): specifies pull-up/-down resistor type. Defaults to None.
        pin_val (int or bool, optional): sets initial pin value. Defaults to None.

    Raises:
        ValueError: prints warning if pin direction is neither "IN" nor "OUT".

    Returns:
        Pin: machine.Pin object representing a specific GPIO pin.
    """    
    # If pin is input, configure as input pin with internal resistors (if applicable)
    if pin_dirn == "IN":
        if pin_pull == "UP":
            pin_obj = Pin(pin_num, Pin.IN, pull=Pin.PULL_UP)
        elif pin_pull == "DOWN":
            pin_obj = Pin(pin_num, Pin.IN, pull=Pin.PULL_DOWN)
        else:
            pin_obj = Pin(pin_num, Pin.IN)
    
    # If pin is output, configure pin as output with initial value (if applicable)
    elif pin_dirn == "OUT":
        if pin_val is None:
            pin_obj = Pin(pin_num, Pin.OUT)
        else:
            pin_obj = Pin(pin_num, Pin.OUT, value=pin_val)

    # If pin not set as input or output, throw error
    else:
        raise ValueError("Invalid pin direction/mode set!")

    return pin_obj

def set_pin(pin_obj,pin_val):
    """Sets pin output to either on or off.

    Args:
        pin_obj (machine.Pin): Target pin.
        pin_val (int or bool): Desired value of target pin.
    """    
    if pin_val == LOGIC_HIGH:
        pin_obj.on()
    elif pin_val == LOGIC_LOW:
        pin_obj.off()
    
    return True

def read_pin(pin_obj):
    """Reads current pin value.

    Args:
        pin_obj (machine.Pin): Target pin.

    Returns:
        bool: current value of pin.
    """ 
    return pin_obj.value()

def pulse_pin(pin_obj,on_time,off_time):
    """Bring pin high and then low for specific periods of time. Used to drive stepper motor.

    Args:
        pin_obj (machine.Pin): Target pin.
        on_time (int): Width of logic-high part of pulse in seconds.
        off_time (int): Width of logic-low part of pulse in seconds.
    """
    # pulse high to drive step
    pin_obj.on()
    sleep(on_time)
    
    # bring low in between steps
    pin_obj.off()
    sleep(off_time)

    return True