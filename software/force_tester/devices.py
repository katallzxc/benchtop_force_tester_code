''' DEVICES v1.0 - Katherine Allison

Created: 2022-04-19
Updated: 2023-05-26

Defines objects for microcontroller as well as force gauge.

Changelog:
- troubleshooting of GaugeConnection object
- adding methods to GaugeConnection object to use specific reading request commands + postprocess reading values
'''
# test of serial code found at http://blog.rareschool.com/2021/01/controlling-raspberry-pi-pico-using.html
# also used https://medium.com/geekculture/serial-connection-between-raspberry-pi-and-raspberry-pico-d6c0ba97c7dc 
import serial
import time

class ControllerConnection:
    TERMINATOR = '\r'.encode('UTF8')

    def __init__(self, device='COM3', baud=115200, timeout=1):
        self.serial = serial.Serial(device, baud, timeout=timeout)

    def receive(self) -> str:
        line = self.serial.read_until(self.TERMINATOR)
        return line.decode('UTF8').strip()

    def send(self, text: str, print_echo=False) -> bool:
        line = '%s\r\f' % text
        self.serial.write(line.encode('UTF8'))
        echo = self.receive()
        if print_echo: print("Echo of motor command is: {0}".format(echo))
        return text == echo
    
    def test_connection(self,test_string,verbose=True):
        sent_successfully = self.send(test_string)
        if (not sent_successfully and verbose):
            print("Warning: sending data to Pico microcontroller over serial appears to be broken")

        returned = self.receive()
        if verbose: 
            print("When %s sent to Pico, Pico returned %s." %(test_string,str(returned)))

    def close(self):
        self.serial.close()

class GaugeConnection:
    TERMINATOR = '\r'.encode('UTF8')
    REQUEST_CODE = "?"
    ERROR_CODE = "*10"
    ERROR_FLAG = 99

    def __init__(self, device='COM4', baud=115200, timeout=1):
        self.serial = serial.Serial(device, baud, timeout=timeout)

    def receive(self) -> str:
        line = self.serial.read_until(self.TERMINATOR)
        return line.decode('UTF8').strip()

    def send(self, text: str) -> bool:
        line = '%s\r' % text # using only carriage return here because line feed causes errors
        self.serial.write(line.encode('UTF8'))
        return 
    
    def request_reading(self) -> str:
        # sends ? command to get measurement and returns value as string reading
        self.send(self.REQUEST_CODE)
        return self.receive()

    def get_force_measurement(self, timeout: float = 0.1) -> float:
        # sends ? command to get measurement and returns value with N unit suffix stripped
        # keep requesting gauge reading until non-erroneous return value
        curr_measurement = self.request_reading()
        if curr_measurement == self.ERROR_CODE: #TODO: reconsider whether these error code readings should be thrown out?
            start_time = time.time()
            while curr_measurement == self.ERROR_CODE:
                curr_time = time.time()
                if (curr_time-start_time) > timeout:
                    print("Force gauge returning error code for at least %d seconds!"%timeout)
                    return self.ERROR_FLAG
                
                curr_measurement = self.request_reading()
            print("After initial error code(s), force gauge measurement obtained after %d seconds" % (curr_time-start_time))
        
        # strip unit from return value
        if curr_measurement[-2:] == " N":
            return float(curr_measurement[:-2])
        else:
            print("Force gauge returning value with incorrect units!")
            return self.ERROR_FLAG
        
    def test_connection(self):
        returned = self.get_force_measurement()
        print("Test reading request to force gauge returned %d N"%returned)

    def close(self):
        self.serial.close()

