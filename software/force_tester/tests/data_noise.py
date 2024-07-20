'''
Script to test correlation between various parameters and noise in data.
'''
import sys
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import gc

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from helpers import files
from helpers import conversions
from main import startup,run_calibration,fill_parameter_dict,plot_curr_data,stop_connections,prompt_move_stage,prompt_stop_testing
import record
import move

NOISY_DATA_FOLDER = "Noise"
NOISY_DATA_PATH = os.path.join(files.get_path(include_analysis_folder=True),NOISY_DATA_FOLDER)

DEBUG_TEST_NAME = "DEBUG"
    
def load_from_file(filename,num_skipped_rows=1):
    filepath = files.assemble_path(filename)
    data_arr = np.loadtxt(filepath,delimiter=files.FILE_DELIM,skiprows=num_skipped_rows)
    return data_arr

def file_in_noisy_list(filename,noisy_file_list):
    is_noisy = False
    for noisy_name in noisy_file_list:
        if noisy_name in filename:
            is_noisy = True
            break
    return is_noisy

def coefficient_of_variation(data_array,data_col=2):
    data_to_analyze = data_array[:,data_col]
    coeff = np.std(data_to_analyze)/np.mean(data_to_analyze)
    return coeff

def quartile_coefficient_of_dispersion(data_array,data_col=2):
    data_to_analyze = data_array[:,data_col]
    q1 = np.percentile(data_to_analyze, 25)
    q3 = np.percentile(data_to_analyze, 75)
    iqr = q3 - q1
    qav = q1 + q3
    coeff = iqr/qav
    return coeff

def edge_coefficient_of_dispersion(data_array,data_col=2):
    data_to_analyze = data_array[:,data_col]
    qL = np.percentile(data_to_analyze, 5)
    qR = np.percentile(data_to_analyze, 95)
    rng = qR - qL
    avg = qL + qR
    coeff = rng/avg
    return coeff

def plot_coeff_histogram(noisy_coeffs,non_noisy_coeffs,metric_string,extrema,num_bins=24):
    plt.hist([non_noisy_coeffs,noisy_coeffs],bins=num_bins,density=True,range=extrema,label=["non-noisy","noisy"])
    plt.title(metric_string)
    plt.legend()
    plt.show()

