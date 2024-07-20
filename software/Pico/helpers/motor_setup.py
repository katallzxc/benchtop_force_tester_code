''' MOTOR_SETUP v2.1 - Katie Allison
Hatton Lab force testing platform motor assembly setup.
Contains class definitions for LimitSwitch and StepperMotor objects.

Created: 2022-11-16
Updated: 2024-07-07

NOTE: The StepperMotor class takes the limit switches as an input in order to check the 
switch state before each motor step, so the LimitSwitch objects must be instantiated prior
to instantiating the StepperMotor object.
'''

from machine import Pin
from time import sleep
import sys, uselect
from helpers.pin_operations import config_pin,set_pin,read_pin,pulse_pin
from helpers.constants import LOGIC_LOW,LOGIC_HIGH,CCW,CW,COMPLETION_CODE
from helpers.constants import FULL_STEPS_PER_MM,MICROSTEPS_PER_FULL_STEP,FULL_STEPS_PER_MOTOR_REV,MIN_PWM_OFF_TIME

INTERRUPT_FLAG = False

def callback(pin):
    """
    Callback function for pin interrupt (backup in case querying value of limit switch with check_flag fails)

    Args:
        pin (Pin): MicroPython machine.Pin object representing limit switch pin
    """
    global INTERRUPT_FLAG
    INTERRUPT_FLAG = True
    #print("Switch pressed and unpressed.")

def pulses_to_mm(num_pulses):
    """
    Short helper function to convert from stepper motor pulse inputs to carriage mm travelled.
    A single pulse actuates the stepper through one single step (or microstep, if applicable).
    
    NOTE: the FULL_STEPS_PER_MM, MICROSTEPS_PER_FULL_STEP, or FULL_STEPS_PER_MOTOR_REV properties 
    of the StepperMotor class should only change if the physical & electrical setup of the system 
    is changed (i.e., the screw or motor is replaced, or the settings on the stepper drive change).
    
    Parameters:
    ------------
    num_pulses - stepper motor drive signal pulses.
    
    Returns:
    ------------
    num_mm - mm that correspond to input motor pulse count.
    """
    pulses_per_mm = FULL_STEPS_PER_MM * MICROSTEPS_PER_FULL_STEP
    num_mm = float(num_pulses/pulses_per_mm)
    
    return num_mm

def mm_to_pulses(num_mm):
    """
    Short helper function to convert from mm travel distance to stepper motor drive pulse count.
    A single pulse actuates the stepper through one single step (or microstep, if applicable).
    
    NOTE: the FULL_STEPS_PER_MM, MICROSTEPS_PER_FULL_STEP, or FULL_STEPS_PER_MOTOR_REV properties 
    of the StepperMotor class should only change if the physical & electrical setup of the system 
    is changed (i.e., the screw or motor is replaced, or the settings on the stepper drive change).
    
    Parameters:
    ------------
    num_mm - distance in mm.
    
    Returns:
    ------------
    num_pulses - number of stepper motor drive signal pulses required to travel this distance.
    """
    pulses_per_mm = FULL_STEPS_PER_MM * MICROSTEPS_PER_FULL_STEP
    num_pulses = int(num_mm*pulses_per_mm)
    
    return num_pulses

