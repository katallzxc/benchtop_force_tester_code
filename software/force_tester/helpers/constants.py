''' CONSTANTS v1.0 - Katie Allison - Created 2024-04-24

Hatton Lab force testing platform constants that are widely used in other modules.
Serial connection constants (port, baud) may need to be updated if the computer assigns a different
port to the device (happens sometimes).

NOTE: Some constants are copied from the Raspberry Pi Pico motor controller code and will need to 
be updated if the constants.py file on the Pico microcontroller is modified.
'''

# set keys for data type indicators
TIME_TYPE = 0
FORCE_TYPE = 1
POSITION_TYPE = 2
PRESSURE_TYPE = 3

# set constants related to serial connections
PNEUMATICS_PORT = 'COM7'
PNEUMATICS_BAUD = 19200
GAUGE_PORT = 'COM6'
GAUGE_BAUD = 115200
MOTOR_CONTROLLER_PORT = 'COM5'
MOTOR_CONTROLLER_BAUD = 115200
REPL_PROMPT = ">>>"

'''
MICROCONTROLLER CONSTANTS
NOTE: these values are from the constants.py file on the Raspberry Pi Pico microcontroller 
and must be updated if the Pico constants.py file is changed
'''
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
# this quantity is the same for many standard steppers
HOME_POS_MM = 100
# this is somewhat arbitrarily set to be generally in the middle of the leadscrew

# set constants associated with TB6600 stepper motor driver settings & specifications
MICROSTEPS_PER_FULL_STEP = 2    
# set using DIP switches. Currently set to 2/A (half-stepping)
# microstep settings DRASTICALLY change how far the leadscrew carriage moves per pulse
# so be VERY CAREFUL if changing this
MIN_PWM_OFF_TIME = 0.001   
# this minimum comes from microstepping tuning--if the off time in the PWM signal is under
# 1 ms, the motor stalls.
POS_PRINT_INTERVAL = int(FULL_STEPS_PER_MM*MICROSTEPS_PER_FULL_STEP/10)
# position printed every 0.1 mm (relationship b/w mm dist & # pulses set by microstep settings)

# set strings used as flags in serial communication between microcontroller and computer
COMPLETION_CODE = "DONE"