class PneumaticConnection:
    TERMINATOR = '\r'.encode('UTF8')
    FILLER_STRING = 999
    
    def __init__(self, device='COM7', baud=19200, timeout=1):
        # establish serial connection and set basic booleans
        self.serial = serial.Serial(device, baud, timeout=timeout)
        self.ON,self.OFF = 1,0
        self.OPEN,self.CLOSED = 1,0
        # set input indices
        self.pos_string = "POS"
        self.neg_string = "NEG"
        self.neu_string = "NEU"
        self.input_strings = [self.neg_string,self.neu_string,self.pos_string]
        self.pump_strings = [self.neg_string,self.pos_string]
        self.pumps,self.valves,self.sensors = self.define_input_indices()
        # set output indices
        self.base_output_string = "OUT"
        self.num_out_channels = 1
        self.output_strings = [self.base_output_string + str(i) for i in range(self.num_out_channels)]
        self.define_output_indices()

    def define_input_indices(self):
        pump_indices = {
            self.neg_string:0,
            self.pos_string:1
        }
        valve_indices = {
            self.neg_string:0,
            self.neu_string:1,
            self.pos_string:2,
        }
        sensor_indices = {
            self.neg_string:0,
            self.pos_string:1
        }
        return pump_indices,valve_indices,sensor_indices

    def define_output_indices(self):
        for i in range(self.num_out_channels):
            self.valves[self.output_strings[i]] = i
            self.sensors[self.output_strings[i]] = i

    def assemble_command(self,command_code, id=None, val=None,print_command=False):
        if not (isinstance(val,int) or isinstance(id,int)):
            print("Incorrect serial command call for pneumatics")
            raise TypeError
        elif not isinstance(id,int):
            id = PneumaticConnection.FILLER_STRING
        elif not isinstance(val,int):
            val = PneumaticConnection.FILLER_STRING
        command_string = '<{0},{1},{2}>'.format(command_code,id,val)
        if print_command: print(command_string)
        return command_string 

    def receive(self) -> str:
        line = self.serial.read_until(self.TERMINATOR)
        return line.decode('UTF8').strip()

    def send(self, text:str) -> bool:
        line = '%s\n'%(text)
        self.serial.write(line.encode('UTF8'))
        echo = self.receive()
        command_only = text[1:-1]
        return echo == command_only
    
    def set_single_valve(self,valve_string,valve_state):
        # define serial commands and get command string
        SET_SINGLE_IN_VALVE = "SI"  # command format: <SI, valve #, valve state>
        SET_SINGLE_OUT_VALVE = "SO" # command format: <SO, valve #, valve state>
        if valve_string in self.input_strings:
            command_str = SET_SINGLE_IN_VALVE
        else:
            command_str = SET_SINGLE_OUT_VALVE

        # send serial command
        valve_id = self.valves[valve_string]
        full_command = self.assemble_command(command_str,id=valve_id,val=valve_state)
        self.send(full_command)
    
    def set_valve_group(self,use_inputs,valve_state):
        # define serial commands and get command string
        SET_ALL_IN_VALVES = "AI"    # command format: <AI, 999, valve state>
        SET_ALL_OUT_VALVES = "AO"   # command format: <AO, 999, valve state>
        if use_inputs:
            command_str = SET_ALL_IN_VALVES
        else:
            command_str = SET_ALL_OUT_VALVES

        # send serial command
        full_command = self.assemble_command(command_str,val=valve_state)
        self.send(full_command)

    def get_valve_state(self,valve_string): #TODO: returns None
        # define serial commands and get command string
        GET_IN_VALVE_STATE = "VI"  # command format: <VI, valve #, 999>
        GET_OUT_VALVE_STATE = "VO" # command format: <VO, valve #, 999>
        if valve_string in self.input_strings:
            command_str = GET_IN_VALVE_STATE
        else:
            command_str = GET_OUT_VALVE_STATE

        # send serial command
        valve_id = self.valves[valve_string]
        full_command = self.assemble_command(command_str,id=valve_id)
        self.send(full_command)

    def get_pressure_value(self,sensor_string):
        # define serial commands and get command string
        GET_IN_PRESSURE = "GI"      # command format: <GI, sensor #, 999>
        GET_OUT_PRESSURE = "GO"     # command format: <GO, sensor #, 999>
        if sensor_string in self.input_strings:
            command_str = GET_IN_PRESSURE
        else:
            command_str = GET_OUT_PRESSURE

        # send serial command
        sensor_id = self.sensors[sensor_string]
        full_command = self.assemble_command(command_str,id=sensor_id)
        self.send(full_command)
        return self.receive()
    
    def set_reference_setpoint(self,pump_string,pump_setpt):
        # define serial commands and get command string
        SET_REF_SETPOINT = "RS"    # command format: <RS, pump #, pump setpoint>
        command_str = SET_REF_SETPOINT
        pump_id = self.pumps[pump_string]

        # send serial command
        full_command = self.assemble_command(command_str,id=pump_id,val=pump_setpt)
        self.send(full_command)
    
    def get_reference_setpoint(self,pump_string): #TODO: returns None
        # define serial commands and get command string
        GET_REF_SETPOINT = "RG"    # command format: <RG, pump #, 999>
        command_str = GET_REF_SETPOINT
        pump_id = self.pumps[pump_string]

        # send serial command
        full_command = self.assemble_command(command_str,id=pump_id)
        self.send(full_command)
    
    def set_pump_state(self,pump_string,pump_state):
        # define serial commands and get command string
        SET_PUMP_STATE = "PS"    # command format: <PS, pump #, pump state>
        command_str = SET_PUMP_STATE
        pump_id = self.pumps[pump_string]

        # send serial command
        full_command = self.assemble_command(command_str,id=pump_id,val=pump_state)
        self.send(full_command)
    
    def get_pump_state(self,pump_string): #TODO: returns None
        # define serial commands and get command string
        GET_PUMP_STATE = "PG"    # command format: <PG, pump #, 999>
        command_str = GET_PUMP_STATE
        pump_id = self.pumps[pump_string]

        # send serial command
        full_command = self.assemble_command(command_str,id=pump_id)
        self.send(full_command)
    
    def get_pump_pressures(self,print_vals=False):
        neg_pump_pressure = self.get_pressure_value(self.neg_string)
        pos_pump_pressure = self.get_pressure_value(self.pos_string)
        if print_vals:
            print("Negative pump pressure: {0}\nPositive pump pressure: {1}".format(neg_pump_pressure,pos_pump_pressure))
        return [neg_pump_pressure,pos_pump_pressure]

    def switch_input_channel(self,valve_string,delay_time=5,evacuate=True):
        # close all input valves then perform neutral evacuation
        if evacuate:
            print("Performing neutral evacuation")
            self.set_valve_group(True, self.CLOSED)
            self.set_single_valve(self.neu_string, self.OPEN)
            time.sleep(delay_time)

        # open desired input valve
        self.set_single_valve(self.neu_string, self.CLOSED)
        if valve_string in self.input_strings:
            self.set_single_valve(valve_string, self.OPEN)
        else:
            print("Input channel switch routine called on non-input valve!")
            raise ValueError
    
    def set_target_pressure(self,target):
        if target > 0:
            pump_to_use = self.pos_string
        else:
            pump_to_use = self.neg_string
        self.set_reference_setpoint(pump_to_use,target)
        return pump_to_use
    
    def check_pressure_against_target(self,target,sensor_str):
        curr = float(self.get_pressure_value(sensor_str))
        curr_diff = abs(curr - target)
        return curr_diff

    def bring_input_to_target(self,target_pressure,timeout = 5):
        # get target pump and whether pressure should be higher or lower
        target_pump = self.set_target_pressure(target_pressure)
        if target_pump == self.pos_string:
            delta_direction = 1
        elif target_pump == self.neg_string:
            delta_direction = -1

        # keep checking pressure until timeout or target reached
        start_time = time.time()
        target_reached = False
        while (not target_reached and (time.time()-start_time) < timeout):
            curr_pressure = float(self.get_pressure_value(target_pump))
            if delta_direction*(curr_pressure - target_pressure) > 0:
                target_reached = True
        return target_pump
    
    def open_valves_to_device(self,input_str,output_str,target_pressure,timeout = 5):
        # check if current device pressure is far from desired
        # if current pressure is far from desired, set neutral evacuation flag
        curr_pressure_diff = self.check_pressure_against_target(target_pressure,output_str)
        print("Current pressure difference is %f"%curr_pressure_diff)
        if curr_pressure_diff < 10:
            evacuate_first = False
        else:
            evacuate_first = True

        # switch active input channel to desired input
        print("Switching input channel to %s"%input_str)
        self.switch_input_channel(input_str,evacuate=evacuate_first)

        # open output channel
        print("Opening output %s"%output_str)
        self.set_single_valve(output_str,self.OPEN)
        start_time = time.time()
        target_reached = False
        while (not target_reached and (time.time()-start_time) < timeout):
            curr_pressure_diff = self.check_pressure_against_target(target_pressure,output_str)
            if curr_pressure_diff < 5:
                target_reached = True
        return self.get_pressure_value(output_str)
    
    def neutralize_pressure(self,open_all_inputs=True,output_str=None,delay_time=5):
        # Set pump setpoints to 0
        print("Clearing reference setpoints to stop regulating")
        self.set_valve_group(True, self.CLOSED)
        self.set_reference_setpoint(self.neg_string,0)
        self.set_reference_setpoint(self.pos_string,0)
        # Evacuate pressure in channels
        if open_all_inputs:
            print("Opening input channels")
            self.set_single_valve(self.neu_string,self.OPEN)
            self.set_single_valve(self.neg_string,self.OPEN)
            time.sleep(delay_time)
            self.set_single_valve(self.pos_string,self.OPEN)
            time.sleep(delay_time)
        else:
            print("Opening neutral channel")
            self.set_single_valve(self.neu_string,self.OPEN)
        # Evacuate pressure in device
        if output_str is None:
            output_str = self.output_strings[0]
        print("Opening output {0} for {1} seconds".format(output_str,delay_time))
        self.set_single_valve(output_str,self.OPEN)
        time.sleep(delay_time)
        return self.get_pressure_value(output_str)
    
    def enter_direct_serial(self): #TODO: listen until done
        def list_serial_commands():
            print("Possible serial command entries are:")
            for command in serial_command_dict:
                command_method,relevant_components = serial_command_dict[command]
                print(" * {0} : to call {1} method for {2}".format(command,str(command_method),relevant_components))

        def execute_serial_command(cmd,str_id,int_val):
            if (cmd == "SI" or cmd == "SO" or cmd == "RS" or cmd == "PS"):
                serial_command_dict[cmd][0](str_id,int_val)
            elif cmd == "AI":
                serial_command_dict[cmd][0](use_inputs=True,valve_state=int_val)
            elif cmd == "AO":
                serial_command_dict[cmd][0](use_inputs=False,valve_state=int_val)
            elif (cmd == "GI" or cmd == "GO" or cmd == "VI" or cmd == "VO" or cmd == "PG" or cmd == "RG"):
                print(serial_command_dict[cmd][0](str_id))

        # Initialize dictionary of possible serial commands
        serial_command_dict = {
            "SI": (self.set_single_valve,"input valves"),
            "SO": (self.set_single_valve,"output valves"),
            "AI": (self.set_valve_group,"input valves"),
            "AO": (self.set_valve_group,"output valves"),
            "GI": (self.get_pressure_value,"input sensors"),
            "GO": (self.get_pressure_value,"output sensors"),
            "VI": (self.get_valve_state,"input valves"),
            "VO": (self.get_valve_state,"output valves"),
            "RS": (self.set_reference_setpoint,"positive or negative pump reference setpoints"),
            "RG": (self.get_reference_setpoint,"positive or negative pump reference setpoints"),
            "PS": (self.set_pump_state,"positive or negative pumps"),
            "PG": (self.get_pump_state,"positive or negative pumps"),
        }
        serial_ID_dict = {
            "SI": self.input_strings,
            "SO": self.output_strings,
            "AI": [PneumaticConnection.FILLER_STRING],
            "AO": [PneumaticConnection.FILLER_STRING],
            "GI": self.pump_strings,
            "GO": self.output_strings,
            "VI": self.input_strings,
            "VO": self.output_strings,
            "RS": self.pump_strings,
            "RG": self.pump_strings,
            "PS": self.pump_strings,
            "PG": self.pump_strings,
        }
        serial_val_dict = {
            "SI": [self.CLOSED,self.OPEN],
            "SO": [self.CLOSED,self.OPEN],
            "AI": [self.CLOSED,self.OPEN],
            "AO": [self.CLOSED,self.OPEN],
            "GI": [PneumaticConnection.FILLER_STRING],
            "GO": [PneumaticConnection.FILLER_STRING],
            "VI": [PneumaticConnection.FILLER_STRING],
            "VO": [PneumaticConnection.FILLER_STRING],
            "RS": [],
            "RG": [PneumaticConnection.FILLER_STRING],
            "PS": [self.OFF,self.ON],
            "PG": [PneumaticConnection.FILLER_STRING],
        }
        # List commands for user
        print("-"*80)
        print("Entering direct serial communication with pneumatics")
        list_serial_commands()

        # Prompt user repeatedly
        num_commands = 0
        direct_serial_done = False
        while not direct_serial_done:
            command_prompt = input("Enter serial command, or enter LIST to see list of possible commands, or press ENTER to finish.")
            if command_prompt == "":
                direct_serial_done = True
            elif command_prompt == "LIST":
                list_serial_commands()
            
            # if user enters valid serial command, get values to include with command
            else:
                if not command_prompt in serial_command_dict:
                    print("Please enter valid serial command from list.")
                else:
                    # prompt for ID (if applicable)
                    option_list = serial_ID_dict[command_prompt]
                    if len(option_list)>1:
                        print("Available ID options:")
                        print(option_list)
                        valid_ID_entered = False
                        while not valid_ID_entered:
                            ID_prompt = input("Select ID from option list.")
                            if not ID_prompt in option_list:
                                print("Please enter valid ID from list.")
                            else:
                                valid_ID_entered = True
                    elif len(option_list) == 1:
                        ID_prompt = option_list[0]

                    # prompt for value (if applicable)
                    option_list = serial_val_dict[command_prompt]
                    if len(option_list)==0:
                        val_prompt = int(input("Enter integer to set reference setpoint pressure value."))
                    elif len(option_list)>1:
                        print("Available value options:")
                        print(option_list)
                        valid_val_entered = False
                        while not valid_val_entered:
                            val_prompt = int(input("Select value from option list."))
                            if not val_prompt in option_list:
                                print("Please enter valid value from list.")
                            else:
                                valid_val_entered = True
                    elif len(option_list) == 1:
                        val_prompt = option_list[0]

                    # execute serial command
                    execute_serial_command(command_prompt,ID_prompt,val_prompt)
                    num_commands += 1

        return num_commands
        
    def test_connection(self,verbose=True):
        if verbose: 
            print("Test pneumatics pump pressure query returned:")
        return self.get_pump_pressures(verbose)

    def close(self):
        self.serial.close()

if __name__ == "__main__":
    mcu = ControllerConnection('COM3',115200)
    send_flag = mcu.send("2+2")
    print(send_flag)
    return_msg = mcu.receive()
    #left_switch,right_switch,stepper = setup_devices(mcu,"left",(20,5,0.5),"right",(18,5,0.5),"main",([13,12],CCW,100,-6,1000))
    print(return_msg)

    mcu.send("LED_blink()")
    return_msg = mcu.receive()
    while len(return_msg) > 0:
        print(return_msg)
        return_msg = mcu.receive()

    print("send digit test")
    mcu.send("0")
    return_msg = mcu.receive()
    while len(return_msg) > 0:
        print(return_msg)
        return_msg = mcu.receive()

    fgu = GaugeConnection('COM4',115200)
    print("gauge object")
    for i in range(0,10):
        print(fgu.get_force_measurement())
        time.sleep(0.1)
        
    pneum = PneumaticConnection('COM7',19200)