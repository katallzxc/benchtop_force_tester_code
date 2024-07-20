''' MAIN v0.0 - Katherine Allison

Created: 2022-04-19
Updated: 2023-12-17

Opens graphical user interface (GUI) to control motor and read limit switches
and force gauge to run force test on material samples (in either pull-off or 
shear).

This is the main function for the testing process.
'''
from force_tester.helpers import conversions
from force_tester.helpers import files
from force_tester.helpers.constants import CCW,CW,MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD
from force_tester.helpers.constants import GAUGE_PORT,GAUGE_BAUD,PNEUMATICS_PORT,PNEUMATICS_BAUD
import force_tester.devices as devices
import force_tester.move as move
import force_tester.routines as routines
import force_tester.record as record
# TEMP
import force_tester.plot as plot

PULL = 0
PUSH = 1

NO_DEVICE_ID = 0
TEST_DEVICE_ID = 7
TEST_DEVICE_CHANNELS = 1
TEST_SLED_MASS = 87.2

def start_connections(actuator_port,actuator_baud,sensor_port,sensor_baud,device_port=None,device_baud=None):
    """Helper function to call class methods from devices.py to set up actuator and sensor.

    Args:
        actuator_port (string): port address for Pico-based motor control system
        actuator_baud (int): serial baud rate for Pico-based motor control system
        sensor_port (string): port address for force gauge
        sensor_baud (int): serial baud rate for force gauge

    Returns:
        mcu (ControllerConnection class object): object for serial connection to Pico-based motor control system
        fgu (GaugeConnection class object): object for serial connection to force gauge
    """
    mcu = devices.ControllerConnection(actuator_port,actuator_baud)
    fgu = devices.GaugeConnection(sensor_port,sensor_baud)
    pdu = None
    if not device_port is None:
        pdu = devices.PneumaticConnection(device_port,device_baud)
    return mcu,fgu,pdu

def stop_connections(mcu,fgu,pdu=None):
    mcu.close()
    fgu.close()
    if not pdu is None:
        pdu.close()

def setup_devices(mcu):
    """
    Setup function for motors and switches.
    """
    # set expected maximum step position along axis
    step_limit_guess = 1500

    # set properties of switch and motor objects
    switchL_name = '\'left\''
    switchL_args = (20,0,5,0.5)
    switchR_name = '\'right\''
    switchR_args = (18,step_limit_guess,5,0.5)
    mot_name = '\'main\''
    mot_args = ([13,12],CCW,100,-6,step_limit_guess)
    
    # send command to set up items and receive result
    #mcu_connection.send("setup_devices('left',"+switchL_args+",'right',"+switchR_args+",'main',"+mot_args+")")
    #TODO: fix dynamic setting of parameters
    setup_call = "setup_devices('left',(20,0,5,0.5),'right',(18,1000,5,0.5),'main',([13,12],CCW,100,-6,1000),True)"
    move.talk_to_actuator(mcu,setup_call,wait_for_completion=True)
    return True

def startup(use_pneumatics=True):
    #actuator,sensor = start_connections(actuator_port='COM3',actuator_baud=115200,sensor_port='COM4',sensor_baud=115200)
    # actuator,sensor = start_connections(actuator_port='COM6',actuator_baud=115200,sensor_port='COM5',sensor_baud=115200)
    
    # try to connect to devices
    if use_pneumatics:
        d_port = PNEUMATICS_PORT
        d_baud = PNEUMATICS_BAUD
    else:
        d_port = None
        d_baud = None
    actuator,sensor,pneumatics = start_connections(
        MOTOR_CONTROLLER_PORT,MOTOR_CONTROLLER_BAUD,GAUGE_PORT,GAUGE_BAUD,d_port,d_baud)

    # check that connections are successful and set up pneumatics (if applicable) and motor controller
    actuator.test_connection("2+2",verbose=True)
    sensor.test_connection()
    if use_pneumatics:
        pneumatics.test_connection()
        prompt_neutralize_pressures(pneumatics)
    setup_devices(actuator)

    return actuator,sensor,pneumatics

