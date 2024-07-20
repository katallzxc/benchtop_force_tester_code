''' ROUTINES v1.0 - Katherine Allison

Created: 2023-11-15
Updated: 2024-02-04

Defines test routines. 
Routines take test parameters (e.g., force targets) as inputs along with gauge and motor objects. 
Routines return test data (one or more data arrays in a dictionary) as an output along with a 
string for the type of test. Dictionaries use constants for data types from record.py as keys.

This module should contain definitions for all types of tests run using the force tester.
'''
import time
import numpy as np
import force_tester.move as move
# import grip
from force_tester.helpers import conversions
from force_tester.helpers import files

SHEAR_TEST = "shear"

def fill_data_dict(data_dict,data_type,data_array):
    data_dict[data_type] = data_array
    return data_dict

def record_routine_parameters(strtype,strflag,duration,limits,targets):
    routine_params = {
        "test type":strtype,
        "test succeeded":strflag,
        "test duration [seconds]":duration,
        "time limits [nanoseconds]":limits[0],
        "position limits [mm]":limits[1],
        "force limits [N]":limits[2],
        "force targets [N]":targets[0],
        "pressure targets [kPa]":targets[1]
    }
    return routine_params

def simple_shear_test(force_gauge, stepper, device=None):
    """Function that runs a simple shear adhesion test with retreat only.

    Args:
        force_gauge (GaugeConnection): object for connection to force gauge
        stepper (ControllerConnection): object for connection to Pico-based motor controller system
    """
    # set motor parameters (acceleration, deceleration, starting vel, running vel)
    # set acceleration time to 0.1s
    # set deceleration time to 0.1s
    # set starting velocity to 5 um/s
    # set running velocity to 5 um/s
    if device is None:
        use_pneumatics = False
    else:
        use_pneumatics = True

    # set limits and buffers
    noforce_limit_seconds = 5
    time_limits = {
        "serial":conversions.sec_to_ns(0.1), #seconds
        "no force":conversions.sec_to_ns(noforce_limit_seconds)
        } #TODO: fix no force counter
    print("Time limit for near-zero force readings before routine ends is {0} seconds or {1} nanoseconds.".format(noforce_limit_seconds,time_limits["no force"]))
    pos_limit = 500 #100 # in mm
    force_limit = 20 # in N - gauge capacity 25 N
    force_buffer = 0.02 # in N, decreased from 0.05 due to low sled mass

    # set targets
    force_targets = []
    pressure_targets = []

    # set initial counters
    reading_count = -1
    noforce_timer = 0

    # size output arrays
    array_rows = 50000 #TODO: fix size
    force_readings = np.empty((array_rows,2))
    position_reports = np.empty((array_rows,2))
    if use_pneumatics:
        pressure_data = np.empty((array_rows,3))

    # check device connection (if running with pneumatics)
    if use_pneumatics:
        press_target = int(input("Enter desired target pressure in kPa. "))
        pressure_targets.append(press_target)
        device.test_connection()
        try:
            pump_id = device.bring_input_to_target(press_target)
            device_id = device.base_output_string + str(0)
            device_pressure = device.open_valves_to_device(pump_id,device_id,press_target)
            print("Current output {0} pressure at {1}".format(device_id,device_pressure))
        except:
            raise UserWarning("Device not initialized!")
    
    start_test = input("Press ENTER to start test, or press any key to cancel. ")
    if start_test != "":
        print("Cancelling test. ")
        move.stop_motor(stepper)
        return False, None, None, None

    # set timing parameters and booleans
    start_time = time.time_ns()
    serial_timeout = conversions.ns_to_sec(time_limits["serial"])

    # take test force reading
    cur_reading = force_gauge.get_force_measurement(timeout=serial_timeout)
    print("Test force reading is %f"%(cur_reading,))

    # start test, moving steadily backward until force threshold reached
    # take readings continuously during scripted motor actions
    print("Starting test. Now retreating to maximum %f mm travel distance."%pos_limit)
    pulses_to_move = conversions.mm_to_pulses(pos_limit)
    move.quick_backward_dist(stepper,pulses_to_move)
    test_done = False
    pulling = False
    zero_force = False
    while not test_done:
        # if at reading time, take a reading and increment count
        reading_count += 1
        cur_reading = force_gauge.get_force_measurement(timeout=serial_timeout)
        force_readings[reading_count][0] = int(time.time_ns()-start_time)
        force_readings[reading_count][1] = cur_reading

        # take next disp reading
        cur_position = move.quick_listen(stepper)
        if cur_position == move.INVALID_POS: 
            print ("Stepper position reported as %s"%cur_position)
        position_reports[reading_count][0] = int(time.time_ns()-start_time)
        position_reports[reading_count][1] = cur_position
        # TODO: consider adding a logical ID, incremented per iteration of loop

        # take next pressure reading
        if use_pneumatics:
            cur_pressure = device.get_pressure_value(device_id)
            pressure_data[reading_count][0] = int(time.time_ns()-start_time)
            pressure_data[reading_count][1] = cur_pressure
            pressure_data[reading_count][2] = press_target

        if abs(cur_reading) > force_limit:
            print("Force limit exceeded, stopping test.")
            move.stop_motor(stepper) # slow stop = de-accelerate first TODO
            test_done = True

        # depending on current stage of script, take motor actions in response to data
        if not pulling:
            if abs(cur_reading) > force_buffer:
                print("Nonzero force reading of %f at position %d."%(cur_reading,conversions.pulses_to_mm(cur_position)))
                #stop_motor(stepper) # slow stop = de-accelerate first TODO
                pulling = True

        else:
            if abs(cur_reading) < force_buffer:
                if not zero_force:
                    zero_force = True
                    noforce_start = time.time_ns()
                    try:
                        print("Zero force reading at position %d"%conversions.pulses_to_mm(cur_position))
                    except:
                        print("oops!")
                else:
                    noforce_timer = time.time_ns() - noforce_start
                    if noforce_timer >= time_limits["no force"]:
                        print("Done test, now wrapping up.")
                        move.stop_motor(stepper) # slow stop = de-accelerate first TODO
                        test_done = True

    #TODO: error handler that returns data so far even if error occurs
    # when done test, resize output arrays
    force_readings = force_readings[0:reading_count,:]
    position_reports = position_reports[0:reading_count,:]
    if use_pneumatics:
        pressure_data = pressure_data[0:reading_count,:]

    # get duration and print results for maximum adhesion force
    test_duration = conversions.ns_to_sec(int(time.time_ns()-start_time))
    print("Maximum frictional force in %d readings over %f seconds: %f N." % (reading_count,test_duration,min(force_readings[:,1])))
    print("Total travel distance: %f mm." % conversions.pulses_to_mm(max(position_reports[:,1])-min(position_reports[:,1])))

    # organize parameter data
    limits = (time_limits,pos_limit,force_limit)
    targets = (force_targets,pressure_targets)

    # put output and parameter data in dictionary
    output_data = {
        files.FORCE_TYPE:force_readings,
        files.POSITION_TYPE:position_reports,
    }
    if use_pneumatics:
        output_data[files.PRESSURE_TYPE] = pressure_data
    parameter_data = record_routine_parameters(SHEAR_TEST,test_done,test_duration,limits,targets)
    return test_done,SHEAR_TEST,output_data,parameter_data

