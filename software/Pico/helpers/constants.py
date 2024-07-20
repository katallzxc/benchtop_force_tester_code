''' CONSTANTS v1.0 - Katie Allison - Created 2024-07-04

Hatton Lab force testing platform motor constants
Contains constants that are used in most other motor control code modules.

NOTE: These constants describe the physical/electrical setup of the force testing platform
(e.g., driver microstep settings, motor step size) and should NOT be changed unless
the force testing platform has been physically modified.
'''

# set the values used to set a pin high or low
LOGIC_LOW = 0
LOGIC_HIGH = 1

# set constants associated with direction of motor turning
# values are arbitrary and not associated with specific physical properties,
# but values are used to set other directional constants (e.g. calibration direction),
# so be careful to catch all references if changing
CCW = 0
CW = 1

# set constants associated with motor 
FULL_STEPS_PER_MM = 40
# source: marked 50 mm on leadscrew support and actuated stepper to move carriage to
# end of marked distance. 2,000 steps required to travel this 50 mm.
# 2000 steps per 50 mm => 40 steps per mm
# 200 steps per rev => 40 steps = 1 mm = 0.2 turns
# so each 0.1 mm is 4 steps = 0.02 turns
FULL_STEPS_PER_MOTOR_REV = 200

# set constants associated with TB6600 stepper motor driver settings & specifications
MICROSTEPS_PER_FULL_STEP = 2    
# set using DIP switches. Currently set to 2/A (half-stepping)
# microstep settings DRASTICALLY change how far the leadscrew carriage moves per pulse
# so be VERY CAREFUL if changing this
MIN_PWM_OFF_TIME = 0.001   
# this minimum comes from microstepping tuning--if the off time in the PWM signal is under
# 1 ms, the motor stalls.

# set strings used as flags in serial communication between microcontroller and computer
COMPLETION_CODE = "DONE"