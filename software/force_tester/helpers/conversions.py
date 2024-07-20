''' CONVERSIONS v0.1 - Katherine Allison

Created: 2023-11-15
Updated: 2024-04-25

Contains helper functions to help convert between units/quantities.
(e.g., between mm travel distance along leadscrew and equivalent number of steps of the driving motor)
'''
from force_tester.helpers.constants import TIME_TYPE,FORCE_TYPE,POSITION_TYPE,PRESSURE_TYPE
from force_tester.helpers.constants import FULL_STEPS_PER_MM,MICROSTEPS_PER_FULL_STEP

MICROSTEPS_PER_MM = FULL_STEPS_PER_MM*MICROSTEPS_PER_FULL_STEP
NS_PER_S = 10**9

UNIT_SCALES = {
    TIME_TYPE:1/NS_PER_S,
    FORCE_TYPE:1,
    POSITION_TYPE:1/MICROSTEPS_PER_MM,
    PRESSURE_TYPE:1
}

def pulses_to_mm(num_pulses):
    """
    Short helper function to convert from stepper motor pulse inputs to carriage mm travelled.
    A single pulse actuates the stepper through one single step (or microstep, if applicable).
    
    NOTE: This is a copy of the function on the Raspberry Pi Pico microcontroller and must be 
    updated if the Pico function is changed.
    
    Parameters:
    ------------
    num_pulses - stepper motor drive signal pulses.
    
    Returns:
    ------------
    num_mm - mm that correspond to input motor pulse count.
    """
    num_mm = float(num_pulses/MICROSTEPS_PER_MM)
    
    return num_mm

def mm_to_pulses(num_mm):
    """
    Short helper function to convert from mm travel distance to stepper motor drive pulse count.
    A single pulse actuates the stepper through one single step (or microstep, if applicable).
    
    NOTE: This is a copy of the function on the Raspberry Pi Pico microcontroller and must be 
    updated if the Pico function is changed.
    
    Parameters:
    ------------
    num_mm - distance in mm.
    
    Returns:
    ------------
    num_pulses - number of stepper motor drive signal pulses required to travel this distance.
    """
    num_pulses = int(num_mm*MICROSTEPS_PER_MM)
    
    return num_pulses

def sec_to_ns(num_seconds):
    """
    Short helper function to convert from seconds to nanoseconds.
    
    Parameters:
    ------------
    num_seconds - time in seconds
    
    Returns:
    ------------
    num_nanosec - time in nanoseconds
    """
    num_nanosec = int(num_seconds*NS_PER_S)
    return num_nanosec

def ns_to_sec(num_nanosec):
    """
    Short helper function to convert from nanoseconds to seconds.
    
    Parameters:
    ------------
    num_nanosec - time in nanoseconds
    
    Returns:
    ------------
    num_seconds - time in seconds
    """
    num_seconds = int(num_nanosec/NS_PER_S)
    return num_seconds

def scale_data_by_type(data_arr,data_type=TIME_TYPE):
    """Apply scaling factor to data.

    Args:
        data_arr (numpy ndarray): array of data, usually 1D
        data_type (int, optional): key for scaling factor lookup. Defaults to TIME_TYPE.

    Returns:
        tuple: scaled data array and scale factor
    """    
    scale_factor = UNIT_SCALES[data_type]
    return (data_arr*scale_factor,scale_factor)

if __name__ == "__main__":
    # N.B.: since the import of constants is an implicit relative import when this module is run directly,
    # to run this directly without errors, you have to run as a module and with qualified name i.e.:
    # python -m force_tester.helpers.conversions
    # Also, run FROM THE DIRECTORY ABOVE force_tester
    # See: https://peps.python.org/pep-0338/#import-statements-and-the-main-module
    
    print("Pulses per mm: {0}".format(mm_to_pulses(1)))
    print("Mm per pulse: {0}".format(pulses_to_mm(1)))
