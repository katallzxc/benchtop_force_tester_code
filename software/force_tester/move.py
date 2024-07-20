''' MOVE v0.0 - Katie Allison
Hatton Lab force testing platform control

Created: 2021-11-03
Updated: 2023-12-17

This is the main function for motor control from a PC.
'''
import time
from force_tester.helpers.constants import COMPLETION_CODE

PROMPT_STRING = ">>>"
INVALID_POS = -99

################## Testing 2023-12-18
def quick_backward_dist(motor_link,num_pulses):
    motor_link.send("stepper_motor.set_direction(stepper_motor.origin_direction)")
    motor_link.send("stepper_motor.step(%d,indicate_completion=False,print_pos=True)"%(num_pulses))
def quick_forward_dist(motor_link,num_pulses):
    motor_link.send("stepper_motor.set_direction(not stepper_motor.origin_direction)")
    motor_link.send("stepper_motor.step(%d,indicate_completion=False,print_pos=True)"%(num_pulses))
def quick_listen(motor_link):
    try:
        returned = int(motor_link.receive())
    except:
        returned = INVALID_POS
    return returned
##################

def listen_to_actuator(motor_link,waiting,verbose):
    returned = motor_link.receive()
    
    num_msgs = 0
    if (returned[:3] != PROMPT_STRING and len(returned)>0):
        num_msgs += 1
        if verbose: print("Motor message %d: %s" % (num_msgs,returned))

    done_listening = False
    while (not done_listening):
        returned = motor_link.receive()
        if len(returned.split())>0:
            first_word = returned.split()[0]
            if first_word == "Traceback":
                while returned != PROMPT_STRING:
                    returned = motor_link.receive()
                    print(returned)
                raise ValueError("Error message received from motor controller")
                
        if waiting:  
            if returned == COMPLETION_CODE:
                done_listening = True

        else:
            if (len(returned) == 0 or returned[:3] == PROMPT_STRING):
                done_listening = True

        if (returned[:3] != PROMPT_STRING and len(returned)>0):
            num_msgs += 1
            if verbose: print("Motor message %d: %s" % (num_msgs,returned))

    return num_msgs

def talk_to_actuator(motor_link,command,wait_for_completion=False,verbose=True):
    motor_link.send(command)
    num_msgs_returned = listen_to_actuator(motor_link,wait_for_completion,verbose)
    return num_msgs_returned

def calibrate_motor(motor_link,press_speed=2,travel_speed=10,wait_for_completion=False):
    calibrate_string = "calibrate_motor(stepper_motor,left_switch,right_switch,press_speed=%s,travel_speed=%s)"%(str(press_speed),str(travel_speed))
    talk_to_actuator(motor_link,calibrate_string,wait_for_completion)

def stop_motor(motor_link,wait_for_completion=False,verbose=False):
    wait_string = str(wait_for_completion)
    # talk_to_actuator(motor_link,"0")
    talk_to_actuator(motor_link,"stepper_motor.no_step(indicate_completion=%s)"%wait_string,wait_for_completion,verbose)

def move_gauge_forward_dist(motor_link,num_pulses,wait_for_completion=False):
    wait_string = str(wait_for_completion)
    talk_to_actuator(motor_link,"stepper_motor.set_direction(not stepper_motor.origin_direction)")
    talk_to_actuator(motor_link,"stepper_motor.step(%d,indicate_completion=%s)"%(num_pulses,wait_string),wait_for_completion)

def move_gauge_forward_vel(motor_link,num_pulses,vel,wait_for_completion=False):
    wait_string = str(wait_for_completion)
    talk_to_actuator(motor_link,"stepper_motor.set_velocity(not stepper_motor.origin_direction,%s)"%str(vel))
    talk_to_actuator(motor_link,"stepper_motor.step(%d,indicate_completion=%s)"%(num_pulses,wait_string),wait_for_completion)
    
def move_gauge_backward_dist(motor_link,num_pulses,wait_for_completion=False):
    wait_string = str(wait_for_completion)
    talk_to_actuator(motor_link,"stepper_motor.set_direction(stepper_motor.origin_direction)")
    talk_to_actuator(motor_link,"stepper_motor.step(%d,indicate_completion=%s)"%(num_pulses,wait_string),wait_for_completion)

def move_gauge_backward_vel(motor_link,num_pulses,vel,wait_for_completion=False):
    wait_string = str(wait_for_completion)
    talk_to_actuator(motor_link,"stepper_motor.set_velocity(stepper_motor.origin_direction,%s)"%str(vel))
    talk_to_actuator(motor_link,"stepper_motor.step(%d,indicate_completion=%s)"%(num_pulses,wait_string),wait_for_completion)

def move_single_step(motor_link,wait_for_completion=False):
    wait_string = str(wait_for_completion)
    talk_to_actuator(motor_link,"stepper_motor.step(1,indicate_completion=%s)"%(wait_string),wait_for_completion)
