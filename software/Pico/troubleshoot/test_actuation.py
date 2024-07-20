''' TEST_ACTUATION v0.0 - Katherine Allison - Created 2024-07-06

Simple test cases that allow staged testing of individual actuation functionalities.

NOTE: This is outdated as of 2024-07-10 and will not work if run directly
(because speed setting function and motor setup parameters have changed)
but is left in place in case I wish to edit it to test other features later
'''

from helpers.motor_setup import LimitSwitch, StepperMotor, pulses_to_mm, mm_to_pulses
from helpers.constants import CCW,CW

test_with_duty=True
min_on_time = 0.00001

def guided_setup(setup_params,verbose=False):
    """
    Setup function for motors and switches.
    Initializes switch and motor objects with option to edit parameters with user input.
    
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
    left_switch, right_switch, stepper_motor - object instances for switches and motors
    """
    def confirm_params_with_prompt(is_switch,device_id,device_args):
        # set type of device
        if is_switch:
            device_type = "switch"
            device_arg_names = "pin_assignment,pos_guess,clearing_distance,bounce_delay"
        else:
            device_type = "motor"
            device_arg_names = "pin_assts,times,start_dirn,home_pos_mm,max_pos_mm"

        # prompt user to confirm parameters
        print("Now setting up {0} with ID of {1} and {2} properties:\n{3}.".format(
            device_type,device_id,len(device_args),device_arg_names))
        new_args = device_args
        change_args = input("Property values are:\n{0}\nPress ENTER to confirm or C to change.".format(new_args))
        while change_args == "C" or change_args == "c":
            new_args = input("Enter new values of properties.")
            change_args = input("Property values are:\n{0}\nPress ENTER to confirm or C to change.".format(new_args))
        return new_args

    # unpack default setup parameters
    switchL_name,switchL_args,switchR_name,switchR_args,mot_name,mot_args = setup_params

    # set up left switch
    left_switch = LimitSwitch(switchL_name)
    switchL_args = confirm_params_with_prompt(True,switchL_name,switchL_args)
    left_switch.setup(*switchL_args)
    if verbose: left_switch.print_details()

    # set up right switch
    right_switch = LimitSwitch(switchR_name)
    switchR_args = confirm_params_with_prompt(True,switchR_name,switchR_args)
    right_switch.setup(*switchR_args)
    if verbose: right_switch.print_details()
    
    # set up motor
    stepper_motor = StepperMotor(mot_name)
    switch_set = [left_switch,right_switch]
    mot_args = confirm_params_with_prompt(False,mot_name,mot_args)
    stepper_motor.setup(switch_set,*mot_args)
    if verbose: stepper_motor.print_details()
    return left_switch, right_switch, stepper_motor

def test_switch(curr_switch):
    user_input = ""
    while len(user_input) == 0: 
        curr_switch.check_flag()
        user_input = input("Press ENTER to get state of switch. Enter any other key to exit.")

def test_set_direction(dirn,stepper):
    stepper.set_direction(dirn)
    print("Direction set to {0}. Motor direction property has value {1}.".format(dirn,stepper.direction))

def test_set_speed(speed,testing_duty,stepper):
    #stepper.set_speed(speed)
    # TEMP: using testing function to set speed instead--be careful! no validation of speeds against minimum!
    stepper.set_pulse_timing_testing(mm_to_pulses(speed),test_with_duty,testing_duty,min_on_time)
    print("Speed set to {0}. Motor speed property has value {1}.".format(speed,stepper.move_speed))
    print("On-time and off-time durations set to {0},{1} and frequency set to {2}.".format(
        stepper.pulse_time,stepper.delay_time,stepper.pulse_freq
    ))

def test_move(steps,stepper):
    print("INFO: Current motor direction is {0}".format(stepper.direction))
    print("INFO: Current motor speed is {0}".format(stepper.move_speed))
    print("INFO: Current motor PWM duty cycle is {0}".format(stepper.duty_cycle))
    print("INFO: Current motor position is {0}".format(stepper.position))

    cancel_msg = input("Press ENTER when ready to step {0} mm, or press C to cancel.".format(pulses_to_mm(steps)))
    if cancel_msg == "C" or cancel_msg == "c": 
        print("Movement test cancelled. Returning to main testing loop.")
        return
    else:
        stepper.step(steps)
        print("INFO: Current motor position is {0}".format(stepper.position))

def run_duty_comparison_test(setup_defaults):
    # specify test set
    test_sets = {
        10: [0.2,0.15,0.1,0.05],
        9: [0.25,0.2,0.15,0.1,0.05],
        8: [0.3,0.25,0.2,0.15,0.1,0.05],
        7: [0.4,0.3,0.25,0.2,0.15,0.1,0.05],
        6: [0.4,0.3,0.25,0.2,0.15,0.1,0.05]#,
        #5: [0.3,0.25,0.2,0.15],
        #4: [0.2,0.15]
        }
    test_sets = {
        10: [0.15],
        9: [0.15],
        8: [0.35],
        7: [0.4],
        6: [0.4],
        5: [0.3],
        4: [0.2]
        }
    
    # set up devices and prompt start
    switchL,switchR,mot = guided_setup(setup_defaults,verbose=True)
    print("Devices set up. Test sets: ")
    print(test_sets)
    
    # run test of all duty cycle values for each speed
    for test_speed in test_sets:
        duty_rng = test_sets[test_speed]
        num_tests = len(duty_rng)
        if num_tests % 2 == 1: duty_rng.append(duty_rng[-1])
        print("NOW TESTING SPEED OF {0} mm/s WITH DUTY VALUES {1}".format(test_speed,duty_rng))
        
        # alternating directions, run short distance at each duty cycle
        dirn = 0
        num_steps = 800
        for duty_val in duty_rng:
            dirn = not dirn
            test_set_direction(dirn,mot)
            test_set_speed(test_speed,duty_val,mot)
            test_move(num_steps,mot)
            print(duty_val)
            
def run_actuation_test(setup_defaults):
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
    
    # test setup and switch readings
    switchL,switchR,mot = guided_setup(setup_defaults,verbose=True)
    print("TESTING LEFT SWITCH")
    test_switch(switchL)
    print("TESTING RIGHT SWITCH")
    test_switch(switchR)
    
    # test setting speed and direction (iteratively)
    testing_done = False
    while not testing_done:
        prompt = "Enter {0} to move carriage toward motor and {1} to move carriage away from motor.\n".format(CCW,CW)
        new_dirn = get_user_integer(prompt,req_binary=True)
        test_set_direction(new_dirn,mot)
        prompt = "Enter a new motor move speed (under 25 mm/s)."
        #new_speed = get_user_integer(prompt)
        new_speed = 1
        prompt = "Enter a new motor PWM duty cycle (under 0.5)."
        new_duty = float(input(prompt))
        test_set_speed(new_speed,new_duty,mot)

        # test movement
        prompt = "Enter desired number of steps to move.\n"
        new_steps = get_user_integer(prompt)
        test_move(new_steps,mot)
        repeat_input = input("Press ENTER to stop testing or R to repeat test.")
        if repeat_input == "R" or repeat_input == "r":
            testing_done = False
        else:
            testing_done = True

if __name__ == "__main__":
    default_setup_parameters = ('left',(20,0,5,0.5),'right',(18,1000,5,0.5),'main',([13,12],[0.001,0.001],CCW,100,1000))
    #run_actuation_test(default_setup_parameters)
    run_duty_comparison_test(default_setup_parameters)