def quantify_noise(files_to_test=None):
# analyze noisy data files and attempt to quantify noise in data with various metrics

    # initialize metric arrays
    noisy = {"coefficient_of_variation":[],"quartile_coefficient_of_dispersion":[],"edge_coefficient_of_dispersion":[]}
    non_noisy = {"coefficient_of_variation":[],"quartile_coefficient_of_dispersion":[],"edge_coefficient_of_dispersion":[]}

    # get list of files to test
    if files_to_test is None:
        test_file_list = files.get_file_list_from_path("force")
    else:
        test_file_list = files_to_test
        
    # get list of noisy and excluded files
    noisy_list = np.loadtxt(os.path.join(NOISY_DATA_PATH,"noisy_test_prefixes.txt"),dtype='str')
    ignore_list = ['shearFAILED_20240301_1606_force.csv','shearNOloadNOpower_20240305_1924_force.csv','shearNOLoad_20240207_1253_force.csv','shearNOload_20240302_1745_force.csv','shearNOLoad_20240414_1641_force.csv']

    # iterate through files computing noise metrics
    num_files_to_try = len(test_file_list)
    for test_file_ind in range(0, num_files_to_try):
        # get next file and check if noisy
        curr_file = test_file_list[test_file_ind]
        if curr_file not in ignore_list:
            file_is_noisy = file_in_noisy_list(curr_file,noisy_list)

            # compute metrics for data from file   
            curr_data = load_from_file(curr_file)
            CoV = coefficient_of_variation(curr_data)
            QCoD = quartile_coefficient_of_dispersion(curr_data)
            ECoD = edge_coefficient_of_dispersion(curr_data)

            # add metrics to dictionary for current file type
            if file_is_noisy:
                noisy["coefficient_of_variation"].append(CoV)
                noisy["quartile_coefficient_of_dispersion"].append(QCoD)
                noisy["edge_coefficient_of_dispersion"].append(ECoD)
                print("CoV is {1}, QCoD is {2}, and ECoD is {3} for NOISY file {0}.".format(curr_file,CoV,QCoD,ECoD))
            else:
                non_noisy["coefficient_of_variation"].append(CoV)
                non_noisy["quartile_coefficient_of_dispersion"].append(QCoD)
                non_noisy["edge_coefficient_of_dispersion"].append(ECoD)
                print("CoV is {1}, QCoD is {2}, and ECoD is {3} for CLEAN file {0}.".format(curr_file,CoV,QCoD,ECoD))
    
    # get sorted results
    noisy_CoV,non_noisy_CoV = np.sort(noisy["coefficient_of_variation"]),np.sort(non_noisy["coefficient_of_variation"])
    noisy_QCoD,non_noisy_QCoD = np.sort(noisy["quartile_coefficient_of_dispersion"]),np.sort(non_noisy["quartile_coefficient_of_dispersion"])
    noisy_ECoD,non_noisy_ECoD = np.sort(noisy["edge_coefficient_of_dispersion"]),np.sort(non_noisy["edge_coefficient_of_dispersion"])

    # print summary of results
    print("Coefficients of variation for noisy data are {0} (avg:{2})\nCoefficients of variation for non-noisy data are {1} (avg: {3})".format(noisy_CoV,non_noisy_CoV,np.mean(noisy_CoV),np.mean(non_noisy_CoV)))
    print("Coefficients of dispersion for noisy data are {0} (avg:{2})\nCoefficients of dispersion for non-noisy data are {1} (avg: {3})".format(noisy_QCoD,non_noisy_QCoD,np.mean(noisy_QCoD),np.mean(non_noisy_QCoD)))
    print("Edge coefficients of dispersion for noisy data are {0} (avg:{2})\nEdge coefficients of dispersion for non-noisy data are {1} (avg: {3})".format(noisy_ECoD,non_noisy_ECoD,np.mean(noisy_ECoD),np.mean(non_noisy_ECoD)))
    
    # put results in histogram
    plot_coeff_histogram(noisy_CoV,non_noisy_CoV,"coefficient of variation",(min(np.min(noisy_CoV),np.mean(non_noisy_CoV)),max(np.max(noisy_CoV),np.max(non_noisy_CoV))))
    plot_coeff_histogram(noisy_QCoD,non_noisy_QCoD,"quartile coefficient of dispersion",(min(np.min(noisy_QCoD),np.mean(non_noisy_QCoD)),max(np.max(noisy_QCoD),np.max(non_noisy_QCoD))))
    plot_coeff_histogram(noisy_ECoD,non_noisy_ECoD,"edge coefficient of dispersion",(min(np.min(noisy_ECoD),np.mean(non_noisy_ECoD)),max(np.max(noisy_ECoD),np.max(non_noisy_ECoD))))

def plot_effect_power_cycle(filename=None,use_number_tests=True):
    file_data = np.loadtxt(files.assemble_path(filename,is_analysis=True),delimiter=files.FILE_DELIM,dtype='str',skiprows=1)
    plot_data = np.zeros((len(file_data),2))
    for i in range(0,len(file_data)):
        force_data = load_from_file(file_data[i,1])
        ECoD = edge_coefficient_of_dispersion(force_data)
        plot_data[i,0] = int(file_data[i,2])
        plot_data[i,1] = ECoD

    # scatter plot of ECoD vs timestamp
    plt.scatter(plot_data[:,0],plot_data[:,1])
    plt.title("Edge coefficient of dispersion vs timestamp")
    plt.xlabel("Timestamp")
    plt.ylabel("ECoD")
    plt.show()

    # scatter plot of ECoD vs test run
    if use_number_tests:
        test_num = []
        ECoD_vals = []
        for i in range(0,len(file_data)):
            if file_data[i,3] != '':
                test_num.append(int(file_data[i,3]))
                force_data = load_from_file(file_data[i,1])
                ECoD = edge_coefficient_of_dispersion(force_data)
                ECoD_vals.append(ECoD)
        plt.scatter(test_num,ECoD_vals)
        plt.title("Edge coefficient of dispersion vs number of tests since calibration")
        plt.xlabel("Number of tests since calibration")
        plt.ylabel("ECoD")
        plt.show()

