''' SYNTHESIS v0.0 - Katie Allison
Functions to synthesize data from multiple tests or to synthesize different types of data from the same test.
Created: 2024-05-21
Updated: 2024-05-21
'''
import numpy as np
import pandas as pd

from force_tester import plot
from force_tester import record
from force_tester import analysis

#from force_tester.helpers import crop
from force_tester.helpers import stats
from force_tester.helpers import conversions
from force_tester.helpers import files

from force_tester.helpers.constants import TIME_TYPE,FORCE_TYPE,POSITION_TYPE,PRESSURE_TYPE

# temp to deal with commas in logs
from csv import reader

PLOT_DESC = analysis.ANALYSIS_DESCRIPTORS[analysis.PLOT]
STAT_DESC = analysis.ANALYSIS_DESCRIPTORS[analysis.STATS]

def parse_date_range_inputs(start,end):
    if start is None:
        start = 0
    else:
        start = int(start.replace("-",""))
    if end is None: 
        end = 22222222
    else:
        end = int(end.replace("-",""))
    return start,end

def parse_file_timestamp(filename,time_only=False):
    filename_parts = filename.split("_")
    date = str(filename_parts[1])
    time = str(filename_parts[2])
    if time_only:
        return int(time)
    else:
        return int(date + time)

def assemble_synthesis_title(desc_str,start_str=None,end_str=None):
    if start_str is None and end_str is None:
        filename = "{0}_all"
    else:
        if start_str is None: 
            start_str = "first"
        elif end_str is None: 
            end_str = "last"
        filename = "{0}_{1}_to_{2}".format(desc_str,start_str,end_str)
    return filename

def list_files_in_date_range(start_date,end_date,full_file_list):
    files_in_date_range = []
    for file in full_file_list:
        file_date = int(file.split("_")[1])
        if (file_date >= start_date and file_date <= end_date):
            files_in_date_range.append(file)
    return files_in_date_range

def export_synthesis_data(data_to_export,column_name_list,export_name):
    dataframe = pd.DataFrame(data_to_export)
    dataframe.columns = column_name_list
    filepath = analysis.get_analysis_path(export_name,analysis_desc=STAT_DESC)
    dataframe.to_csv(filepath)

def multifile_plot(scale=True,convert=True,repeats=True,change_limits=True):
    done_plotting = False
    num_plots = 0
    while not done_plotting:
        done_adding_series = False
        num_series = 0
        start_new_plot = input("Hit ENTER to start selecting data series for plot {0}, or enter any key to finish.\n".format(num_plots+1))
        if (start_new_plot != "") or (not repeats):
            done_plotting = True
        else:
            data_series = []
            while not done_adding_series:
                file1 = input("Now adding data series {0} to plot {1}. Enter first filename to add to data series file pair or press ENTER to finish and proceed to plotting.\n".format(num_series+1,num_plots+1))
                if (file1 == ""):
                    done_adding_series = True
                else:
                    # import first set of data
                    data1,type1 = analysis.import_data(file1)

                    # get second set of data if applicable (if not vs. time graph)
                    file2 = input("Enter second filename to add to data series file pair or press ENTER to use only file 1. ")
                    if file2 != "":
                        data2,type2 = analysis.import_data(file2)
                    else:
                        data2,type2 = analysis.import_data(file1)
                        data1[:,2] = data1[:,1]
                        type1 = TIME_TYPE
                        datafile = file1
                        file1 = files.get_base_filename_from_path(file1,remove_ext=True)
                        file1 = file1 + "_{0}{1}".format(files.DATA_DESCRIPTORS[type1],files.FILE_EXT)
                        file2 = datafile

                    # scale data to standard units
                    if scale:
                        scaled_data,scale_factor = analysis.scale_data(data1[:,2],type1)
                        data1 = np.reshape(scaled_data,(-1,1))
                        scaled_data,scale_factor = analysis.scale_data(data2[:,2],type2)
                        data2 = np.reshape(scaled_data,(-1,1))
                    else:
                        data1 = np.reshape(data1[:,2],(-1,1))
                        data2 = np.reshape(data2[:,2],(-1,1))
                    
                    # reshape array and convert data if needed
                    # (e.g., converting motor position along leadscrew into displacement from test start)
                    if np.shape(data1)!=np.shape(data2):
                        min_len = min(np.shape(data1)[0],np.shape(data2)[0])
                        print("Data series 1 (length {0}) and 2 (length {1}) will be resized to have length {2}.".format(np.shape(data1)[0],np.shape(data2)[0],min_len))
                        data1 = data1[:min_len,:]
                        data2 = data2[:min_len,:]
                    if convert:
                        if type1 == POSITION_TYPE:
                            converted_data = analysis.convert_data(data1,type1,-1,data1[0][0])
                            data1 = np.reshape(converted_data,(-1,1))
                        if type2 == POSITION_TYPE:
                            converted_data = analysis.convert_data(data2,type2,-1,data2[0][0])
                            data2 = np.reshape(converted_data,(-1,1))
                    combined_data = np.concatenate((data1,data2),axis=1)
                    # export_analysis_data(next_file,next_data,data_type,SCALE)

                    if change_limits:
                        limit_left = input("Enter a start index for plotting this dataseries. ")
                        limit_right = input("Enter an end index for plotting this dataseries. ")
                        if limit_left == "":
                            limit_left = 0
                        else:
                            limit_left == int(limit_left)
                        if limit_right == "":
                            limit_right = -1
                        else:
                            limit_right = int(limit_right)
                        #combined_data = set_test_start(combined_data,54,325)
                        combined_data = analysis.set_test_start(combined_data,limit_left,limit_right)
                    
                    legend_text = input("Enter a legend entry for this dataseries. ")
                    data_series.append((file1,file2,combined_data,legend_text))
                    num_series += 1

            # plot graph of data (vs time only, not other data arrays)
            plot_title = input("Enter the plot title. ")
            if plot_title != "":
                try:
                    default_name = files.get_base_filename_from_path(data_series[-1][0])
                    save_name = input("Enter a filename base string for the plot image or press ENTER to use the default ({0}).\n".format(default_name))
                    breakpoint()
                    plot.make_multiseries_graph_x_vs_y(plot_title,data_series,PLOT_DESC,plot_size=(7,5),x_col=1,y_col=2,fit_line=True,filename_replacement=save_name)
                except:
                    print("Plotting not successful")
        num_plots += 1
    return num_plots

