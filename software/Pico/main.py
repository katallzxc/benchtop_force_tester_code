import gc
import os

from troubleshoot.test_blink import LED_blink,print_test
from helpers.motor_setup import LimitSwitch, StepperMotor
from helpers.motor_run import calibrate_motor
from helpers.constants import CCW,CW,COMPLETION_CODE

flag = False
switch_flag_delay = 0.5
#TODO: remove unused globals
left_switch = None
right_switch = None
stepper_motor = None

def df():
    s = os.statvfs('//')
    return ('MB{0}'.format((s[0]*s[3])/1048576))

def free():
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    return 'MP{0:.2f}'.format(F/T*100)

def setup_devices(switchL_name,switchL_args,switchR_name,switchR_args,mot_name,mot_args,verbose=False):
    """
    Setup function for motors and switches.
    
    Initializes switch and motor objects
    
    Parameters:
    ------------
    switchL_name - string identifying left side switch
    switchL_args - set of variables to set left side switch parameters
    switchR_name - string identifying right side switch
    switchR_args - set of variables to set right side switch parameters
    mot_name - string identifying stepper motor
    mot_args - set of variables to set stepper motor parameters
    verbose - flag indicating whether or not to print setup info

    Returns:
    ------------
    left_switch, right_switch, stepper_motor - global object instances for switches and motors
    """
    # set up left switch
    global left_switch
    left_switch = LimitSwitch(switchL_name)
    left_switch.setup(*switchL_args)
    if verbose: left_switch.print_details()

    # set up right switch
    global right_switch
    right_switch = LimitSwitch(switchR_name)
    right_switch.setup(*switchR_args)
    if verbose: right_switch.print_details()
    
    # set up motor
    switch_set = [left_switch,right_switch]
    global stepper_motor
    stepper_motor = StepperMotor(mot_name,switch_set)
    stepper_motor.setup(*mot_args)
    if verbose: stepper_motor.print_details()
    
    print(COMPLETION_CODE)
    return left_switch, right_switch, stepper_motor

if __name__ == "__main__":
    # run basic IO tests
    print_test()
    LED_blink()

    # get motor ready
    # step_limit_guess = 1000
    # setup_devices("left",(20,0,5,0.5),"right",(18,step_limit_guess,5,0.5),"main",([13,12],CCW,100,-6,step_limit_guess))
    # calibrate_motor(stepper_motor,left_switch,right_switch)