'''
Script to test whether the stepper motor calibration routine (for the force tester) runs correctly.
TO DO: fix motor controller connections to be less clunky
'''
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import move
from devices import ControllerConnection
from helpers.constants import REPL_PROMPT,MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD

mcu = ControllerConnection(MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD)

def test_setup(print_setup=False):
    mcu.send("setup_devices('left',(20,0,5,0.5),'right',(18,1000,5,0.5),'main',([13,12],CCW,100,-6,1000),True)")
    num_msgs = 0
    done_listening = False
    while (not done_listening):
        returned = mcu.receive()
        if len(returned.split())>0:
            first_word = returned.split()[0]
            if first_word == "Traceback":
                raise ValueError("Error message received from motor controller")

        if (returned[:3] != REPL_PROMPT and len(returned)>0):
            num_msgs += 1
            if print_setup: print("Motor message %d: %s" % (num_msgs,returned))
        else:
            done_listening = True
            print("Motor setup complete")

    assert num_msgs>0, "no messages received from microcontroller during setup"

def test_switch(curr_switch):
    user_input = ""
    while len(user_input) ==0: 
        if curr_switch == 0: 
            move.talk_to_actuator(mcu,'left_switch.check_flag()')
        elif curr_switch == 1: 
            move.talk_to_actuator(mcu,'right_switch.check_flag()')
        user_input = input("Press ENTER to get state of switch. Enter any other key to exit.")

def test_calibrate(print_info=False):
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
    prompt = "Enter 0 to test left switch and 1 to test right switch.\n"
    user_switch = get_user_integer(prompt,req_binary=True)
    test_switch(user_switch)
    prompt = "Enter desired travel speed (for fast move between left and right switches).\n"
    user_speed_fast = get_user_integer(prompt)
    prompt = "Enter desired press speed (for slow move when pressing switches).\n"
    user_speed_slow = get_user_integer(prompt)
    move.calibrate_motor(mcu,press_speed=user_speed_slow,travel_speed=user_speed_fast,wait_for_completion=True)
    prompt = "Did test succeed? 0 or 1\n"
    success_flag = bool(get_user_integer(prompt,req_binary=True))
    if success_flag:
        print("SUCCESS: calibrate testing passed")
    else:
        print("FAILED: User asserted that calibrate test failed.")

if __name__ == "__main__":
    try:
        test_calibrate(print_info=False)
    finally:
        mcu.close()