def query_memory(stepper_link):
    # stepper_link.send("print(df())")
    # cur_df = stepper_link.receive()
    # if cur_df[1] != "B":
    #     print(cur_df)
    #     cur_df = stepper_link.receive()

    stepper_link.send("print(free())")
    cur_free = stepper_link.receive()
    if cur_free[1] != "P":
        print(cur_free)
        cur_free = stepper_link.receive()

    return cur_free
    
def query_velocity(stepper_link):
    stepper_link.receive()
    stepper_link.send("stepper_motor.pulse_time")
    pt = stepper_link.receive()
    stepper_link.send("stepper_motor.delay_time")
    dt = stepper_link.receive()
    print("Pulse/delay: {0}/{1}".format(pt,dt))

def long_shear_test(force_gauge,stepper,max_time=5,max_pos=500,get_memory=True,get_velocity=True):

    # set limits and buffers
    time_limits = {"serial":conversions.sec_to_ns(0.1), "no force":conversions.sec_to_ns(max_time),"total":conversions.sec_to_ns(10)}
    pos_limit = max_pos
    force_limit = 20 # in N - gauge capacity 25 N
    force_buffer = 0.02 # in N, decreased from 0.05 due to low sled mass
    force_targets = []

    # initalize variables and arrays
    reading_count = -1
    noforce_timer = 0
    array_rows = 50000
    force_readings = np.empty((array_rows,2))
    position_reports = np.empty((array_rows,2))
    
    start_test = input("Press ENTER to start test, or press any key to cancel. ")
    if start_test != "":
        move.stop_motor(stepper)
        return False, None, None, None
    start_time = time.time_ns()
    serial_timeout = conversions.ns_to_sec(time_limits["serial"])

    # take test force reading
    cur_reading = force_gauge.get_force_measurement(timeout=serial_timeout)
    print("Test force reading is %f"%(cur_reading,))

    # collect garbage then disable GC
    if get_velocity: query_velocity(stepper)
    if get_memory:
        stepper.send("gc.collect()")
        stepper.send("gc.disable()")
        response = stepper.receive()
        if len(response)>3: print(response)
        stepper.receive()

    # start test, moving steadily backward until force threshold reached
    pre_test = query_memory(stepper)
    print(pre_test)
    print("Starting test. Now retreating to maximum %f mm travel distance."%pos_limit)
    microsteps_to_move = conversions.mm_to_pulses(pos_limit)
    move.quick_backward_dist(stepper,microsteps_to_move)
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

        if abs(cur_reading) > force_limit:
            print("Force limit exceeded, stopping test.")
            move.stop_motor(stepper) # slow stop = de-accelerate first TODO
            test_done = True
            break
        if time.time_ns() - start_time > time_limits["total"]:
            print("Test past total time limit")
            move.stop_motor(stepper) # slow stop = de-accelerate first TODO
            test_done = True
            break

        # depending on current stage of script, take motor actions in response to data
        if not pulling:
            if abs(cur_reading) > force_buffer:
                print("Nonzero force reading of %f at position %d."%(cur_reading,cur_position))
                pulling = True
        else:
            if abs(cur_reading) < force_buffer:
                if not zero_force:
                    zero_force = True
                    noforce_start = time.time_ns()
                    print("Zero force reading at position %d"%cur_position)
                else:
                    noforce_timer = time.time_ns() - noforce_start
                    if noforce_timer >= time_limits["no force"]:
                        print("Done test, now wrapping up.")
                        move.stop_motor(stepper) # slow stop = de-accelerate first TODO
                        test_done = True

    #re-enable GC
    print(stepper.receive())
    print(stepper.receive())
    if get_memory:
        post_test = query_memory(stepper)
        print(post_test)
        stepper.send("gc.collect()")
        stepper.send("gc.enable()")
        response = stepper.receive()
        if len(response)>3: print(response)
    else:
        pre_test,post_test = None,None
    if get_velocity: query_velocity(stepper)

    force_readings = force_readings[0:reading_count,:]
    position_reports = position_reports[0:reading_count,:]
    test_duration = conversions.ns_to_sec(int(time.time_ns()-start_time))
    print("Maximum frictional force in %d readings over %f seconds: %f N." % (reading_count,test_duration,min(force_readings[:,1])))
    print("Total travel distance: %f mm." % conversions.pulses_to_mm(max(position_reports[:,1])-min(position_reports[:,1])))

    # organize parameter data
    limits = (time_limits,pos_limit,force_limit)
    targets = (force_targets,[])
    output_data = {files.FORCE_TYPE:force_readings,files.POSITION_TYPE:position_reports,}
    parameter_data = {"test type":DEBUG_TEST_NAME,"test succeeded":test_done,"test duration [seconds]":test_duration,
        "time limits [nanoseconds]":limits[0],"position limits [mm]":limits[1],"force limits [N]":limits[2],
        "force targets [N]":targets[0],"pressure targets [kPa]":targets[1]}
    return test_done,DEBUG_TEST_NAME,output_data,parameter_data,(pre_test,post_test)

