''' ANALYSIS v0.0 - Katie Allison
Hatton Lab force testing platform data computational postprocessing and graphing code
Some of this code based on SparkFun tutorial for tkinter GUIs for hardware: 
https://learn.sparkfun.com/tutorials/python-gui-guide-introduction-to-tkinter/all

Created: 2023-12-11
Updated: 2023-12-11

This code imports raw data from saved data files and turns it into (various types of) usable graphs. Also used by GUI to display analysis information.

Data inputs:
- 
Notes:
- 
'''
import numpy as np
import pandas as pd

from force_tester import plot
from force_tester import record

#from force_tester.helpers import crop
from force_tester.helpers import stats
from force_tester.helpers import conversions
from force_tester.helpers import files

from force_tester.helpers.constants import TIME_TYPE,FORCE_TYPE,POSITION_TYPE,PRESSURE_TYPE

# temp to deal with commas in logs
from csv import reader

CROP = 0
CLEAN = 1
STATS = 2
SCALE = 3
CONVERT = 4
PLOT = 9

ANALYSIS_DESCRIPTORS = {
    CROP: 'cropped',
    CLEAN: 'cleaned',
    STATS: 'stats',
    SCALE: 'scaled',
    CONVERT: 'converted',
    PLOT: 'plot'
    }

def display_paths():
    data_input = files.get_path(include_analysis_folder=False)
    path_info = "Input data is imported from {0} to analysis module.\n".format(data_input)

    analysis_output = files.get_path(include_analysis_folder=True)
    path_info += "Output data is exported to {0} from analysis module.".format(analysis_output)

    return path_info

def get_analysis_path(filepath,analysis_desc=""):
    analysis_filename = files.get_analysis_filename(filepath,analysis_desc)
    analysis_path = files.assemble_path(analysis_filename,is_analysis=True)
    return analysis_path

def import_data(filename):
    # pull data from file
    filepath = files.assemble_path(filename)
    data_arr = np.loadtxt(filepath,delimiter=files.FILE_DELIM,skiprows=1)
    # get data type from filename suffix
    data_type = files.get_data_type_from_path(filename)
    return data_arr,data_type

def import_log_data(filename,param_to_fetch,param_is_row_num=False):
    # pull data from file
    filepath = files.assemble_path(filename)
    data_val = None
    row_ct = 0
    with open(filepath) as f:
        for row in reader(f):
            if param_is_row_num and row_ct == param_to_fetch:
                data_val = row[1]
            else:
                if row[0] == param_to_fetch:
                    data_val = row[1]
            row_ct += 1
    return data_val

def export_stats_data(base_filename,stats_dict):
    stats_df = pd.DataFrame.from_dict(stats_dict,orient='index')
    stats_df.columns = ["statistical quantity value"]
    filepath = get_analysis_path(base_filename,analysis_desc=ANALYSIS_DESCRIPTORS[STATS])
    stats_df.to_csv(filepath)
    return filepath

def export_analysis_data(filename,analysis_data_arr,data_type_str,analysis_type):
    # get data type and format data
    if type(data_type_str) is str:
        data_type = files.DATA_DESCRIPTORS_INVERSE[data_type_str]
    else:
        data_type = data_type_str
    data_df = record.format_data(data_type,analysis_data_arr[:,1:])
    # get filepath and export
    filepath = get_analysis_path(filename,analysis_desc=ANALYSIS_DESCRIPTORS[analysis_type])
    data_df.to_csv(filepath)
    return filepath

def crop_data(data,time_col=1,data_col=2,crop_to_after_max=False):
    # crop any fake data (data where all columns, including time, are 0)
    near_zero_time_inds = np.asarray(abs(data[:,time_col])<=1e-9).nonzero()[0]
    if len(near_zero_time_inds) > 0:
        cropped_data = data[:near_zero_time_inds[0],:]
    else:
        cropped_data = data

    # (for removing force artifacts) crop beginning up to first 0 after max value
    if crop_to_after_max:
        max_ind = np.argmax(cropped_data[:,data_col])
        if cropped_data[max_ind][data_col]>0:
            low_inds = np.asarray(cropped_data[:,data_col]<=0).nonzero()
            low_inds = low_inds[0]
            crop_ind = np.asarray(low_inds>max_ind).nonzero()[0]
            if len(crop_ind) > 0:
                cropped_data = cropped_data[low_inds[crop_ind[0]]:,:]
    return cropped_data

def scale_data(curr_data,data_type=TIME_TYPE,use_type=True,factor=1):
    if use_type:
        return conversions.scale_data_by_type(curr_data,data_type)
    else:
        return curr_data*(1/factor),factor
    