def multifile_multitest_plot(scale=True,convert=True,repeats=True,end_limit=None,base_plot_title=""):
    done_plotting = False
    num_plots = 0
    while not done_plotting:
        done_adding_series = False
        num_series = 0
        start_new_plot = input("Hit ENTER to start selecting data series for plot {0}, or enter any key to finish.\n".format(num_plots+1))
        if (start_new_plot != "") or (not repeats):
            done_plotting = True
        else:
            data_series = []
            while not done_adding_series:
                file1 = input("Now adding data series {0} to plot {1}. Enter first filename to add to data series file pair or press ENTER to finish and proceed to plotting.\n".format(num_series+1,num_plots+1))
                if (file1 == ""):
                    done_adding_series = True
                else:
                    # import first set of data
                    data1,type1 = analysis.import_data(file1)

                    # get second set of data if applicable (if not vs. time graph)
                    file2 = input("Enter second filename to add to data series file pair, press ENTER to use only file 1, or press F to use corresponding force data for file 1. ")
                    if file2 == "F":
                        file2 = files.crop_data_type_from_filename(file1)
                        file2 = file2 + "_{0}{1}".format(files.DATA_DESCRIPTORS[files.FORCE_TYPE],files.FILE_EXT)
                        data2,type2 = analysis.import_data(file2)
                    elif file2 == "":
                        data2,type2 = analysis.import_data(file2)
                    else:
                        data2,type2 = analysis.import_data(file1)
                        data1[:,2] = data1[:,1]
                        type1 = TIME_TYPE
                        datafile = file1
                        file1 = files.get_base_filename_from_path(file1,remove_ext=True)
                        file1 = file1 + "_{0}{1}".format(files.DATA_DESCRIPTORS[type1],files.FILE_EXT)
                        file2 = datafile

                    # scale data to standard units
                    if scale:
                        scaled_data,scale_factor = analysis.scale_data(data1[:,2],type1)
                        data1 = np.reshape(scaled_data,(-1,1))
                        scaled_data,scale_factor = analysis.scale_data(data2[:,2],type2)
                        data2 = np.reshape(scaled_data,(-1,1))
                    else:
                        data1 = np.reshape(data1[:,2],(-1,1))
                        data2 = np.reshape(data2[:,2],(-1,1))
                    
                    # reshape array and convert data if needed
                    # (e.g., converting motor position along leadscrew into displacement from test start)
                    if np.shape(data1)!=np.shape(data2):
                        min_len = min(np.shape(data1)[0],np.shape(data2)[0])
                        print("Data series 1 (length {0}) and 2 (length {1}) will be resized to have length {2}.".format(np.shape(data1)[0],np.shape(data2)[0],min_len))
                        data1 = data1[:min_len,:]
                        data2 = data2[:min_len,:]
                    if convert:
                        if type1 == POSITION_TYPE:
                            converted_data = analysis.convert_data(data1,type1,-1,data1[0][0])
                            data1 = np.reshape(converted_data,(-1,1))
                        if type2 == POSITION_TYPE:
                            converted_data = analysis.convert_data(data2,type2,-1,data2[0][0])
                            data2 = np.reshape(converted_data,(-1,1))
                    combined_data = np.concatenate((data1,data2),axis=1)

                    if not(end_limit is None):
                        limit_left = 0
                        limit_right = int(end_limit)
                        combined_data = analysis.set_test_start(combined_data,limit_left,limit_right)
                    
                    # get test number and timestamp
                    base_filename = files.crop_data_type_from_filename(file1)
                    test_time = str(parse_file_timestamp(base_filename,time_only=True))
                    log_filename = base_filename + '_' + record.LOG_TYPE_NAME + files.FILE_EXT
                    test_num = analysis.import_log_data(log_filename,"test number relative to last calibration")
                    if num_series == 0:
                        first_test_num = test_num

                    legend_text = "test {0} ({1}:{2})".format(test_num,test_time[0:2],test_time[2:])
                    print("Legend will be automatically set to {0}".format(legend_text))
                    data_series.append((file1,file2,combined_data,legend_text))
                    num_series += 1

            # plot graph of data (vs time only, not other data arrays)
            if base_plot_title == "":
                plot_title = input("Enter the plot title. ")
            else:
                plot_title = base_plot_title + " (tests {0} to {1})".format(first_test_num,test_num)

            default_name = files.get_base_filename_from_path(data_series[-1][0])
            save_name = input("Enter a filename base string for the plot image or press ENTER to use the default ({0}).\n".format(default_name))
            try:
                plot.make_multiseries_graph_x_vs_y(plot_title,data_series,PLOT_DESC,plot_size=(7,5),x_col=1,y_col=2,fit_line=True,filename_replacement=save_name)
            except:
                print("Plotting not successful")
        num_plots += 1
    return num_plots

