''' PLOTTER CLASS v0.0 - Katie Allison
Test script for Plotter object (plot.py getting annoying to work with)

Created: 2024-04-18
Updated: 2024-04-18
'''
import numpy as np
import matplotlib.pyplot as plt
import os

from force_tester.helpers import files

# set root and subfolder locations
DATA_INPUT_PATH = files.get_path()
PLOT_OUTPUT_DIRECTORY = files.ANALYSIS_DIRECTORY
PLOT_OUTPUT_PATH = os.path.join(DATA_INPUT_PATH, PLOT_OUTPUT_DIRECTORY)

# set file type constants
PLOT_EXT = ".png"
DATA_DELIM = files.FILE_DELIM

class PlotterDebugger:
    DEFAULT_LINETYPES = ['r','g','b','k']
    PLOT = 9
    def __init__(self,fig_size=(7,5),lines=DEFAULT_LINETYPES):
        # set up plot size and line order
        self.fig,self.ax = plt.subplots(figsize=fig_size)
        self.linetypes = lines
        self.plot_path = PLOT_OUTPUT_PATH
        # reset data series index and make lists for data filenames and arrays
        self.data_series_ind = 0
        self.data_files = []
        self.data_series = []
        # reset legend entry index and make list for legend entry/corresp. index/corresp. type tuples
        self.legend_ind = 0
        self.legend_entries = []

    def get_next_linetype(self,corresp_data_ind=None,is_analysis=False):
        # use index of relevant data series
        # (either current or that associated with current analysis)
        index = self.data_series_ind - 1 # get index of last plotted series
        if is_analysis:
            if not (corresp_data_ind is None):
                index = corresp_data_ind
            type_setting = "--"
        else:
            type_setting = "-"

        # cycle through linetype list
        num_linetypes = len(self.linetypes)
        if index > num_linetypes:
            next_linetype = self.linetypes[index % num_linetypes]
        else:
            next_linetype = self.linetypes[index]
        return next_linetype + type_setting
        
    def add_legend_entry(self,legend_text,series_ind,is_analysis=False):
        legend_tuple = (legend_text,series_ind,is_analysis)
        self.legend_entries.append(legend_tuple)
        self.legend_ind += 1
        
    def add_data_series(self,file_tuple,data_arr):
        self.data_files.append(file_tuple)
        self.data_series.append(data_arr)
        self.data_series_ind += 1

    def plot_data_series(self,src_files,data,legend,cols,line=None,add_new=True):
        # if this data is being plotted for the first time, add to data and legend lists
        if add_new:
            self.add_legend_entry(legend,self.data_series_ind,is_analysis=False)
            self.add_data_series(src_files,data)

        # split data into independent and dependent coords and plot 
        indep_data = data[:,cols[0]]
        dep_data = data[:,cols[1]]

        # plot series
        if line is None:
            line = self.get_next_linetype()
        self.ax.plot(indep_data, dep_data, line, label=legend)

    def set_title(self,title):
        self.ax.set_title(title)

    def set_labels(self,axis_labels):
        self.ax.set_xlabel(axis_labels[0])
        self.ax.set_ylabel(axis_labels[1])

    def set_legend(self):
        self.ax.legend()

    def fully_label_plot(self,title_lbl,axis_lbls):
        self.set_title(title_lbl)
        self.set_labels(axis_lbls)
        self.set_legend()

    def show_plot(self):
        plt.show()

    def export_plot(self,filename,show=False):
        filepath = os.path.join(PLOT_OUTPUT_PATH, filename)
        plt.savefig(filepath)
        if show: self.show_plot()

    def command_line_plotter(self):
        def quick_import(filename):
            filepath = files.assemble_path(filename)
            print(filepath)
            data_arr = np.loadtxt(filepath,delimiter=DATA_DELIM,skiprows=1)
            data_type = files.get_data_type_from_path(filename)
            return data_arr,data_type
        
        def list_plot_commands():
            print("Possible plotting commands are:")
            for command in command_dict:
                command_purpose = command_dict[command][1]
                print(" * {0} : to {1}".format(command,command_purpose))

        def execute_plot_command(cmd,cmd_args):
            command_dict[cmd][0](*cmd_args)

        # Initialize dictionary of possible serial commands
        command_dict = {
            "LO": (quick_import,"load data from file",1),
            "DA": (self.plot_data_series,"plot single data series",4),
            "TS": (self.set_title,"set title string",1),
            "AS": (self.set_labels,"set axis label strings",1),
            "LE": (self.set_legend,"add legend",0),
            "SH": (self.show_plot,"show plot",0),
            "EX": (self.export_plot,"export plot",1)
        }
        # List commands for user
        print("-"*80)
        print("Entering direct serial communication with pneumatics")
        list_plot_commands()

        # Prompt user repeatedly
        num_commands = 0
        plotting_done = False
        while not plotting_done:
            command_prompt = input("Enter plot command, or enter LIST to see list of possible commands, or press ENTER to finish.")
            if command_prompt == "":
                plotting_done = True
            elif command_prompt == "LIST":
                list_plot_commands()
            
            # if user enters valid serial command, get values to include with command
            else:
                if not command_prompt in command_dict:
                    print("Please enter valid serial command from list.")
                else:
                    # prompt for any arguments
                    num_args = command_dict[command_prompt][2]
                    arg_list = []
                    for i in range(0,num_args):
                        arg_list.append(input("Enter string for next argument: "))
                    arg_tuple = tuple(arg_list)
                    # execute serial command
                    execute_plot_command(command_prompt,arg_tuple)
                    num_commands += 1

        return num_commands

def debug_plotter():
    PltrDebug = PlotterDebugger()
    PltrDebug.command_line_plotter()

if __name__ == "__main__":
    # N.B.: since the import of other force_tester modules is an implicit relative import when this module is run directly,
    # to run this directly without errors, you have to run as a module and with qualified name i.e.:
    # python -m force_tester.plotter_class
    # Also, run FROM THE DIRECTORY ABOVE force_tester
    # See: https://peps.python.org/pep-0338/#import-statements-and-the-main-module
    debug_plotter()