def convert_data(curr_data,data_type,factor,shift,data_scaled=True):
    if not data_scaled:
        data_in_standard_units = conversions.scale_data_by_type(curr_data,data_type)
    else:
        data_in_standard_units = curr_data
    converted_data = factor*data_in_standard_units + shift
    return converted_data

def set_test_start(curr_data,start_ind,finish_ind):
    return curr_data[start_ind:finish_ind,:]

def locate_test_start(curr_data,threshold_val,threshold_rate):
    pass

def analysis_numerical(curr_data,col_to_analyze,print_out=False):
    # get shape information and basic stats info
    curr_shape = stats.get_shape(curr_data)
    curr_mean,curr_median,curr_min,curr_max = stats.get_basic_stats(curr_data,col_to_analyze)

    # return numerical analysis info in dictionary (and print if requested)
    stats_dict = {"shape":str(curr_shape),"mean":curr_mean,"median":curr_median,"minimum":curr_min,"maximum":curr_max}
    if print_out:
        print("{0} rows and {1} columns in file (including any index columns).".format(curr_shape[0],curr_shape[1]))
        print("Mean: {0}\nMedian: {1}\nMinimum: {2}\nMaximum: {3}".format(curr_mean,curr_median,curr_min,curr_max))
    return stats_dict

def auto_analysis_numerical(next_file,next_data,file_data_type,crop=True,scale=True):
    if crop:
        if file_data_type == FORCE_TYPE:
            next_data = crop_data(next_data,crop_to_after_max=True)
        else:
            next_data = crop_data(next_data)
        export_analysis_data(next_file,next_data,file_data_type,CROP)

    # scale data to standard units
    if scale:
        scaled_data = next_data
        scaled_data[:,1],scale_factor = scale_data(next_data[:,1],TIME_TYPE)
        scaled_data[:,2],scale_factor = scale_data(next_data[:,2],file_data_type)
        export_analysis_data(next_file,scaled_data,file_data_type,SCALE)

    # # compute and export basic stats
    shape_and_stats = analysis_numerical(scaled_data,2)
    export_stats_data(next_file,shape_and_stats)
    return shape_and_stats

def auto_analysis_graphical(next_file,next_data,file_data_type,plot_title):
    # scale data to standard units
    scaled_data = next_data
    scaled_data[:,1],scale_factor = scale_data(next_data[:,1],TIME_TYPE)
    scaled_data[:,2],scale_factor = scale_data(next_data[:,2],file_data_type)
    
    # plot data
    plot.make_graph_x_vs_t(next_file,plot_title,scaled_data)
    return True

def command_line_analysis(crop=True,scale=True,change_limits=False,repeats=True):
    done_analyzing = False
    num_files_analyzed = 0
    while not done_analyzing:
        next_file = input("Enter filename to analyze or press ENTER to finish. ")
        if (next_file == "" or not repeats):
            done_analyzing = True
        else:
            # import and crop data
            next_data,data_type = import_data(next_file)
            if crop:
                crop_type = input("If data is force data, press C to crop positive values. Otherwise, press ENTER to crop only trailing 0s. ")
                if (crop_type == "C" or crop_type == "c"):
                    print("Cropping positive values out of data.")
                    next_data = crop_data(next_data,crop_to_after_max=True)
                else:
                    if crop_type !="":
                        print("User entered unrecognized value %s as crop type."%crop_type)
                    next_data = crop_data(next_data)
                export_analysis_data(next_file,next_data,data_type,CROP)

            # scale data to standard units
            if scale:
                scaled_data,scale_factor = scale_data(next_data[:,1],TIME_TYPE)
                next_data[:,1] = scaled_data
                scaled_data,scale_factor = scale_data(next_data[:,2],data_type)
                next_data[:,2] = scaled_data
                export_analysis_data(next_file,next_data,data_type,SCALE)

            if change_limits:
                #combined_data = set_test_start(combined_data,54,325)
                next_data = set_test_start(next_data,0,217)
            
            # compute and export basic stats
            shape_and_stats = analysis_numerical(next_data,2,print_out=True)
            export_stats_data(next_file,shape_and_stats)

            # plot graph of data (vs time only, not other data arrays)
            plot_title = input("Enter a plot title to plot data or press ENTER to skip plotting. ")
            if plot_title != "":
                try:
                    plot.make_graph_x_vs_t(next_file,plot_title,next_data,ANALYSIS_DESCRIPTORS[PLOT],data_scaled=True)
                except:
                    print("Plotting not successful")
        num_files_analyzed += 1
    return num_files_analyzed