def multifile_basic_stats_summary(start_date=None,end_date=None):
    # parse input dates and get filename
    filename = assemble_synthesis_title("statssummary",start_date,end_date)
    start_date_int,end_date_int = parse_date_range_inputs(start_date,end_date)
    
    # get basic stats from files in range
    force_data_files = files.get_file_list_from_path(files.DATA_DESCRIPTORS[FORCE_TYPE])
    files_in_range = list_files_in_date_range(start_date_int,end_date_int,force_data_files)
    num_files = len(files_in_range)

    # get stats for each file
    file_stat_data = np.empty((num_files,5),dtype=object)
    file_stat_data[:,0] = np.array(files_in_range,dtype=object).reshape((num_files,))
    for curr_file_ind in range(0,num_files):
        # get stats from file
        curr_data,curr_type = analysis.import_data(files_in_range[curr_file_ind])
        mean,median,min,max = stats.get_basic_stats(curr_data=curr_data)

        # store stats in array
        file_stat_data[curr_file_ind][1] = str(mean)
        file_stat_data[curr_file_ind][2] = str(median)
        file_stat_data[curr_file_ind][3] = str(min)
        file_stat_data[curr_file_ind][4] = str(max)

    export_synthesis_data(file_stat_data,["filename","mean","median","min","max"],filename)

