''' FILES v0 - Katie Allison
Helper code for handling filenames etc

Created: 2024-04-24 based on code originally in record.py

This code handles general filepath and filename-related operations.
E.g., generating consistent filenames, getting filepaths, adding or removing data type in filenames.
'''
import datetime as dt
import os

from force_tester.helpers.constants import TIME_TYPE,FORCE_TYPE,POSITION_TYPE,PRESSURE_TYPE

# set root and subfolder locations
REPO_DIRECTORY = "hattonlab"
DATA_DIRECTORY = "data_experimental"
ANALYSIS_DIRECTORY = "analysis"

# set file type constants
FILE_EXT = ".csv"
FILE_DELIM = ","
FILENAME_STRING_SEPARATOR = "_"
SEP_CHAR = FILENAME_STRING_SEPARATOR

# make dictionaries and global constants with strings associated with different data types
DATA_DESCRIPTORS = {
    TIME_TYPE:'time',
    FORCE_TYPE:'force',
    POSITION_TYPE:'position',
    PRESSURE_TYPE:'pressure'
    }
DATA_DESCRIPTORS_INVERSE = {value: key for key, value in DATA_DESCRIPTORS.items()}

def get_base_filename_from_path(filepath,remove_ext=False):
    """Strip any directory or (if applicable) extension information from filepath.
    NOTE: Takes off file extension by splitting by "." so don't put periods in filenames.
    """    
    base_filename = os.path.basename(filepath)
    if remove_ext:
        base_filename = base_filename.split(".")[0]
    return base_filename

def get_repository_path():
    """Get the path to the repo folder using constant for repo root directory.
    """
    root_path =  os.getcwd().split(REPO_DIRECTORY)[0]
    repo_path = os.path.join(root_path,REPO_DIRECTORY)
    return repo_path

def get_path(include_analysis_folder=False):
    """Get the path to the data folder using constants for data folder.
    If include_analysis_folder is true, gets the analysis subfolder of the data folder.

    NOTE: relies on having the data folder directly in the repo root directory and on having
    the analysis folder directly in the data folder.
    Also, constants for folder names must be changed if directory structure/names changed.

    Returns:
        data_path: path to experimental data folder (or to its analysis subfolder)
    """
    repo_root_path = get_repository_path()
    data_path = os.path.join(repo_root_path,DATA_DIRECTORY)
    if include_analysis_folder:
        data_path = os.path.join(data_path,ANALYSIS_DIRECTORY)
    return data_path

def assemble_path(initial_path,is_analysis=False):
    """Assembles data/analysis folder filepath and filename into complete path, 
    using base filename stripping to avoid accidental duplication of data/analysis
    folder filepath elements.
    """
    filename = get_base_filename_from_path(initial_path)
    base_path = get_path(is_analysis)
    full_path_to_file = os.path.join(base_path,filename)
    return full_path_to_file

def get_timestamp():
    """Generate timestamp in YYYYMMDD_hhmm format.

    Returns:
        timestamp: string with formatted date and time
    """    
    date_format = "%Y%m%d"
    time_format = "%H%M"
    stamp_format = date_format + SEP_CHAR + time_format
    timestamp = dt.datetime.now().strftime(stamp_format)
    return timestamp

def get_data_filename(file_desc,file_time,file_type):
    """Assembles description, timestamp, and string marking type of data 
    (e.g., force/position/pressure/time, log, plot, pulled from DATA_DESCRIPTORS 
    or equivalents in record.py or analysis.py) into filename with extension.

    Args:
        file_desc (string): test name or other description of contents
        file_time (str): timestamp for data collection or export
        file_type (str): string marking type of data

    Returns:
        filename (str): assembled string for full filename
    """    
    filename = file_desc + SEP_CHAR + file_time 
    filename += SEP_CHAR + file_type
    filename += FILE_EXT
    return filename

def get_analysis_filename(data_filename,analysis_desc):
    """Assembles original filename (or user-entered combination of/summary of
    multiple data filenames) and new description string(s) associated with
    analysis processes into a filename for analysis output files.

    Args:
        data_filename (str): original/combined data filename
        analysis_desc (str): string with analysis process description(s)

    Returns:
        filename (str): assembled string for full filename
    """    
    filename = get_base_filename_from_path(data_filename,remove_ext=True)
    filename += SEP_CHAR + analysis_desc 
    filename += FILE_EXT
    return filename