class LimitSwitch:
    '''
    Class to represent an SPDT microswitch operating as an NC (normally closed) limit switch.

    Properties:
    ------------
    id - string to indicate side of ballscrew to which switch is assigned ('Left' or 'Right').
    data_pin - GPIO pin on the Pico that detects when the switch signal falls to LOW.
    position - motor in motor steps at which switch is pressed (set during motor calibration).
    clearing_offset - required distance (in mm) from switch that must be moved before switch flag can be cleared.
    delay - time interval to wait after switch is opened to ignore bouncing effect. #TODO: remove if not needed
    flag - Boolean that indicates whether switch is open or closed.

    Methods:
    ------------
    __init__ - create an instance of the class (a LimitSwitch object).
    callback - set flag property to indicate that switch is open (called at falling edge event of GPIO pin). #TODO: move or remove
    setup - set properties of a LimitSwitch object and set up corresponding GPIO pin.
    print_details - print all values of LimitSwitch object properties.
    check_flag - query value of flag and print warning if flag is hit.
    clear_flag - reset flag to indicate that switch is closed again.
    '''

    def __init__(self,name):
        """
        Instantiates a LimitSwitch object.
        """
        self.id = name

    def setup(self,pin_assignment,pos_guess,clearing_distance,bounce_delay):
        """
        Sets up a LimitSwitch object by specifying its (direction-specific) ID, input pin
        assignment in the Pico GPIO, how long to wait after switch opening to ignore
        bouncing effect, and initializes status (flag set to False).
        Sets up event detection for the GPIO pin to indicate when switch opens.
        """
        # set properties of switch
        self.data_pin = config_pin(pin_assignment, "IN", "UP")
        self.position = pos_guess
        self.clearing_offset = clearing_distance
        #self.delay = bounce_delay #TODO: remove if not needed
        self.flag = False

        # event detection for rising edge of switch input (triggered when switch opens and then closes again)
        self.data_pin.irq(trigger=Pin.IRQ_RISING, handler=callback)

        print("INFO: %s side switch set up!"%self.id)
    
    def print_details(self):
        """
        Prints values of all LimitSwitch object property values for a given instance for verification.
        """
        print("LIMIT SWITCH OBJECT PROPERTIES =================")
        print("Switch ID is %s."%self.id)
        print("Motor must move %f mm away from switch to clear switch." % self.clearing_offset)
        #print("There is a %f millisecond debouncing delay after switch activation." %self.delay) #TODO: remove if not needed
        print("Current switch activation status is %r."%self.flag)
        print("=========================================")

    def check_flag(self,interrupts_on=True):
        """
        Checks limit switch status and prints warning if switch is pressed
        """
        self.flag = read_pin(self.data_pin)
        if self.flag and interrupts_on:
            print("INFO: %s side switch pressed!"%self.id)
            #sleep(self.delay) #not needed if not using interrupts
        return self.flag

    def clear_flag(self):
        """
        Resets limit switch status when switch is closed.
        """
        self.flag = read_pin(self.data_pin)
        if self.flag:
            raise ValueError("Clear switch routine entered when switch is still pressed!")
        else:
            self.flag = False
            print("INFO: %s side switch cleared!"%self.id)