def multifile_CoF_estimate_summary(start_date=None,end_date=None):
    # parse input dates and get filename
    filename = assemble_synthesis_title("CoFestimatevals",start_date,end_date)
    start_date_int,end_date_int = parse_date_range_inputs(start_date,end_date)
    
    # get basic stats from files in range
    force_data_files = files.get_file_list_from_path(files.DATA_DESCRIPTORS[FORCE_TYPE])
    files_in_range = list_files_in_date_range(start_date_int,end_date_int,force_data_files)
    num_files = len(files_in_range)

    # get stats for each file
    file_stat_data = np.empty((num_files,6),dtype=object)
    file_stat_data[:,0] = np.array(files_in_range,dtype=object).reshape((num_files,))
    for curr_file_ind in range(0,num_files):
        # get stats data from force file
        curr_data,curr_type = analysis.import_data(files_in_range[curr_file_ind])
        mean,median,min,max = stats.get_basic_stats(curr_data=curr_data)
        file_stat_data[curr_file_ind][1] = str(mean)
        file_stat_data[curr_file_ind][2] = str(median)
        file_stat_data[curr_file_ind][3] = str(min)
        file_stat_data[curr_file_ind][4] = str(max)

        # get mass data from log file
        log_filename = files.crop_data_type_from_filename(files_in_range[curr_file_ind])
        log_filename = log_filename + '_' + record.LOG_TYPE_NAME + files.FILE_EXT
        mass = analysis.import_log_data(log_filename,"sled mass [g]")
        file_stat_data[curr_file_ind][5] = str(mass)

    export_synthesis_data(file_stat_data,["filename","mean","median","min","max","mass"],filename)

def multifile_velocity_check(start_date=None,end_date=None):
    def compute_velocity(time_range,pos_range):
        t1,t2 = time_range
        x1,x2 = pos_range
        dt = (t2-t1)*conversions.UNIT_SCALES[TIME_TYPE]
        dx = (x2-x1)*conversions.UNIT_SCALES[POSITION_TYPE]
        if dt <=0: print("Time difference is negative in velocity computation!")
        if dx <=0: print("Position difference is negative in velocity computation!")
        return dx/dt
    def debug_velocity(pos_time_data):
        dxdt = pos_time_data[1:,:] - pos_time_data[:-1,:]
        print(dxdt)
        print(np.std(pos_time_data,0))
        return
    
    # parse input dates and get filename
    filename = assemble_synthesis_title("velocity_check",start_date,end_date)
    start_date_int,end_date_int = parse_date_range_inputs(start_date,end_date)
    
    # get basic stats from files in range
    pos_data_files = files.get_file_list_from_path(files.DATA_DESCRIPTORS[POSITION_TYPE])
    files_in_range = list_files_in_date_range(start_date_int,end_date_int,pos_data_files)
    num_files = len(files_in_range)

    # get stats for each file
    file_stat_data = np.empty((num_files,7),dtype=object)
    file_stat_data[:,0] = np.array(files_in_range,dtype=object).reshape((num_files,))
    print(file_stat_data)
    for curr_file_ind in range(0,num_files):
        # import position data and crop first line, plus separate into time and position data
        print(files_in_range[curr_file_ind])
        curr_data,curr_type = analysis.import_data(files_in_range[curr_file_ind])
        curr_data = curr_data[1:,1:]
        debug_velocity(curr_data)
        time_data = curr_data[:,0]
        posn_data = curr_data[:,1]

        # remove invalid data and get minimum and maximum values
        if len(time_data[time_data < 1]) > 0:
            breakpoint()
        if len(time_data[posn_data < 1]) > 0:
            breakpoint()
        time_data[time_data < 1] = np.nan
        posn_data[posn_data == -99 ] = np.nan
        times = (np.nanmin(time_data),np.nanmax(time_data))
        positions = (np.nanmin(posn_data),np.nanmax(posn_data))

        # store minimum and maximum values and compute overall velocity
        file_stat_data[curr_file_ind][1] = str(times[0])
        file_stat_data[curr_file_ind][2] = str(times[1])
        file_stat_data[curr_file_ind][3] = str(positions[0])
        file_stat_data[curr_file_ind][4] = str(positions[1])
        file_stat_data[curr_file_ind][5] = str(compute_velocity(times,positions))

        # compute local velocity (between points a small number of rows apart)
        times = (time_data[10],time_data[20])
        positions = (posn_data[20],posn_data[10])
        file_stat_data[curr_file_ind][6] = str(compute_velocity(times,positions))

    export_synthesis_data(file_stat_data,["filename","Tmin","Tmax","Xmin","Xmax","overall velocity","local velocity"],filename)