def run_calibration(actuator_device,slow_speed=6,fast_speed=10):
    move_input = input("If motor is far from left switch, enter a non-zero amount of mm to move back before calibration; else, press ENTER.\n") 
    #TODO: validate input
    if move_input != "":
        mm_to_move = float(move_input)
        if mm_to_move > 0:
            check_continue = input("Are you sure it's safe to move back by {0} mm? Enter M to move or hit ENTER to go straight to calibration.\n".format(mm_to_move))
            if (check_continue == "m" or check_continue == "M"):
                move.move_gauge_backward_dist(actuator_device,conversions.mm_to_pulses(mm_to_move),wait_for_completion=True)
    move.calibrate_motor(actuator_device,press_speed=slow_speed,travel_speed=fast_speed,wait_for_completion=True)

def prompt_neutralize_pressures(pneum_device):
    check_neutralize = input("Neutralize device and input pressures? Enter N or n to neutralize or hit ENTER to leave unchanged. ")
    if (check_neutralize == "n" or check_neutralize == "N"):
        pneum_device.neutralize_pressure()
    return check_neutralize

def prompt_direct_serial(pneum_device):
    check_serial = input("Any remaining serial commands? Enter SER (all caps) to send direct serial commands to pneumatics controller or hit ENTER to leave unchanged. ")
    if check_serial == "SER":
        pneum_device.enter_direct_serial()
    return check_serial

def prompt_move_stage(actuator_device):
    mm_moved = 0
    ready_to_start = False
    while not ready_to_start:
        move_dir = input("Enter 0 to move backward and 1 to move forward, or hit ENTER to use current position for test start.\n")
        if move_dir == "0":
            mm_to_move = float(input("How many mm to move back?\n")) #TODO: validate input
            mm_moved -= mm_to_move
            move.move_gauge_backward_dist(actuator_device,conversions.mm_to_pulses(mm_to_move),wait_for_completion=True)
        elif move_dir == "1":
            mm_to_move = float(input("How many mm to move forward?\n")) #TODO: validate input
            mm_moved += mm_to_move
            move.move_gauge_forward_dist(actuator_device,conversions.mm_to_pulses(mm_to_move),wait_for_completion=True)
        else:
            ready_to_start = True
    return mm_moved

def prompt_test_details(last_entries):
    prompt_individually = True

    # if recent values available, ask whether they should be used again
    if not(last_entries is None):
        test_description,curr_sled_mass,device_id_code,device_num_channels,tests_completed = last_entries
        last_entries_string = "Press X to enter test details individually, or press ENTER to use last entries from test {0}:".format(tests_completed)
        last_entries_string = last_entries_string + "\n* Description filestring: {0}\n* Sled mass [g]: {1}".format(test_description,curr_sled_mass)
        last_entries_string = last_entries_string + "\n* Device ID: {0}\n* Number of input channels: {1}\n".format(device_id_code,device_num_channels)
        use_last_entries = input(last_entries_string)
        if use_last_entries == "":
            prompt_individually = False
    
    # if recent values not used, prompt for individual parameters
    if prompt_individually:
        # get test description and sled mass
        test_description = input("Enter any additional string for data filename and then press ENTER.\n")
        curr_sled_mass = input("Enter the mass of the testing sled in grams, or hit ENTER to use the default value of {0}.\n".format(TEST_SLED_MASS))
        if curr_sled_mass == "": 
            curr_sled_mass = str(TEST_SLED_MASS)

        # get device ID code
        device_id_code = input("Enter the device ID, hit ENTER to use the default ID of {0}, or enter X if there is no device.\n".format(TEST_DEVICE_ID))
        if device_id_code == "": 
            device_id_code = str(TEST_DEVICE_ID)
        elif device_id_code == "X" or device_id_code == "x":
            device_id_code = str(NO_DEVICE_ID)

        # get number of input channels in device
        device_num_channels = input("Enter the number of device input channels, hit ENTER to use the default value of {0}, or enter X if there is no device.\n".format(TEST_DEVICE_CHANNELS))
        if device_num_channels == "": 
            device_num_channels = str(TEST_DEVICE_CHANNELS)
        elif device_num_channels == "X" or device_num_channels == "x":
            device_num_channels = str(NO_DEVICE_ID)

    return test_description,curr_sled_mass,device_id_code,device_num_channels

