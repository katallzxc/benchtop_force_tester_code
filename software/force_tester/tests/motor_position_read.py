'''
Script to test whether the stepper motor in the force tester returns current stepper position when polled while motor is running.
'''
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import move
from devices import ControllerConnection
from helpers.constants import CCW,CW
from helpers.constants import MICROSTEPS_PER_FULL_STEP,FULL_STEPS_PER_MM,HOME_POS_MM
from helpers.constants import POS_PRINT_INTERVAL,MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD

mcu = ControllerConnection(MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD)
MICROSTEPS_PER_MM = MICROSTEPS_PER_FULL_STEP*FULL_STEPS_PER_MM
HOME_POS_PULSES = HOME_POS_MM*MICROSTEPS_PER_MM

def setup(be_verbose=False):
    setup_call = "setup_devices('left',(20,0,5,0.5),'right',(18,1000,5,0.5),'main',([13,12],CCW,100,-6,1000),True)"
    move.talk_to_actuator(mcu,setup_call,wait_for_completion=True,verbose=be_verbose)

def test_set_direction(dirn):
    if dirn == CCW:
        sent_successfully = mcu.send("stepper_motor.set_direction(stepper_motor.origin_direction)")
    elif dirn == CW:
        sent_successfully = mcu.send("stepper_motor.set_direction(not stepper_motor.origin_direction)")
    mcu.receive()
    assert sent_successfully == True, "direction command not sent"

def test_quick_move(dirn,steps):
    if dirn == CW:
        move.quick_forward_dist(mcu,steps)
    else:
        move.quick_backward_dist(mcu,steps)

def motor_move_and_give_pos(be_verbose=False):
    def get_user_integer(msg,req_binary=False):
        # helper function to repeatedly ask for input until valid integer is inputted
        valid_int = False
        while not valid_int:
            try:
                user_int = int(input(msg))
                if req_binary:
                    if (user_int == 0 or user_int == 1):
                        valid_int = True
                else:
                    valid_int = True
            except ValueError:
                if req_binary:
                    print("Entry must be 0 or 1")
                else:
                    print("Entry must be an integer.")
        return user_int

    setup(be_verbose)
    mcu.receive()

    # get direction to move and set sign of change in position (to either increment or decrement)
    prompt = "Enter {0} to move carriage toward motor and {1} to move carriage away from motor.\n".format(CCW,CW)
    new_dirn = get_user_integer(prompt,req_binary=True)
    if new_dirn == 0:
        change_sign = -1
    elif new_dirn == 1:
        change_sign = 1

    # get distance (in pulses) to move
    prompt = "Enter desired number of steps to move.\n"
    new_steps = get_user_integer(prompt)
    test_quick_move(new_dirn,new_steps)
    
    # check position repeatedly
    invalid_count = 0
    last_valid = 0
    still_moving = True
    while still_moving:
        returned = mcu.receive()
        try:
            pos = int(returned)
            last_valid = pos
        except:
            invalid_count += 1
            if invalid_count > 5: 
                still_moving = False
        if be_verbose: print(pos)

    # determine expected last position
    # (based on starting position and step print interval, both hardcoded in microcontroller code)
    pos_change = change_sign*(1 + new_steps - (new_steps % POS_PRINT_INTERVAL))
    expected_pos = int(HOME_POS_PULSES + pos_change)
    if (new_steps % POS_PRINT_INTERVAL == 0): 
        expected_pos = expected_pos - change_sign*POS_PRINT_INTERVAL

    # set failure string for assert output
    fail_str = "position {0} printed by motor does not match expected position {1}".format(
        last_valid,expected_pos)
    fail_str = fail_str + " based on home position {0} (pulses) and print interval {1}".format(
        HOME_POS_PULSES,POS_PRINT_INTERVAL)
    assert last_valid == expected_pos,fail_str

if __name__ == "__main__":
    try:
        motor_move_and_give_pos(True)
        print("SUCCESS: Motor position readout testing passed")
    finally:
        mcu.close()