def command_line_comparison(scale=True,repeats=True):
    done_analyzing = False
    num_pairs_analyzed = 0
    while not done_analyzing:
        file1 = input("Enter first filename to analyze or press ENTER to finish. ")
        if (file1 == "" or not repeats):
            done_analyzing = True
        else:
            # import and crop data
            file2 = input("Enter second filename to analyze. ")
            data1,type1 = import_data(file1)
            data2,type2 = import_data(file2)

            # scale data to standard units
            if scale:
                scaled_data,scale_factor = scale_data(data1[:,2],type1)
                data1 = np.reshape(scaled_data,(-1,1))
                scaled_data,scale_factor = scale_data(data2[:,2],type2)
                data2 = np.reshape(scaled_data,(-1,1))
                print(data1)
                print(data2)
                print(np.shape(data1))
                print(np.shape(data2))
                if np.shape(data1)!=np.shape(data2):
                    min_len = min(np.shape(data1)[0],np.shape(data2)[0])
                    print(min_len)
                    data1 = data1[:min_len,:]
                    print(np.shape(data1))
                    print(data1)
                    data2 = data2[:min_len,:]
                combined_data = np.concatenate((data1,data2),axis=1)
                # export_analysis_data(next_file,next_data,data_type,SCALE)

            # plot graph of data (vs time only, not other data arrays)
            plot_title = input("Enter a plot title to plot data or press ENTER to skip plotting. ")
            if plot_title != "":
                try:
                    plot.make_graph_x_vs_y(file1,file2,plot_title,combined_data,x_col=0,y_col=1)
                except:
                    print("Plotting not successful")
        num_pairs_analyzed += 1
    return num_pairs_analyzed

def command_line_multiseries(crop=True,scale=True,convert=True,repeats=True,change_limits=True):
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
                    # import and crop data
                    file2 = input("Enter second filename to add to data series file pair. ")
                    data1,type1 = import_data(file1)
                    if file2 != "":
                        data2,type2 = import_data(file2)
                    else:
                        data2,type2 = import_data(file1)
                        data1[:,2] = data1[:,1]
                        type1 = TIME_TYPE
                        datafile = file1
                        file1 = files.get_base_filename_from_path(file1,remove_ext=True)
                        file1 = file1 + "_{0}{1}".format(files.DATA_DESCRIPTORS[type1],files.FILE_EXT)
                        file2 = datafile
                    
                    if crop:
                        if type1 == FORCE_TYPE:
                            data1 = crop_data(data1,crop_to_after_max=True)
                            export_analysis_data(file1,data1,type1,CROP)
                        elif type1 != TIME_TYPE:
                            data1 = crop_data(data1)
                            export_analysis_data(file1,data1,type1,CROP)

                        if type2 == FORCE_TYPE:
                            data2 = crop_data(data2,crop_to_after_max=True)
                            export_analysis_data(file2,data2,type2,CROP)
                        elif type2 != TIME_TYPE:
                            data2 = crop_data(data2)
                            export_analysis_data(file2,data2,type2,CROP)


                    # scale data to standard units
                    if scale:
                        scaled_data,scale_factor = scale_data(data1[:,2],type1)
                        data1 = np.reshape(scaled_data,(-1,1))
                        scaled_data,scale_factor = scale_data(data2[:,2],type2)
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
                            converted_data = convert_data(data1,type1,-1,data1[0][0])
                            data1 = np.reshape(converted_data,(-1,1))
                        if type2 == POSITION_TYPE:
                            converted_data = convert_data(data2,type2,-1,data2[0][0])
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
                        combined_data = set_test_start(combined_data,limit_left,limit_right)
                    
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
                    plot.make_multiseries_graph_x_vs_y(plot_title,data_series,ANALYSIS_DESCRIPTORS[PLOT],plot_size=(7,5),x_col=1,y_col=2,fit_line=True,filename_replacement=save_name)
                except:
                    print("Plotting not successful")
        num_plots += 1
    return num_plots

if __name__ == "__main__":
    # N.B.: since the import of other force_tester modules is an implicit relative import when this module is run directly,
    # to run this directly without errors, you have to run as a module and with qualified name i.e.:
    # python -m force_tester.analysis
    # Also, run FROM THE DIRECTORY ABOVE force_tester
    # See: https://peps.python.org/pep-0338/#import-statements-and-the-main-module

    #print(display_paths())
    command_line_multiseries(crop=False,change_limits=False)
    # command_line_comparison()
    # command_line_analysis(crop=False,change_limits=True)