def run_long_test(test_memory=True,test_velocity=True,test_microsteps=False):
    num_tests = 0
    test_param_values = None
    actuator,sensor,device = startup(use_pneumatics=False)
    if test_memory: print(query_memory(actuator))

    run_calibration(actuator) # current: slow 8, fast 12. Former: slow 8, fast 10
    if test_memory: print(query_memory(actuator))
    if test_velocity: query_velocity(actuator)

    try:
        all_tests_done = False
        while not all_tests_done:
            if test_memory: print(query_memory(actuator))
            prompt_move_stage(actuator)
            if test_memory: print(query_memory(actuator))

            test_success,test_type,test_data,test_params,RAM_change = long_shear_test(sensor, actuator,get_memory=test_memory,get_velocity=test_velocity)
            if test_success == False:
                print("This test failed!")
                break
            else:
                num_tests += 1
            
            # record test parameters
            test_desc = "halfsteps"
            test_param_values = (test_desc,0,0,0,num_tests)
            test_params = fill_parameter_dict(test_params,*test_param_values)
            test_file = record.record_all_test_data(test_type + test_desc,test_data,test_params)

            # try to plot data, then check whether to keep testing
            if test_memory:
                titlestr = "memory test [{3}] {0}: {1} -> {2}".format(num_tests,RAM_change[0],RAM_change[1],test_desc)
            else:
                titlestr = "noise test [{0}] {1}".format(test_desc,num_tests)
            test_file = plot_curr_data(test_file,auto_on=True,auto_title=titlestr)
            all_tests_done = prompt_stop_testing()
    finally:
        query_velocity(actuator)
        stop_connections(actuator,sensor)

if __name__ == "__main__":
    #quantify_noise()
    # check_effect_power_cycle('TestsSincePowerCycle_all_stats.csv')
    # plot_effect_power_cycle('TestsSincePowerCycle_2024-02-29_to_2024-03-02_stats.csv',use_number_tests=False)
    run_long_test(test_memory=False,test_velocity=False,test_microsteps=True)