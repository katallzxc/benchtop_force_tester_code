''' GUI v0.2 - Katie Allison
Hatton Lab force testing platform control graphical user interface
This file based on code developed for Legere Reeds and sample code from Shipman's tkinter docs.

Created: 2021-11-16
Updated: 2023-05-26

This creates the graphical user interface for the motor control process.

Notes:
- likely add a "move_until" function that moves motor until target force reading is reached : therefore inputs for at least the target force and target force reading duration (?) possibly at both ends of test but at that point I'm just making a new test routine
- alternative: store test routines in csv and have "make a test" button -> likely a better strategy as well as a more familiar workflow
'''

import tkinter as tk
import time

import devices
import main
import move

STOP_ID = 0
GAUGE_ID = 1
CONTROLLER_ID = 2

GAUGE_PORT = 'COM4'
CONTROLLER_PORT = 'COM3'

controller = None
gauge = None

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
        self.output_text = ""

    def createWidgets(self):
        # make title label
        title_string = "Force Tester Control Options"
        self.appTitle = tk.Label(self, text=title_string)
        self.appTitle.grid(row=0, column=0, columnspan=3, padx=10)
        self.appTitle.config(font=("Verdana", 14),fg="#0000FF")
        self.option_add("*Font", "Verdana 10")

        # make description label
        description_string = "This app allows you to calibrate the force sensor, move the stage to a specific position, move the stage at a specific velocity, or run standard routines."
        self.appDescriptor = tk.Label(self, text=description_string)
        self.appDescriptor.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        # make error message
        self.errorLabel = tk.Label(self, text = "Errors: ")
        self.errorLabel.grid(row=2, column=0, padx=10, pady=10)
        self.errorLabel.config(font=("Verdana", 10),fg="#FF0000")
        self.errorMessage = tk.Label(self, text = "")
        self.errorMessage.grid(row=2, column=1, columnspan=2, padx=10, pady=10)
        self.errorMessage.config(font=("Verdana", 10),fg="#FF0000")

        # make output message
        self.outputLabel = tk.Label(self, text = "Outputs: ")
        self.outputLabel.grid(row=3, column=0, padx=10, pady=10)
        self.outputLabel.config(font=("Verdana", 10),fg="#00FF00")
        self.outputMessage = tk.Label(self, text = "")
        self.outputMessage.grid(row=3, column=1, columnspan=2, padx=10, pady=10)
        self.outputMessage.config(font=("Verdana", 10),fg="#00FF00")

        # make title for testing and setup actions
        description_string = "Setup and Manual Testing"
        self.setupDescriptor = tk.Label(self, text=description_string)
        self.setupDescriptor.grid(row=4, column=0, columnspan=3, padx=10)
        self.setupDescriptor.config(fg="#0000FF")

        # make start/stop buttons
        self.deviceStopButton = tk.Button(self, text = "Stop all connections",command = self.stop_device_connections,state = tk.DISABLED)
        self.deviceStopButton.grid(row=5, column=0, padx=10, pady=10)
        self.deviceStopButton.config(bg="#FF0000")
        self.gaugeSetupButton = tk.Button(self, text = "Start gauge connection",command = self.start_gauge_connection)
        self.gaugeSetupButton.grid(row=5, column=1, padx=10, pady=10)
        self.gaugeSetupButton.config(bg="#00FF00")
        self.controllerSetupButton = tk.Button(self, text = "Start controller connection",command = self.start_controller_connection)
        self.controllerSetupButton.grid(row=5, column=2, padx=10, pady=10)
        self.controllerSetupButton.config(bg="#00FF00")

        # make sensor testing descriptor, entry, and button
        self.gaugeTestLabel = tk.Label(self, text = "Set duration (s) of gauge test then press button to take readings for specified duration: ")
        self.gaugeTestLabel.grid(row=6, column=0, padx=10, pady=10)
        self.gaugeTestEntry = tk.Entry(self)
        self.gaugeTestEntry.grid(row=6, column=1, padx=10, pady=10)
        self.gaugeTestButton = tk.Button(self, text = "Take readings for set duration",command = self.take_gauge_readings)
        self.gaugeTestButton.grid(row=6, column=2, padx=10, pady=10)

        # make move to desciptor, entry, and button
        self.moveToLabel = tk.Label(self, text = "Set position (mm) using text entry then press button to move to position: ")
        self.moveToLabel.grid(row=7, column=0, padx=10, pady=10)
        self.moveToEntry = tk.Entry(self)
        self.moveToEntry.grid(row=7, column=1, padx=10, pady=10)
        self.moveToButton = tk.Button(self, text = "Move motor to position",command = self.run_move_to)
        self.moveToButton.grid(row=7, column=2, padx=10, pady=10)
        
        # make move at desciptor, entry, and button
        self.moveAtLabel = tk.Label(self, text = "Set velocity (mm/s) using text entry then press button to move at velocity: ")
        self.moveAtLabel.grid(row=8, column=0, padx=10, pady=10)
        self.moveAtEntry = tk.Entry(self)
        self.moveAtEntry.grid(row=8, column=1, padx=10, pady=10)
        self.moveAtButton = tk.Button(self, text = "Move motor at velocity",command = self.run_move_at)
        self.moveAtButton.grid(row=8, column=2, padx=10, pady=10)

        # make title for calibration and setup actions
        description_string = "Motion Routines for Calibration and Running Experiments"
        self.routineDescriptor = tk.Label(self, text=description_string)
        self.routineDescriptor.grid(row=9, column=0, columnspan=3, padx=10)
        self.routineDescriptor.config(fg="#0000FF")

        # make calibrate desciptor and button
        self.calibrateLabel = tk.Label(self, text = "Calibrate motor automatically by seeking limit switches")
        self.calibrateLabel.grid(row=10, column=0, padx=10, pady=10)
        self.calibrateButton = tk.Button(self, text = "Calibrate motor position",command = self.run_calibrate_routine)
        self.calibrateButton.grid(row=10, column=2, padx=10, pady=10)

        # make test routine desciptor, entry, and button
        self.testRoutineLabel = tk.Label(self, text = "Select specific test routine then press button to run test: ")
        self.testRoutineLabel.grid(row=11, column=0, padx=10, pady=10)
        self.testRoutineLabel.config(state = tk.DISABLED)
        self.testRoutineEntry = tk.Entry(self)
        self.testRoutineEntry.grid(row=11, column=1, padx=10, pady=10)
        self.testRoutineEntry.config(state = tk.DISABLED)
        self.testRoutineButton = tk.Button(self, text = "Run selected test",command = self.run_test_routine)
        self.testRoutineButton.grid(row=11, column=2, padx=10, pady=10)
        self.testRoutineButton.config(state = tk.DISABLED)

        # make listbox to show all routines
        self.separator = tk.Frame(self, bg="#0000FF")
        self.separator.grid(row=12, column=0, columnspan=3, padx=10, pady=10, sticky='nswe')
        self.separator.rowconfigure(0, weight=1)
        self.separator.columnconfigure(0, weight=1)
        self.separator.grid_propagate(0)
        description_string = "Available Test Routines:"
        self.testRoutineDisplayDescriptor = tk.Label(self, text=description_string)
        self.testRoutineDisplayDescriptor.grid(row=12, column=0, columnspan=3, padx=10)

        self.testRoutineDisplay = tk.Listbox(self,width=100,state=tk.DISABLED,relief=tk.FLAT,bg="#F0F0F0")
        self.testRoutineDisplay.grid(row=13, column=0, columnspan=3, padx=10)

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

    def start_gauge_connection(self):
        self.clear_error_text()
        global gauge
        gauge = devices.GaugeConnection(device=GAUGE_PORT)
        if gauge.serial is None: #TODO: Fix me - does not proceed to point of error display
            self.display_error_text("Gauge connection unsuccessful")
        else:
            self.clear_error_text()
            self.display_output_text("Gauge connection successful")
            self.gaugeSetupButton.config(state = tk.DISABLED)
            self.deviceStopButton.config(state = tk.NORMAL)

    def start_controller_connection(self):
        self.clear_error_text()
        global controller
        controller = devices.ControllerConnection(device=CONTROLLER_PORT)
        if controller.serial is None: #TODO: Fix me
            self.display_error_text("Controller connection unsuccessful")
        else:
            self.clear_error_text()
            self.display_output_text("Controller connection successful")
            self.controllerSetupButton.config(state = tk.DISABLED)
            self.deviceStopButton.config(state = tk.NORMAL)

    def stop_device_connections(self):
        self.clear_error_text()
        global controller
        global gauge

        if not ((controller is None) and (gauge is None)):
            controller.close() #TODO: fix me to work for only one
            gauge.close()
            self.clear_error_text()
            self.display_output_text("Device connections closed successfully")
        else:
            self.display_error_text("No connections active.")

        self.controllerSetupButton.config(state = tk.NORMAL)
        self.gaugeSetupButton.config(state = tk.NORMAL)
        self.deviceStopButton.config(state = tk.DISABLED)

    def take_gauge_readings(self):
        self.clear_error_text()
        readings_duration = self.gaugeTestEntry.get()
        if not readings_duration:
            self.display_error_text(0)
        else:
            self.display_output_text("Printing gauge results for %d seconds."%float(readings_duration))
            start_time = time.time()
            time.sleep(0.5)
            self.display_output_text("elapsed time %d"%(time.time()-start_time))
            #while True:#(time.time() - start_time) < readings_duration:
            for i in range(0,10):
                self.display_output_text("test "*i)
                time.sleep(0.5)
                #self.display_output_text("%d N"%gauge.get_force_measurement())
                self.display_output_text(str(time.time()-start_time))
            self.display_output_text("Done printing gauge results")

    def run_move_to(self):
        self.clear_error_text()
        goal_pos = self.moveToEntry.get()
        if not goal_pos:
            self.display_error_text(0)
        else:
            self.display_output_text("Moving motor %d mm from current position."%float(goal_pos))

    def run_move_at(self):
        self.clear_error_text()
        step_vel = self.moveAtEntry.get()
        if not step_vel.isnumeric():
            self.display_error_text(0)
        self.display_output_text("Moving at %i steps per min"%int(step_vel))

    def run_calibrate_routine(self):
        global controller
        self.clear_error_text()
        self.display_output_text("Calibrating")
        move.calibrate_motor(controller,speed=10,wait_for_completion=True)

    def run_test_routine(self):
        self.clear_error_text()
        test_id = self.testRoutineEntry.get()
        if not test_id.isnumeric():
            raise ValueError("Please identify test routine with a numeric ID!")
        self.display_output_text("Running test %i"%int(test_id))

# open and run application
def run_GUI():
    app_title = 'Run Force Tester'
    app = Application(app_title)
    app.after(MS_DELAY, app.check_condition)
    app.mainloop()

if __name__ == "__main__":
    run_GUI()