def prompt_stop_testing():
    check_continue = input("Stop testing process? Enter S to stop testing or hit ENTER to start another test.\n")
    if (check_continue == "s" or check_continue == "S"):
        all_tests_done = True
    else:
        all_tests_done = False
    return all_tests_done

def fill_parameter_dict(param_dict,strdesc,strmass,strID,strchannels,testnum):
    param_dict["motor pulses per mm"]=conversions.mm_to_pulses(1)
    param_dict["test description"]=strdesc
    param_dict["sled mass [g]"]=strmass
    param_dict["test device ID"]=strID
    param_dict["number of test device channels"]=strchannels
    param_dict["test number relative to last calibration"]=testnum
    return param_dict

def plot_curr_data(curr_data_log,auto_on=False,auto_title=None):
    try:
        test_file = files.crop_data_type_from_filename(curr_data_log)
        test_file = test_file + "_" + files.DATA_DESCRIPTORS[files.FORCE_TYPE] + files.FILE_EXT
        plot.command_line_plot("plot",curr_data=test_file,use_auto_plot=auto_on,auto_plot_title=auto_title)

    except:
        print("Plot failed")

    return test_file

def run_test_with_pneumatics():
    num_tests = 0
    test_param_values = None
    actuator,sensor,device = startup(use_pneumatics=True)
    run_calibration(actuator)
    try:
        all_tests_done = False
        while not all_tests_done:
            # move back more if needed and get test parameters
            prompt_move_stage(actuator)
            test_desc,sled_mass,device_id,device_channels = prompt_test_details(test_param_values)

            # run test routine
            print("Entering test routine.\n"+("*"*30))
            test_success,test_type,test_data,test_params = routines.simple_shear_test(sensor, actuator,device)
            print("Exiting test routine.\n"+("*"*30))
            if test_success == False:
                print("This test failed!")
                break
            else:
                num_tests += 1
            
            # record test parameters
            test_param_values = (test_desc,sled_mass,device_id,device_channels,num_tests)
            test_params = fill_parameter_dict(test_params,*test_param_values)
            test_name = test_type + test_desc
            test_file = record.record_all_test_data(test_name,test_data,test_params)

            # try to plot data, then check whether to keep testing
            test_file = plot_curr_data(test_file)
            all_tests_done = prompt_stop_testing()

            # prompt user to clean up pneumatics setup if necessary (e.g., vent pressure)
            prompt_neutralize_pressures(device)
            prompt_direct_serial(device)
    finally:
        stop_connections(actuator,sensor,device)

def run_test_without_pneumatics():
    num_tests = 0
    test_param_values = None
    actuator,sensor,device = startup(use_pneumatics=False)
    run_calibration(actuator) # current: slow 8, fast 12. Former: slow 8, fast 10
    try:
        all_tests_done = False
        while not all_tests_done:
            # move back more if needed and get test parameters
            prompt_move_stage(actuator)
            test_desc,sled_mass,device_id,device_channels = prompt_test_details(test_param_values)

            # run test routine
            print("Entering test routine.\n"+("*"*30))
            test_success,test_type,test_data,test_params = routines.simple_shear_test(sensor, actuator,device=None)
            print("Exiting test routine.\n"+("*"*30))
            if test_success == False:
                print("This test failed!")
                break
            else:
                num_tests += 1
            
            # record test parameters
            test_param_values = (test_desc,sled_mass,device_id,device_channels,num_tests)
            test_params = fill_parameter_dict(test_params,*test_param_values)
            test_name = test_type + test_desc
            test_file = record.record_all_test_data(test_name,test_data,test_params)

            # try to plot data, then check whether to keep testing
            test_file = plot_curr_data(test_file)
            all_tests_done = prompt_stop_testing()
    finally:
        stop_connections(actuator,sensor)

if __name__ == "__main__":
    use_pneumatics = True
    if use_pneumatics:
        run_test_with_pneumatics()
    else:
        run_test_without_pneumatics()