# def simple_pulloff_test(preload_target, force_gauge, stepper):
#     """Function that runs a simple pull-off adhesion test with preload, dwelling, and retreat.

#     Args:
#         preload_target (float): target preload force in N
#         force_gauge (GaugeConnection): object for connection to force gauge
#         stepper (ControllerConnection): object for connection to Pico-based motor controller system
#     """

#     # options for getting correlation between motor and sensor data:
#     # 1) get timing of in/out signals from/to motor and get position at motor stop and figure it out
#     # 2) send shorter motor commands more frequently 

#     # set motor parameters (acceleration, deceleration, starting vel, running vel)
#     # set acceleration time to 0.1s
#     # set deceleration time to 0.1s
#     # set starting velocity to 5 um/s
#     # set running velocity to 5 um/s

#     # set force gauge parameters (reading interval)
#     read_interval = 0.3 # in seconds
#     move_distance = 100 # in mm

#     # set limits and buffers
#     preload_target_buffer = 0.1 # in N
#     noforce_buffer = 0.05 # in N
#     dwell_time_limit = 50*read_interval
#     noforce_time_limit = 80*read_interval

#     # set counter variables
#     reading_count = 0
#     noforce_time_count = 0
#     dwell_time_count = 0

#     # set initial flag variables
#     test_done = False
#     approaching = True
#     dwelling = False

#     # size output array
#     force_readings = np.empty((5000,2)) #TODO: fix size

#     # take readings continuously during scripted motor actions
#     print("Starting test, now approaching to maximum %f mm travel distance."%100)
#     steps_to_move = conversions.mm_to_steps(move_distance)
#     move.move_gauge_forward_dist(stepper,steps_to_move)# set distance to travel (in steps) to 6000 (likely microsteps)
#     start_time = time.time()
#     while not test_done:
#         # take a reading and increment count
#         cur_reading = force_gauge.get_force_measurement(timeout=read_interval)
#         force_readings[reading_count][0] = cur_reading
#         force_readings[reading_count][1] = time.time()-start_time
#         reading_count += 1

