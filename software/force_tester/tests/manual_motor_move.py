'''
Script to test whether the stepper motor in the force tester moves in response to manually set move direction and distance.
TO DO: fix motor controller connections to be less clunky
'''
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from devices import ControllerConnection
from helpers.constants import CCW,CW,REPL_PROMPT,COMPLETION_CODE
from helpers.constants import MICROSTEPS_PER_FULL_STEP,FULL_STEPS_PER_MM
from helpers.constants import MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD

mcu = ControllerConnection(MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD)
MICROSTEPS_PER_MM = MICROSTEPS_PER_FULL_STEP*FULL_STEPS_PER_MM

def listen_to_actuator(waiting=False,verbose=False):
    num_msgs = 0
    done_listening = False
    while (not done_listening):
        returned = mcu.receive()
        if len(returned.split())>0:
            first_word = returned.split()[0]
            if first_word == "Traceback":
                returned = returned + mcu.receive() + mcu.receive() + mcu.receive()
                raise ValueError("Error message received from motor controller:\n{0}".format(returned))
                
        if (waiting and returned == COMPLETION_CODE):
            done_listening = True

        elif (len(returned) == 0 or returned[:3] == REPL_PROMPT):
            done_listening = True

        if (returned[:3] != REPL_PROMPT and len(returned)>0):
            num_msgs += 1
            if verbose: print("Motor message %d: %s" % (num_msgs,returned))
    return num_msgs

def listen_until_prompt(verbose=False):
    done_listening = False
    while (not done_listening):
        returned = mcu.receive()
        if (len(returned) == 0 or returned[:3] == REPL_PROMPT):
            done_listening = True
        else:
            if verbose: print("Motor message: %s" % (returned))
#TODO: figure out timing--does prompt always appear before return val?

def test_setup(print_setup=False):
    # send command to set up items and receive result
    # parameters as of Jul 2024
    mcu.send("setup_devices('left',(20,0,5,0.5),'right',(18,1000,5,0.5),'main',([13,12],CCW,100,-6,1000),True)")
    num_msgs = listen_to_actuator()
    print("Motor setup complete")
    listen_until_prompt(True)
    assert num_msgs>0, "no messages received from microcontroller during setup"

def test_set_direction(dirn):
    if dirn == CCW:
        sent_successfully = mcu.send("stepper_motor.set_direction(stepper_motor.origin_direction)",print_echo=True)
    elif dirn == CW:
        sent_successfully = mcu.send("stepper_motor.set_direction(not stepper_motor.origin_direction)",print_echo=True)
    listen_until_prompt(True)
    assert sent_successfully == True, "direction command not sent"

def test_get_direction(dirn,print_info=False):
    mcu.send("int(stepper_motor.direction)")
    set_dir = int(mcu.receive())
    if print_info:
        print("INFO: Current motor direction is %d"%set_dir)
        print("INFO: Desired direction was %d"%dirn)
    listen_until_prompt(True)

    assert set_dir == dirn, "current direction does not match desired direction"

def test_set_speed(speed):
    sent_successfully = mcu.send("stepper_motor.set_speed(%s)"%speed,print_echo=True)
    listen_until_prompt(True)
    assert sent_successfully == True, "speed command not sent"

def test_move(steps,print_info=False):
    mcu.send("stepper_motor.direction")
    curr_dir = mcu.receive()
    if print_info: print("INFO: Current motor direction is %s"%curr_dir)

    mcu.send("int(stepper_motor.position)")
    start_pos = int(mcu.receive())
    if print_info: print("INFO: Current motor position is %d"%start_pos)

    mcu.send("int(stepper_motor.move_speed)")
    curr_speed = int(mcu.receive())
    if print_info: print("INFO: Current motor scalar speed is %d"%curr_speed)

    mcu.send("stepper_motor.step(%d)"%steps)
    listen_to_actuator(verbose=print_info)

    mcu.send("int(stepper_motor.position)")
    try:
        end_pos = int(mcu.receive())
    except:
        print(mcu.receive())
    if print_info: print("INFO: Current motor position is %d"%end_pos)
    assert abs(abs(end_pos-start_pos) - steps) < MICROSTEPS_PER_MM, "step count not consistent"

def manual_motor_move(print_info=False):
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

    #motor_connection.motor_connection() -> decide whether to import mcu or make it here
    test_setup(print_setup=False)
    prompt = "Enter {0} to move carriage toward motor and {1} to move carriage away from motor.\n".format(CCW,CW)
    new_dirn = get_user_integer(prompt,req_binary=True)
    test_set_direction(new_dirn)
    test_get_direction(new_dirn,print_info)
    prompt = "Enter desired speed as an integer between 5 and 10 (mm/s).\n"
    new_speed = get_user_integer(prompt)
    test_set_speed(new_speed)
    prompt = "Enter desired number of steps to move.\n"
    new_steps = get_user_integer(prompt)
    test_move(new_steps,print_info)
    prompt = "Did test succeed? 0 or 1\n"
    success_flag = bool(get_user_integer(prompt,req_binary=True))
    if success_flag:
        print("SUCCESS: motor move testing passed")
    else:
        print("FAILED: User asserted that motor move test failed.")

if __name__ == "__main__":
    try:
        manual_motor_move(print_info=True)
    finally:
        mcu.close()