class StepperMotor:
    """
    Class to represent 23HS6430 NEMA 23 stepper driven by TB6600 motor driver 
    and Raspberry Pi Pico microcontroller.

    Properties:
    ------------
    steps_per_rev - steps per revolution, which is 200 or 1.8 deg per step for this motor.
    steps_per_mm - number of steps of motor required to travel 1 mm along its axis.
    microsteps_per_mm - number of microsteps of motor required to travel 1 mm along its axis.
    min_off_time - minimum duration of delays between step pulses for this motor.
    
    id - string to name motor.
    origin_direction - direction carriage moves to approach motor (dirn of decreasing position).
    duty_cycle_by_speed - all possible integer speeds and tuned values of PWM duty cycles for each.
    min_switch - LimitSwitch object that is used to set minimum reachable position along leadscrew.
    max_switch - LimitSwitch object that is used to set maximum reachable position along leadscrew.

    step_pin - GPIO pin (in BCM numbering) on the Pico to which step command PWM signal is sent.
    dirn_pin - GPIO pin (in BCM numbering) to which direction signal (low=CCW, high=CW) is sent.
    pulse_time - duration of step pulse sent to motor (i.e., on/high period in PWM signal).
    delay_time - time between consecutive step pulses (i.e., off/low period in PWM signal).
    direction - current direction setting for motor (which is sent to dirn_pin GPIO pin).
    position - current distance (in stepper pulses) between carriage and limit switch (origin).
    home_position - distance (in pulses) from min_switch when motor is in default (home) position.
    min_steps - approx. safe travel limit (in pulses) from origin in neg dirn, used in calibration.
    max_steps - approx. safe travel limit (in pulses) from min_switch to near end of leadscrew.

    Methods:
    ------------
    __init__ - create an instance of the class (a StepperMotor object) with ID, origin, switches, and tuned properties.
    setup - set properties of a StepperMotor object and set up GPIO pins for it.
    print_details - print all values of StepperMotor object properties.
    set_direction - switch StepperMotor direction property and send change to corresponding GPIO pin.
    set_speed - based on dictionary of tuned duty cycle values by speed, set timing properties for input speed.
    set_velocity - call set_direction and set_speed to change velocity.
    step - actuate through motor microstep(s) by sending a pulse/pulses to the GPIO pin corresponding to the STEP command.
    clear_switch_area - react to limit switch activation by moving away from the switch a safe distance.
    no_step - set STEP pin to low.
    home - move to home position.
    """
    # set relationships between steps, shaft angle, and linear travel distance as class variables 
    # since they don't change during normal operation and reflect physical/electrical setup
    steps_per_rev = FULL_STEPS_PER_MOTOR_REV
    steps_per_mm = FULL_STEPS_PER_MM
    microsteps_per_mm = FULL_STEPS_PER_MM*MICROSTEPS_PER_FULL_STEP
    min_off_time = MIN_PWM_OFF_TIME # 1 ms - min duration of low part of signal before motor stalls

    def __init__(self,name,switches):
        """
        Instantiates a StepperMotor object with origin direction, ID, and tuned PWM properties.
        """
        # Set motor name, origin, and switch assignments
        self.id = name
        self.origin_direction = CCW
        self.min_switch = switches[0]
        self.max_switch = switches[1]
        
        # validate switch assignment
        if not isinstance(self.min_switch, LimitSwitch):
            error_str = "Switch assigned to min. position is not a member of LimitSwitch class."
            raise TypeError(error_str)
        if not isinstance(self.max_switch, LimitSwitch):
            error_str = "Switch assigned to max. position is not a member of LimitSwitch class."
            raise TypeError(error_str)
        
        # Set values of PWM timing properties that have been tuned for best performance
        # with minimal vibration using the test_actuation script (2024-07-07)
        self.duty_cycle_by_speed = { # speed in mm/s : optimized duty cycle value
            10: 0.15, 9: 0.15, 8: 0.35, 7: 0.4, 6: 0.4, 5: 0.3, 0: 0
            }

    def setup(self,pin_assts,start_dirn,home_pos_mm,min_pos_mm,max_pos_mm):
        """
        Sets up a StepperMotor object by specifying pin assignments for direction and step signals
        (in the Pico GPIO), initializing timing properties (step pulse width, frequency, etc.), and
        setting positional properties (home position and axis limits, in number of drive pulses).
        """
        # assign control pins (must match physical circuit!) and initialize speed to 0
        self.step_pin = config_pin(pin_assts[0], "OUT")
        self.dirn_pin = config_pin(pin_assts[1], "OUT")
        self.set_speed(0)
        
        # set positional properties
        self.home_position = mm_to_pulses(home_pos_mm)
        self.min_steps = mm_to_pulses(min_pos_mm)
        self.max_steps = mm_to_pulses(max_pos_mm)

        # set starting position and direction and set step command to initially LOGIC_LOW
        self.position = self.home_position
        self.set_direction(start_dirn)
        self.no_step()
        print('INFO: %s motor set up!'%self.id)
    
    def print_details(self):
        """
        Prints values of all StepperMotor object property values for a given instance for verification.
        """
        print("STEPPER MOTOR OBJECT PROPERTIES =================")
        print("Motor ID is %s."%self.id)
        print("Each shaft revolution requires %d steps." % StepperMotor.steps_per_rev)
        print("Each step pulse lasts %f seconds and has a subsequent delay of %f seconds." %(self.pulse_time,self.delay_time))
        print("Step frequency is %f pulses/s, duty cycle is %f, and scalar carriage speed is %f mm/s." %(self.pulse_freq,self.duty_cycle,self.move_speed))
        if self.direction == CW:
            print("Current direction is clockwise.")
        elif self.direction == CCW:
            print("Current direction is counterclockwise.")
        if self.origin_direction == CW:
            print("Origin direction (direction of decreasing position) is clockwise.")
        elif self.origin_direction == CCW:
            print("Origin direction (direction of decreasing position) is counterclockwise.")
        #print("%d steps move %s motor 1 mm."%(StepperMotor.steps_per_mm,self.id))
        #print("Home position is %d steps and current position is %d steps."%(self.home_position,self.position))
        #print("Travel limit is %d steps." %self.max_steps)
        print("%d microsteps move %s motor 1 mm."%(StepperMotor.microsteps_per_mm,self.id))
        print("Home position is %d microsteps and current position is %d microsteps."%(self.home_position,self.position))
        print("Absolute travel limits located at %d and %d microsteps." %(self.min_steps,self.max_steps))
        print("=========================================")

    def set_direction(self,dirn,indicate_completion=False):
        """Changes the direction assigned to a StepperMotor object, validates value (CW=1/CCW=0) 
        and outputs direction signal to the corresponding GPIO output pin.
        """
        def validate_direction():
            """Checks that direction is 0 or 1 and that motor can safely move in this direction.
            """
            # check that direction value is either clockwise or counterclockwise
            if (dirn != CCW and dirn != CW):
                error_str = 'Direction set to {0} but should be CW (1) or CCW (0).'.format(dirn)
                raise ValueError(error_str)
            
            #check safety of moving in this direction
            else:
                # set positive and negative directions (away from and towards switch)
                loc = self.position
                pos_dirn = not self.origin_direction
                neg_dirn = self.origin_direction
                
                # check if there is space to move in current direction
                if (dirn == neg_dirn and loc < self.min_steps):
                    error_str = "Direction set to left but motor is too close to left switch!"
                    raise ValueError(error_str)
                elif (dirn == pos_dirn and loc > self.max_steps):
                    error_str = "Direction set to right but motor is too close to right switch!"
                    raise ValueError(error_str)
                
        # check direction and update object property and pin value
        validate_direction()
        self.direction = dirn
        set_pin(self.dirn_pin,dirn)
        if indicate_completion:
            print(COMPLETION_CODE)
    
    def set_speed(self,speed,indicate_completion=False):
        """Sets the appropriate stepper drive pulse on and off timings for a 
        provided speed (in mm/s) given the tuned duty cycle value for that speed
        and updates timing-related StepperMotor properties. 
        """
        def get_timings_from_speed(speed_mm):
            """Uses provided speed in mm/s to compute motor drive pulse timings in s.
            """
            # look up tuned duty cycle value for this speed (ensuring that it exists)
            # note: this constrains speed to be one of a small, finite set of integer values
            try:
                self.duty_cycle = self.duty_cycle_by_speed[speed_mm]
            except:
                raise KeyError("Speed of {0} not available in tuned speed-duty dictionary.".format(speed_mm))
            
            # convert mm/s to frequency in steps/s and get period
            self.pulse_freq = mm_to_pulses(speed_mm)
            if self.pulse_freq == 0:
                pulse_period = 0
            else:
                pulse_period = 1/self.pulse_freq
            
            # set timings based on pulse_period and duty cycle
            step_high_time = pulse_period*(self.duty_cycle)
            step_low_time = pulse_period*abs(1 - self.duty_cycle)
            return step_high_time,step_low_time
        
        def validate_timings(on_time,off_time):
            """Check that pulse timings meet minima and that duty cycle is reasonable.
            """
            # check that minimum delay (off) duration is not violated (for nonzero speeds)
            if (off_time < StepperMotor.min_off_time) and (abs(off_time) > 0):
                error_str = "PWM off-time {0} below min. value, {1}.".format(off_time,StepperMotor.min_off_time)
                raise ValueError(error_str)

            # check that duty cycle is not too high
            if on_time > off_time:
                error_str = "PWM off-time {0} less than on-time {1}, meaning duty cycle over 50%.".format(off_time,on_time)
                raise ValueError(error_str)
            
        # compute and validate pulse on-/off-time duration
        on_time_s,off_time_s = get_timings_from_speed(speed)
        validate_timings(on_time_s,off_time_s)

        # once validated, update pulse timing and speed properties
        self.move_speed = speed
        self.pulse_time = on_time_s
        self.delay_time = off_time_s
        if indicate_completion:
            print(COMPLETION_CODE)

    def set_velocity(self,dirn,speed,indicate_completion=False):
        """
        Uses set_direction and set_speed methods to set motor velocity.
        """
        self.set_direction(dirn,indicate_completion=False)
        self.set_speed(speed,indicate_completion=False)
        if indicate_completion:
            print(COMPLETION_CODE)

    def step(self,n=1,interrupts_on=True,print_pos=False,indicate_completion=False,calibrating=False,info=True):
        """
        Sends a pulse to the STEP output to actuate the stepper motor through n steps.
        """
        def check_input():
            #print("made it into check_input")
            if spoll.poll(0):
                serial_input = sys.stdin.read(1).strip()
                if serial_input == '':
                    #print("poll returns empty")
                    return None
                else:
                    print("poll returns something")
                    print(serial_input)
                    return serial_input
            else:
                #print("poll returns nothing")
                return None
        
        spoll=uselect.poll()
        spoll.register(sys.stdin,uselect.POLLIN)

        #TODO: add acceleration? time 0.1 for accel and decel
        step_display_interval = mm_to_pulses(0.1)
        for i in range(0,n):
            # pulse high then low to drive step
            pulse_pin(self.step_pin,self.pulse_time,self.delay_time)
            
            # update step count
            if self.direction == self.origin_direction:
                self.position = self.position - 1
            else:
                self.position = self.position + 1
            
            # if moving long distance, print position every 1 mm
            if print_pos and (i % step_display_interval == 0):
                #print('Current motor position is %s steps' %(str(self.position)))
                print(self.position)

            # check against max travel limit and stop process if this limit exceeded
            if self.position > self.max_steps:
                error_str = 'Travel limit exceeded in positive direction. '
                error_str = error_str + 'Reported current motor position is ' + str(self.position) + ' pulses. '
                error_str = error_str + 'Travel limit is ' + str(self.max_steps) + ' pulses.'
                raise ValueError(error_str)

            # check against max travel limit and stop process if this limit exceeded
            if self.position < self.min_steps:
                error_str = 'Travel limit exceeded in negative direction. '
                error_str = error_str + 'Reported current motor position is ' + str(self.position) + ' pulses. '
                error_str = error_str + 'Travel limit is ' + str(self.min_steps) + ' pulses.'
                raise ValueError(error_str)

            # stop stepping if limit switch hit or if stop command sent by PC
            self.max_switch.check_flag(interrupts_on)
            self.min_switch.check_flag(interrupts_on)
            if interrupts_on:
                # check if limit switches hit
                if self.max_switch.flag: 
                    if not calibrating: self.clear_switch_area(self.max_switch)
                    break
                
                if self.min_switch.flag:
                    if not calibrating: self.clear_switch_area(self.min_switch)
                    break

                #print("made it to interrupt block")
                if check_input() is not None:
                    #print("breaking")
                    break
                #print("made it past check_input")
                #if sys.stdin.readline().strip() == "STOP":
                #    self.no_step()
                #    break
                #TODO: check if sys available, check if sys works, check on delay
                # Alternatively: multithreading?? one thread running step(), one thread waiting for input, change global flag
                # potential issue: could get quite slow? unsure how threading affects timing.
                # in theory, this whole routine shouldn't be TOO intensive on Pico...in practice, it's possible the serial IO adds quite a bit of overhead

        if info: print("INFO: motor moved %d microsteps in direction %d."%(i+1,self.direction))
        if indicate_completion:
            print(COMPLETION_CODE)

    def clear_switch_area(self,cur_switch,stop_process=True):
        """
        When switch is activated by motor, steps motor back until minimum clearing distance from switch
        is reached then resets the switch status.
        """
        # set direction that takes carriage away from switch
        if cur_switch is self.min_switch:
            safe_direction = not self.origin_direction
        elif cur_switch is self.max_switch:
            safe_direction = self.origin_direction
        else:
            print("is command not working in clear_switch_area") #TODO: check this

        # check that we were actually moving toward the switch last time motor moved
        if self.direction == safe_direction:
            print("WARNING: switch has been opened but motor does not seem to be moving near switch.")
            print("Check direction settings for StepperMotor class.")

        # switch direction and step back to let switch close
        print("Entered clear switch")
        self.set_direction(safe_direction)
        steps_to_clear = mm_to_pulses(cur_switch.clearing_offset)
        self.step(steps_to_clear,interrupts_on=False)
        cur_switch.clear_flag()
        
        # if not calibrating, switch pressing is serious error, so end process
        if stop_process:
            error_string = 'WARNING: Limit switch activated unexpectedly. Actuation of motors stopping. '
            error_string = error_string + 'Reported current motor position is ' + str(self.position) + ' steps.'
            raise ValueError(error_string)
        
    def no_step(self,indicate_completion=False):
        """
        Sets STEP output to low for this motor to prevent any further steps.
        """
        set_pin(self.step_pin,LOGIC_LOW)
        if indicate_completion:
            print(COMPLETION_CODE)
    
    def home(self,homing_speed,indicate_completion=False):
        """
        Moves carriage to home position.
        """
        # get steps between current position and home position and find direction
        position_diff = int(self.position - self.home_position)
        if position_diff < 0:
            homing_dirn = not self.origin_direction
        elif position_diff > 0:
            homing_dirn = self.origin_direction

        # set velocity and then step until home position reached
        self.set_velocity(homing_dirn,homing_speed)
        switch_pressed = False
        while self.position != self.home_position: #TO DO: fix error that would keep this in infinite switch-pressing loop
            # likely fixed above TO DO? should stop either when clearing the first time or when switch is pressed a second time
            # take a step
            self.step()

            # check switches
            if self.min_switch.flag:
                self.clear_switch_area(self.min_switch,True)
                if switch_pressed:
                    raise UserWarning("Switch pressed during homing attempt!")
                else:
                    switch_pressed = True
            if self.max_switch.flag:
                self.clear_switch_area(self.max_switch,True)
                if switch_pressed:
                    raise UserWarning("Switch pressed during homing attempt!")
                else:
                    switch_pressed = True

        if indicate_completion:
            print(COMPLETION_CODE)
        return self.position
    
if __name__ == "__main__":
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

    # test motor
    # m.set_velocity(CCW,6)
    m.step(200)