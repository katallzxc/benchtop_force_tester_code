''' MOTOR_RUN v2.0 - Katie Allison
Hatton Lab force testing platform control

Created: 2021-11-03
Updated: 2024-02-03

Actuates a stepper motor using one of three motion modes:
    MANUAL   - motor moves whenever a key is pressed
    AUTO     - motor moves in regular sweeps across a specified bounding box

This is the main function for motor control.

Notes:
 - need to add basic move to, move at functions
'''

import time
from helpers.motor_setup import mm_to_pulses,StepperMotor,LimitSwitch
from helpers.constants import CCW,COMPLETION_CODE

def calibrate_motor(motor,switchL,switchR,press_speed=6,travel_speed=10):
    """Function to calibrate motor position by finding endstop limit switches and
    setting zero position at left switch and maximum position at right switch.

    Args:
        motor (StepperMotor): fully set up StepperMotor object
        switchL (LimitSwitch): fully set up LimitSwitch object
        switchR (LimitSwitch): fully set up LimitSwitch object
        press_speed (int): slow move speed in mm/s
        travel_speed (int): fast move speed in mm/s
    """
    #TODO: consider moving this fcn to motor_run 
    def find_axis_limit(curr_switch,travel_direction,move_fast=False):
        """
        Helper function for calibrate_motor.
        Moves motor towards switch until switch is pressed, steps motor
        backwards and presses switch a second time, then sets the zero point
        for current axis at switch location.
        """
        report_pos = True
        def press_switch(num_steps,set_max_pos,fast_steps=0,move_fast=False):
            """
            Helper function for find_axis_limit.
            Steps towards limit switch until either switch is hit or step limit is exceeded.
            """
            # step towards switch and set position to be 0 at switch location
            if (move_fast and (fast_steps < num_steps)):
                motor.set_velocity(travel_direction,travel_speed)
                motor.step(fast_steps,calibrating=True)
                if not curr_switch.flag:
                    motor.set_velocity(travel_direction,press_speed)
                    motor.step(num_steps-fast_steps,calibrating=True)
            else:
                motor.set_velocity(travel_direction,press_speed)
                motor.step(num_steps,calibrating=True)

            # when switch is hit, update position and then back off
            if curr_switch.flag:
                # print out reported position (for checking for skipped steps, etc.)
                if report_pos:
                    print("Reported position at switch press is %s."%str(motor.position))

                # set new motor and/or switch position
                if curr_switch is motor.min_switch:
                    motor.position = 0
                    curr_switch.position = 0
                elif (curr_switch is motor.max_switch and set_max_pos):
                    motor.max_steps = motor.position
                    curr_switch.position = motor.position

                # back carriage away from switch
                motor.clear_switch_area(curr_switch,False)
            
            # if switch not hit, print warning
            else:
                error_string = "%s side limit switch not hit"%curr_switch.id
                raise ValueError(error_string)
        
        # take first pass towards switch
        steps_to_move = motor.max_steps
        if move_fast:
            print("Now starting first pass towards %s side switch at %d mm/s."%(curr_switch.id,travel_speed))
            fast_steps = int(steps_to_move/5)
        else:
            print("Now starting first pass towards %s side switch at %d mm/s."%(curr_switch.id,press_speed))
            fast_steps = 0
        press_switch(steps_to_move,False,fast_steps,move_fast)
        time.sleep(0.5)
        
        # move towards switch a second time
        steps_to_move = 2*mm_to_pulses(curr_switch.clearing_offset)
        print("Now starting second pass towards %s side switch at %d mm/s."%(curr_switch.id,press_speed))
        press_switch(steps_to_move,True)
    
    print("Motor calibration beginning")
    # find zero point for left side of axis
    calibration_direction = motor.origin_direction
    find_axis_limit(switchL,calibration_direction,move_fast=False)

    # find zero point for right side of axis
    calibration_direction = (not motor.origin_direction)
    find_axis_limit(switchR,calibration_direction,move_fast=True)
    print(COMPLETION_CODE)

#TODO: implement move_to,move_at  
      
if __name__ == "__main__":
    start_time = time.time()
    # set initial guess at maximum position of axis (number of steps between left switch and right switch)
    step_limit_guess = 1000

    # set up switches
    lSwitch = LimitSwitch("left")
    lSwitch.setup(20,0,5,0.5)
    lSwitch.print_details()
    rSwitch = LimitSwitch("right")
    rSwitch.setup(18,step_limit_guess,5,0.5)
    rSwitch.print_details()
    
    # set up motor
    m = StepperMotor("main",[lSwitch,rSwitch])
    m.setup([13,12],CCW,100,-6,step_limit_guess) #pin_assts,start_dirn,home_pos_mm,min_pos_mm,max_pos_mm
    m.print_details()
    print("Time: " + str(time.time()-start_time))
    calibrate_motor(m,lSwitch,rSwitch,10)