def get_generic_filename(namestr,use_analysis=True,subdirectory="",file_ext=FILE_EXT):
    filepath = get_path(use_analysis)
    filename = namestr + file_ext
    fullpath = os.path.join(filepath,subdirectory,filename)
    return fullpath

def get_data_type_string_from_path(filepath):
    """Takes in a filepath and crops to just the filename, then crops the filename to 
    the last string after separator character (_), which should be the type descriptor.
    """
    base_filename = get_base_filename_from_path(filepath,remove_ext=True)
    data_type_str = base_filename.split(SEP_CHAR)[-1]
    return data_type_str

def get_data_type_from_path(filepath):
    """Given a filepath, strips the part of the filename that describes the data type
    and looks this descriptor up in the inverse descriptor dictionary to find the
    integer key for the data type. (where, e.g., "time" corresponds to 0 (TIME_TYPE))

    Args:
        filepath (str): filepath including a known data type descriptor string

    Returns:
        data_type (int): key from data type dictionary associated with this string
    """
    data_type_str = get_data_type_string_from_path(filepath)
    data_type = DATA_DESCRIPTORS_INVERSE[data_type_str]
    return data_type

def crop_data_type_from_filename(filename):
    """Given a filename, returns the parts of the filename leading up to and not
    including the type string (i.e., returns only the name/description and timestamp)

    Args:
        filename (str): full filename including extension

    Returns:
        cropped_filename (str): partial filename (incl. description and timestamp)
    """    
    base_filename = get_base_filename_from_path(filename,remove_ext=True)
    filetype = get_data_type_string_from_path(base_filename)
    len_cropped_filename = len(base_filename) - len(filetype) - len(SEP_CHAR)
    cropped_filename = base_filename[:len_cropped_filename]
    return cropped_filename

def get_file_list_from_path(filter_txt=None):
    """Returns a list of all files in the data directory (filtering by a substring if needed)

    Args:
        filter_txt (str, optional): Substring by which to filter. Defaults to None.

    Returns:
        filtered_datafile_list (list): list of all files, including directories, in data directory
    """    
    all_datafile_list = os.listdir(get_path())
    if filter_txt is None:
        filtered_datafile_list = all_datafile_list
    else:
        filtered_datafile_list = []
        for file in all_datafile_list:
            if filter_txt in file:
                filtered_datafile_list.append(file)
    return filtered_datafile_list

def fix_file_ext(prompt=True):
    """Helper function to fix files that have been exported in CSV format but without CSV file extension.
    """    
    # list all files in data folder
    base_path = get_path()
    files = os.listdir(base_path)
    for file in files:
        # check that path is not to folder
        fullpath = os.path.join(base_path, file)
        if (not os.path.isdir(fullpath)):
            # if file does not have a file extension, add CSV extension
            if len(file.split(".")) < 2:
                print(os.path.isdir(fullpath))
                if prompt:
                    prompt_result = input("Add %s extension to %s file? Press R to rename. "%(FILE_EXT,file))
                if (not prompt) or (prompt_result == "R"):
                        os.rename(fullpath, fullpath + FILE_EXT)

def print_dictionary_constants(constant_dict):
    """Helper function to print all keys and values from a dictionary 
    (intended for use in checking values in a dictionary defined as a global constant).
    """    
    for key in constant_dict:
        print("{0}:{1}".format(key,constant_dict[key]))

if __name__ == "__main__":
    # N.B.: since the import of constants is an implicit relative import when this module is run directly,
    # to run this directly without errors, you have to run as a module and with qualified name i.e.:
    # python -m force_tester.helpers.files
    # Also, run FROM THE DIRECTORY ABOVE force_tester
    # See: https://peps.python.org/pep-0338/#import-statements-and-the-main-module

    print_constants = False
    get_file_list = False
    get_file_name = True
    if print_constants:
        print("-"*50 + "constants" + "-"*50)
        print("Time key is {0}, force is {1}, position is {2}, and pressure is {3}.".format(TIME_TYPE,FORCE_TYPE,POSITION_TYPE,PRESSURE_TYPE))
        print("-"*50 + "data filename descriptors" + "-"*50)
        print_dictionary_constants(DATA_DESCRIPTORS)
    if get_file_list:
        print(get_file_list_from_path())
    if get_file_name:
        test_filename = get_data_filename("testDATAtest",get_timestamp(),DATA_DESCRIPTORS[TIME_TYPE])
        print(test_filename)
        print(get_analysis_filename(test_filename,"test_analysis"))