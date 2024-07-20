'''
Script to test pneumatics control.
'''
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import devices

PORT = 'COM7'
BAUD = 19200
pdu = devices.PneumaticConnection(PORT,BAUD)
PROMPT_STRING = ">>>"

def startup(start_setpt=0):
    pdu.set_reference_setpoint(pdu.pos_string,start_setpt)
    pdu.set_reference_setpoint(pdu.neg_string,start_setpt)
    return pdu.get_pump_pressures(print_vals=True)

def get_and_regulate_target_pressure(be_verbose=False):
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
    
    def send_serial_commands_directly():
        serial_mode_done = False
        while not serial_mode_done:
            prompt = input("Enter a command, or press ENTER to finish.")
            if prompt == "":
                serial_mode_done = True
            else:
                print(pdu.send(prompt))
                print(pdu.receive())

    test_done = False
    while not test_done:
        # prompt = "Enter {0} to regulate input and {1} to regulate output.\n".format(0,1)
        # side_to_reg = get_user_integer(prompt,req_binary=True)
        prompt = "Enter desired pressure in kPa.\n"
        pressure_to_reg = get_user_integer(prompt)
        # pressure_targets = [pressure_to_reg]
        pump_id = pdu.bring_input_to_target(pressure_to_reg)
        print("{0} pump pressure is {1} kPa.".format(pump_id,pdu.get_pressure_value(pump_id)))
        device_id = pdu.base_output_string + str(0)
        device_pressure = float(pdu.open_valves_to_device(pump_id,device_id,pressure_to_reg))
        print("Current output {0} pressure at {1}".format(device_id,device_pressure))
        
        prompt = input("Press ENTER to finish, press R to keep regulating, or press S to switch to serial command direct entry.")
        if prompt == "S" or prompt == "s":
            send_serial_commands_directly()
        elif prompt == "":
            test_done = True
    assert isinstance(device_pressure,float),"pressure ({0}) is not float".format(device_pressure)

def communicate_through_serial_loop():
    pdu.enter_direct_serial()

if __name__ == "__main__":
    try:
        startup()
        get_and_regulate_target_pressure()
        communicate_through_serial_loop()
    finally:
        pdu.close()