#         # depending on current stage of script, take motor actions in response to data
#         if approaching:
#             if abs(cur_reading - preload_target) < preload_target_buffer:
#                 print("Done approaching, now dwelling for %d seconds."%(dwell_time_limit*read_interval))
#                 move.stop_motor(stepper) # slow stop = de-accelerate first TODO
#                 approaching = False
#                 dwelling = True

#         elif dwelling:
#             dwell_time_count += 1
#             if dwell_time_count >= dwell_time_limit:
#                 print("Done dwelling, now pulling away.")
#                 steps_to_move = conversions.mm_to_steps(move_distance*0.5) #DIS -7000, MI
#                 move.move_gauge_backward_dist(stepper,steps_to_move)
#                 dwelling = False

#         elif abs(cur_reading) < noforce_buffer:
#             noforce_time_count += 1
#             if noforce_time_count >= noforce_time_limit:
#                 print("Done test, now wrapping up.")
#                 move.stop_motor(stepper) # slow stop = de-accelerate first TODO
#                 test_done = True

#     # when done test, resize output array and print results for maximum adhesion force
#     force_readings = force_readings[0:reading_count,:]
#     print("Maximum adhesive force in %d readings: %f N." % (reading_count,max(abs(force_readings[:,0]))))
#     return force_readings, "pulloff"

# def simple_shear_test_gripper(preload_target, force_gauge, stepper):
    # """Function that runs a simple shear adhesion test with preload, dwelling, and retreat.
    # This function is designed for testing force required to pull object from gripper.

    # Args:
    #     preload_target (float): target preload force in N
    #     force_gauge (GaugeConnection): object for connection to force gauge
    #     stepper (ControllerConnection): object for connection to Pico-based motor controller system
    # """

    # # set motor parameters (acceleration, deceleration, starting vel, running vel)
    # # set acceleration time to 0.1s
    # # set deceleration time to 0.1s
    # # set starting velocity to 5 um/s
    # # set running velocity to 5 um/s

    # # set force gauge parameters (reading interval)
    # read_interval = 0.3 # in seconds
    # move_distance = 100 # in mm

    # # set limits and buffers
    # preload_target_buffer = 0.1 # in N
    # noforce_buffer = 0.05 # in N
    # dwell_time_limit = 50*read_interval
    # noforce_time_limit = 80*read_interval

    # # set counter variables
    # reading_count = 0
    # noforce_time_count = 0
    # dwell_time_count = 0

    # # set initial flag variables
    # test_done = False
    # closing = True
    # opening = False
    # dwelling = False

    # # size output array
    # force_readings = np.empty((5000,2)) #TODO: fix size

    # # take readings continuously during scripted motor actions
    # print("Starting grip test, now closing gripper.")
    # start_time = time.time()
    # while not test_done:
    #     # take a reading and increment count
    #     cur_reading = force_gauge.get_force_measurement(timeout=read_interval)
    #     force_readings[reading_count][0] = cur_reading
    #     force_readings[reading_count][1] = time.time()-start_time
    #     reading_count += 1

    #     # check gripper conditions
    #     #TODO: gripper code here
    #     cur_gripper_pos = 0 #change me

    #     # depending on current stage of script, take motor and gripper actions in response to data
    #     if closing:
    #         # create preload with gripper closure
    #         #TODO: gripper code here (or possibly before loop)
    #         # basically slowly close until we've closed enough to hit target closure force (probably fully close)

    #         if abs(cur_reading - preload_target) < preload_target_buffer:
    #             print("Done closing, now opening.")
    #             closing = False
    #             opening = True

    #     elif opening:
    #         #TODO: gripper code here
    #         # basically slowly open to desired position
    #         if cur_gripper_pos==0: #change me
    #             print("Done opening, now dwelling.")
    #             opening = False
    #             dwelling = True

    #     elif dwelling:
    #         dwell_time_count += 1
    #         if dwell_time_count >= dwell_time_limit:
    #             print("Done dwelling, now pulling away.")
    #             steps_to_move = conversions.mm_to_steps(move_distance) #DIS -7000, MI
    #             move.move_gauge_backward_dist(stepper,steps_to_move)
    #             dwelling = False

    #     elif abs(cur_reading) < noforce_buffer:
    #         noforce_time_count += 1
    #         if noforce_time_count >= noforce_time_limit:
    #             print("Done test, now wrapping up.")
    #             move.stop_motor(stepper) # slow stop = de-accelerate first TODO
    #             test_done = True

    # # when done test, resize output array and print results for maximum adhesion force
    # force_readings = force_readings[0:reading_count,:]
    # print("Maximum adhesive force in %d readings: %f N." % (reading_count,max(abs(force_readings[:,0]))))
    # return force_readings, "shear_grip"