def multifile_timestep_check(start_date=None,end_date=None):
    def compute_step_data(pos_time_data):
        dxdt = pos_time_data[1:,:] - pos_time_data[:-1,:]
        if (dxdt[0,1] != -4 and np.std(dxdt[:,1]) != 0):
            print("First line is: ")
            print(pos_time_data[0,:])
            print(dxdt[0,:])
            dxdt = dxdt[1:,:]
            print("New first line is: ")
            print(pos_time_data[1,:])
            print(dxdt[0,:])
        return dxdt
    def make_timestep_array(step_data):
        dt = step_data[:,0]
        num_steps = np.shape(dt)[0]
        return np.array(dt).reshape((num_steps,))
    
    # parse input dates and get filename
    filename = assemble_synthesis_title("timesteps",start_date,end_date)
    start_date_int,end_date_int = parse_date_range_inputs(start_date,end_date)
    
    # get basic stats from files in range
    pos_data_files = files.get_file_list_from_path(files.DATA_DESCRIPTORS[POSITION_TYPE])
    files_in_range = list_files_in_date_range(start_date_int,end_date_int,pos_data_files)
    num_files = len(files_in_range)

    # get stats for each file
    file_time_data = {}
    for curr_file_ind in range(0,num_files):
        # import data from current file and get timestep data
        curr_data,curr_type = analysis.import_data(files_in_range[curr_file_ind])
        pos_time_steps = compute_step_data(curr_data[:,1:])
        time_steps = make_timestep_array(pos_time_steps)

        # store filename and timestep data in dictionary
        file_time_data[files_in_range[curr_file_ind]] = time_steps
    data_df = pd.DataFrame({k:pd.Series(v) for k,v in file_time_data.items()})
    filepath = analysis.get_analysis_path(filename,analysis_desc=STAT_DESC)
    data_df.to_csv(filepath)

def multifile_force_export(start_date=None,end_date=None):
    def make_force_pt_array(force_data):
        num_pts = np.shape(force_data)[0]
        return np.array(force_data).reshape((num_pts,))
    
    # parse input dates and get filename
    filename = assemble_synthesis_title("force_data",start_date,end_date)
    start_date_int,end_date_int = parse_date_range_inputs(start_date,end_date)
    
    # get basic stats from files in range
    force_data_files = files.get_file_list_from_path(files.DATA_DESCRIPTORS[FORCE_TYPE])
    files_in_range = list_files_in_date_range(start_date_int,end_date_int,force_data_files)
    num_files = len(files_in_range)

    # get stats for each file
    file_force_data = {}
    for curr_file_ind in range(0,num_files):
        # import data from current file and store force data in dictionary
        curr_data,curr_type = analysis.import_data(files_in_range[curr_file_ind])
        force_pts = make_force_pt_array(curr_data[:,2])
        file_force_data[files_in_range[curr_file_ind]] = force_pts
    data_df = pd.DataFrame({k:pd.Series(v) for k,v in file_force_data.items()})
    filepath = analysis.get_analysis_path(filename,analysis_desc=STAT_DESC)
    data_df.to_csv(filepath)

def multifile_tests_since_power_cycle_summary(start_date=None,end_date=None):
    # parse input dates and get filename
    filename = assemble_synthesis_title("TestsSincePowerCycle",start_date,end_date)
    start_date_int,end_date_int = parse_date_range_inputs(start_date,end_date)
    
    # get basic stats from files in range
    force_data_files = files.get_file_list_from_path(files.DATA_DESCRIPTORS[FORCE_TYPE])
    files_in_range = list_files_in_date_range(start_date_int,end_date_int,force_data_files)
    num_files = len(files_in_range)

    # get stats for each file
    file_stat_data = np.empty((num_files,3),dtype=object)
    file_stat_data[:,0] = np.array(files_in_range,dtype=object).reshape((num_files,))
    
    for curr_file_ind in range(0,num_files):
        # get stats data from force file
        base_filename = files.crop_data_type_from_filename(files_in_range[curr_file_ind])
        file_stat_data[curr_file_ind][1] = parse_file_timestamp(base_filename)
        log_filename = base_filename + '_' + record.LOG_TYPE_NAME + files.FILE_EXT
        test_num = analysis.import_log_data(log_filename,"test number relative to last calibration")
        if test_num is not None:
            file_stat_data[curr_file_ind][2] = str(test_num)

    export_synthesis_data(file_stat_data,["filename","time","number"],filename)

if __name__ == "__main__":
    #multifile_force_export(start_date="20240507",end_date="20240516")
    #multifile_tests_since_power_cycle_summary(start_date="20240506",end_date="20240516")
    multifile_multitest_plot(base_plot_title="Long test sequence with no load and full steps")
