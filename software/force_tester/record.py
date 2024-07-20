''' RECORD v1.1 - Katie Allison
Hatton Lab force testing platform data recording (formatting + export) code.

Created: 2023-12-11
Updated: 2024-02-09

This code saves raw test data from force testing operations to CSV text files.
This script also contains global constants and dictionaries that are used by analysis.py and others.

Notes:
- relies on specific directory structure and directory names
- always exports data vs time
- always exports a log file along with data exports
'''
import datetime as dt
import numpy as np
import pandas as pd
import os

try:
    from .helpers import files
except Exception:
    from helpers import files

# get keys for data type indicators from files.py
TIME_TYPE = files.TIME_TYPE
FORCE_TYPE = files.FORCE_TYPE
POSITION_TYPE = files.POSITION_TYPE
PRESSURE_TYPE = files.PRESSURE_TYPE

# make dictionaries and global constants with strings associated with different data types
LOG_TYPE_NAME = 'log'
DATA_TYPE_NAMES = files.DATA_DESCRIPTORS
LOG_HEADERS = ['Parameter Value/Export Filename']
DATA_HEADERS = {
    TIME_TYPE:'Time',
    FORCE_TYPE:'Force',
    POSITION_TYPE:'Motor position',
    PRESSURE_TYPE:('Actual actuation pressure','Target actuation pressure')
    }
DATA_RECORDING_UNITS = {
    TIME_TYPE:'[ns]',
    FORCE_TYPE:'[N]',
    POSITION_TYPE:'[steps]',
    PRESSURE_TYPE:'[kPa]'
    }
DATA_STANDARD_UNITS = {
    TIME_TYPE:'[seconds]',
    FORCE_TYPE:'[N]',
    POSITION_TYPE:'[mm]',
    PRESSURE_TYPE:'[kPa]'
}

def get_timestamp():
    """Generate timestamp in YYYYMMDD_hhmm format.

    Returns:
        timestamp: string with formatted date and time
    """    
    date_format = "%Y%m%d"
    time_format = "%H%M"
    stamp_format = date_format + "_" + time_format
    timestamp = dt.datetime.now().strftime(stamp_format)
    return timestamp

def format_data(data_type,data_arr):
    """Formats test data array into pandas DataFrame with column header strings and row indices.

    Args:
        data_type (int): Key used to get datatype-specific strings from constant dictionaries.
        data_arr (numpy ndarray): Array of test data with time data in column 0.

    Returns:
        data_df (pandas DataFrame): formatted output data
    """
    def get_headers(num_cols,data_type_key):
        """Helper function that interprets (possibly tuple) data header constant into
        one or more header strings and packs time header into list with data header string(s).
        """        
        time_header = DATA_HEADERS[TIME_TYPE]
        data_header = DATA_HEADERS[data_type_key]

        # pack headers into list
        if type(data_header) is tuple:
            # if type of data has more than one header string available, unpack header strings
            headers = [time_header,*data_header]
            if num_cols < 3: # but don't use all header strings if data is not present for all
                headers = headers[0:num_cols]
        else:
            headers = [time_header,data_header]

        # add units to headers
        headers[0] += " " + DATA_RECORDING_UNITS[TIME_TYPE]
        for i in range(1,len(headers)):
            headers[i] += " " + DATA_RECORDING_UNITS[data_type_key]
        return headers

    # put data into dataframe with headers
    num_data_cols = data_arr.shape[-1]
    data_df = pd.DataFrame(data_arr)
    data_df.columns = get_headers(num_data_cols,data_type)
    return data_df

def format_log(test_params):
    """Formats dictionary of test parameters into pandas DataFrame.

    Args:
        test_params (dict): dictionary containing test parameter names and values.

    Returns:
        param_df (pandas DataFrame): formatted output data
    """    
    param_df = pd.DataFrame.from_dict(test_params,orient='index')
    param_df.columns = LOG_HEADERS
    return param_df

def export_outputs(dataframe,filepath,strname,strtime,data_type=TIME_TYPE,is_log=False):
    """Exports data from a dataframe to a CSV file. If dataframe contains test data, 
    uses data_type to get relevant header information from global constant dictionaries.
    If dataframe contains log data, uses log-related global constants.

    Args:
        dataframe (pandas DataFrame): formatted output data with column headers and row indices
        filepath (str): path to export location
        strname (str): test name (usually containing type of test and any specific details like material)
        strtime (str): timestamp for export
        data_type (int, optional): Key used to get datatype-specific strings from constant dictionaries.
        is_log (bool, optional): Indicates whether output is log data. Defaults to False.

    Returns:
        filename (str): filename (without path and file extension) for exported data
    """
    if is_log:
        strtype = LOG_TYPE_NAME
    else:
        strtype = DATA_TYPE_NAMES[data_type]
    filename = files.get_data_filename(strname,strtime,strtype)
    export_path = os.path.join(filepath, filename)
    dataframe.to_csv(export_path)
    return filename

def record_all_test_data(strtest,data_dict,params_dict):
    """Main function that loops through a dictionary of data arrays from a test and saves
    all data in CSV files, as well as log data (including filenames of data exports) in a
    log CSV file.

    Args:
        strtest (str): string describing test, used in filename for exports
        data_dict (dict): dictionary containing all test data arrays (keys are datatype constants from files.py)
        params_dict (dict): dictionary containing test parameter values (keys are parameter name/description)

    Returns:
        new_log_name (str): filename  (without path and file extension) for exported log file
    """
    # get export filepath and timestamp
    strpath = files.get_path()
    strtime = get_timestamp()
    params_dict['timestamp'] = strtime
    file_strings = (strpath,strtest,strtime)
    
    # export all data arrays (for each relevant data type)
    data_exports = []
    for data_type_key in data_dict:
        data_frame = format_data(data_type_key,data_dict[data_type_key])
        new_export_name = export_outputs(data_frame,*file_strings,data_type_key)
        data_exports.append(new_export_name)

    # add export filenames to metadata in log dictionary and export log
    params_dict['exported files'] = data_exports #TODO: fix to have semicolons not commas
    param_frame = format_log(params_dict)
    new_log_name = export_outputs(param_frame,*file_strings,is_log=True)
    return new_log_name

def print_dictionary_constants(constant_dict):
    """Helper function to print all keys and values from a dictionary 
    (intended for use in checking values in a dictionary defined as a global constant).
    """    
    for key in constant_dict:
        print("{0}:{1}".format(key,constant_dict[key]))

def make_dummy_dict(make_log,i=10,j=2,k=3):
    """Makes dummy dictionary with log-data-like elements or data-array-like elements for testing record.py
    """
    if make_log:
        return {'test':0,'test2':'str'}
    else:
        return {FORCE_TYPE: np.random.rand(i,j),POSITION_TYPE: np.random.rand(i,j),PRESSURE_TYPE: np.random.rand(i,k)}

if __name__ == "__main__":
    log_export_name = record_all_test_data("dummyoutput",make_dummy_dict(False),make_dummy_dict(True))
    print("Log file exported as {0} to data folder: {1}.".format(log_export_name,files.get_path()))