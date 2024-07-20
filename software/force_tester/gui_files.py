''' GUI_FILES v0. - Katie Allison
Hatton Lab force testing platform control graphical user interface

Created: 2024-02-08
Updated: 2024-02-08

This creates the graphical user interface for selecting data files.
'''

import tkinter as tk
from tkinter import filedialog
import time
import numpy as np

from force_tester import analysis

from force_tester.helpers import stats
from force_tester.helpers import files

STOP_ID = 0
GAUGE_ID = 1
CONTROLLER_ID = 2

MS_DELAY = 50

# set up graphical user interface
class Application(tk.Frame):
    def __init__(self, title, master = None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()
        self.master.title(title)
        self.master.eval('tk::PlaceWindow . center')
        self.error_text = ""
        self.clear_error_text()
        self.output_text = analysis.display_paths()
        self.display_output_text(self.output_text)
        self.curr_file = ""
        self.curr_data = None
        self.data_type = 0

    def createWidgets(self):
        # make description label
        description_string = "This app allows you to pick data files to analyze and view brief results of analysis."
        self.appDescriptor = tk.Label(self, text=description_string)
        self.appDescriptor.grid(row=0, column=0, columnspan=5, padx=10, pady=10)
        self.appDescriptor.config(font=("Verdana", 10),fg="#000000")

        # make file picker
        self.filePickButton = tk.Button(self, text = "Select File",command = self.start_file_picker,state = tk.NORMAL)
        self.filePickButton.grid(row=1, column=0, padx=10, pady=10)
        self.filePickButton.config(bg="#FFAAAA",font=("Verdana", 10))
        self.filePickLabel = tk.Label(self, text = "Select a file to enable data import and analysis. Default start directory is set in the record.py module.")
        self.filePickLabel.grid(row=1, column=1, columnspan=4, padx=10, pady=10)
        self.filePickLabel.config(font=("Verdana", 10),fg="#000000")

        # make start/stop buttons
        self.importDataButton = tk.Button(self, text = "Import data",command = self.import_data,state = tk.DISABLED)
        self.importDataButton.grid(row=3, column=0, padx=10, pady=10)
        self.importDataButton.config(bg="#FFAAAA",font=("Verdana", 10))
        self.runNumericalButton = tk.Button(self, text = "Run numerical analysis",command = self.run_numbers,state = tk.DISABLED)
        self.runNumericalButton.grid(row=3, column=1, padx=10, pady=10)
        self.runNumericalButton.config(bg="#AAFFAA",font=("Verdana", 10))
        self.runGraphicalButton = tk.Button(self, text = "Make graph",command = self.make_graph,state = tk.DISABLED)
        self.runGraphicalButton.grid(row=3, column=2, padx=10, pady=10)
        self.runGraphicalButton.config(bg="#AAFFAA",font=("Verdana", 10))

        # make graph title input
        self.plotTitleLabel = tk.Label(self, text = "Set plot title:")
        self.plotTitleLabel.grid(row=3, column=3, padx=10, pady=10)
        self.plotTitleLabel.config(font=("Verdana", 10),fg="#000000")
        self.plotTitleEntry = tk.Entry(self)
        self.plotTitleEntry.grid(row=3, column=4, padx=10, pady=10)

        # make listbox to show all routines
        self.separator = tk.Frame(self, bg="#0000FF")
        self.separator.grid(row=4, column=0, columnspan=5, padx=10, pady=10, sticky='nswe')
        # self.separator.rowconfigure(0, weight=1)
        # self.separator.columnconfigure(0, weight=1)
        # self.separator.grid_propagate(0)

        # make error message
        self.errorLabel = tk.Label(self, text = "Errors: ")
        self.errorLabel.grid(row=5, column=0, padx=10, pady=10)
        self.errorLabel.config(font=("Verdana", 10),fg="#AA0000")
        self.errorMessage = tk.Label(self, text = "")
        self.errorMessage.grid(row=5, column=1, columnspan=4, padx=10, pady=10)
        self.errorMessage.config(font=("Verdana", 10),fg="#AA0000")

        # make output message
        self.outputLabel = tk.Label(self, text = "Outputs: ")
        self.outputLabel.grid(row=6, column=0, padx=10, pady=10)
        self.outputLabel.config(font=("Verdana", 10),fg="#00AA00")
        self.outputMessage = tk.Label(self, text = "")
        self.outputMessage.grid(row=6, column=1, columnspan=4, padx=10, pady=10)
        self.outputMessage.config(font=("Verdana", 10),fg="#00AA00")

    def check_condition(self):
        #TODO: fix me
        self.outputMessage.config(text=self.output_text)
        self.errorMessage.config(text=self.error_text)
        self.after(MS_DELAY, self.check_condition)

    def display_error_text(self,error_code):
        if error_code == 0:
            self.error_text = "Please enter a value in the textbox before executing this command."
        else:
            self.error_text = error_code
        self.errorMessage.config(text=self.error_text)

    def clear_error_text(self):
        self.error_text = ""
        self.errorMessage.config(text=self.error_text)

    def display_output_text(self,output_data):
        self.output_text = output_data
        self.outputMessage.config(text=self.output_text)

    def clear_output_text(self):
        self.output_text = ''
        self.outputMessage.config(text=self.output_text)

    def start_file_picker(self):
        self.clear_error_text()
        self.curr_file = filedialog.askopenfilename()
        self.display_error_text("No file selected")
        file_path = self.curr_file
        if file_path == "":
            self.display_error_text("No file selected")
        else:
            self.clear_error_text()
            self.filePickLabel.config(text="Selected file: %s"%file_path)
            self.runNumericalButton.config(state = tk.DISABLED)
            self.runGraphicalButton.config(state = tk.DISABLED)
            self.importDataButton.config(state = tk.NORMAL)
            return file_path
        
    def import_data(self):
        try:
            self.display_output_text(self.curr_file)
            self.curr_data,self.data_type = analysis.import_data(self.curr_file)
            data_type_str = files.DATA_DESCRIPTORS[self.data_type]
            try:
                curr_shape = stats.get_shape(self.curr_data)
                self.display_output_text(curr_shape[0])
                output_string = "{0} rows and {1} columns in ".format(curr_shape[0],curr_shape[1])
                output_string=output_string + "{0} data file (including any index columns).".format(data_type_str)
                self.display_output_text(output_string)
                self.runNumericalButton.config(state = tk.NORMAL)
                self.runGraphicalButton.config(state = tk.NORMAL)
            except:
                self.display_error_text("Data imported but shape fetch unsuccessful")
        except:
            self.display_error_text("Data import not successful")
        return self.curr_data
    
    def run_numbers(self):
        self.clear_output_text()
        try:
            stats = analysis.auto_analysis_numerical(self.curr_file,self.curr_data,self.data_type)
            output_string = "Shape: {0}\nMean: {1}\nMedian: {2}\n".format(stats["shape"],stats["mean"],stats["median"])
            output_string += "Minimum: {0}\nMaximum: {1}".format(stats["minimum"],stats["maximum"])
            self.display_output_text(output_string)
        except:
            self.display_error_text("Data numerical analysis not successful")
    
    def get_plot_title(self):
        self.clear_error_text()
        plt_title = self.plotTitleEntry.get()
        if plt_title == "":
            self.display_error_text("Enter a title for the plot.")
        return plt_title

    def make_graph(self):
        # get plot title
        plot_title = self.get_plot_title()
        # make plot
        try:
            if plot_title != "":
                if self.data_type == files.FORCE_TYPE:
                    self.curr_data = analysis.crop_data(self.curr_data,crop_to_after_max=True)
                else:
                    self.curr_data = analysis.crop_data(self.curr_data)
                analysis.auto_analysis_graphical(self.curr_file,self.curr_data,self.data_type,plot_title)
                output_string = "Plot saving to: {0}".format(self.curr_file)
                self.display_output_text(output_string)
        except:
            self.display_error_text("Data plotting not successful")

    # def start_controller_connection(self):
    #     self.clear_error_text()
    #     global controller
    #     controller = devices.ControllerConnection(device=CONTROLLER_PORT)
    #     if controller.serial is None: #TODO: Fix me
    #         self.display_error_text("Controller connection unsuccessful")
    #     else:
    #         self.clear_error_text()
    #         self.display_output_text("Controller connection successful")
    #         self.controllerSetupButton.config(state = tk.DISABLED)
    #         self.deviceStopButton.config(state = tk.NORMAL)

    # def stop_device_connections(self):
    #     self.clear_error_text()
    #     global controller
    #     global gauge

    #     if not ((controller is None) and (gauge is None)):
    #         controller.close() #TODO: fix me to work for only one
    #         gauge.close()
    #         self.clear_error_text()
    #         self.display_output_text("Device connections closed successfully")
    #     else:
    #         self.display_error_text("No connections active.")

    #     self.controllerSetupButton.config(state = tk.NORMAL)
    #     self.gaugeSetupButton.config(state = tk.NORMAL)
    #     self.deviceStopButton.config(state = tk.DISABLED)

    # def take_gauge_readings(self):
    #     self.clear_error_text()
    #     readings_duration = self.gaugeTestEntry.get()
    #     if not readings_duration:
    #         self.display_error_text(0)
    #     else:
    #         self.display_output_text("Printing gauge results for %d seconds."%float(readings_duration))
    #         start_time = time.time()
    #         time.sleep(0.5)
    #         self.display_output_text("elapsed time %d"%(time.time()-start_time))
    #         #while True:#(time.time() - start_time) < readings_duration:
    #         for i in range(0,10):
    #             self.display_output_text("test "*i)
    #             time.sleep(0.5)
    #             #self.display_output_text("%d N"%gauge.get_force_measurement())
    #             self.display_output_text(str(time.time()-start_time))
    #         self.display_output_text("Done printing gauge results")

    # def run_move_to(self):
    #     self.clear_error_text()
    #     goal_pos = self.moveToEntry.get()
    #     if not goal_pos:
    #         self.display_error_text(0)
    #     else:
    #         self.display_output_text("Moving motor %d mm from current position."%float(goal_pos))

    # def run_move_at(self):
    #     self.clear_error_text()
    #     step_vel = self.moveAtEntry.get()
    #     if not step_vel.isnumeric():
    #         self.display_error_text(0)
    #     self.display_output_text("Moving at %i steps per min"%int(step_vel))

    # def run_calibrate_routine(self):
    #     global controller
    #     self.clear_error_text()
    #     self.display_output_text("Calibrating")
    #     move.calibrate_motor(controller,speed=10,wait_for_completion=True)

    # def run_test_routine(self):
    #     self.clear_error_text()
    #     test_id = self.testRoutineEntry.get()
    #     if not test_id.isnumeric():
    #         raise ValueError("Please identify test routine with a numeric ID!")
    #     self.display_output_text("Running test %i"%int(test_id))

# open and run application
def run_GUI():
    app_title = 'Analyze Force Test Data'
    app = Application(app_title)
    app.after(MS_DELAY, app.check_condition)
    app.mainloop()

if __name__ == "__main__":
    # N.B.: since the import of other force_tester modules is an implicit relative import when this module is run directly,
    # to run this directly without errors, you have to run as a module and with qualified name i.e.:
    # python -m force_tester.gui_files
    # Also, run FROM THE DIRECTORY ABOVE force_tester
    # See: https://peps.python.org/pep-0338/#import-statements-and-the-main-module

    run_GUI()