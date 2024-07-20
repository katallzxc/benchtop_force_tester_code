''' GUI_PLOTS v0. - Katie Allison
Hatton Lab force testing platform control graphical user interface

Created: 2024-02-10
Updated: 2024-02-10

This creates the graphical user interface for creating and annotating plots.
Code here partially from: https://stackoverflow.com/questions/30774281/update-matplotlib-plot-in-tkinter-gui
'''
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import filedialog
import numpy as np

from force_tester import analysis
from force_tester.helpers import files

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

    def createWidgets(self):
        # make description label
        description_string = "This app allows you to create and annotate plots using data pulled from CSV files."
        self.appDescriptor = tk.Label(self, text=description_string)
        self.appDescriptor.grid(row=0, column=0, columnspan=6, padx=10, pady=10)
        self.appDescriptor.config(font=("Verdana", 10),fg="#000000")
        self.clearButton = tk.Button(self, text = "Clear Plot",command = self.empty_plot,state = tk.NORMAL)
        self.clearButton.grid(row=0, column=6, columnspan=2, padx=10, pady=10)
        self.clearButton.config(bg="#FFAAAA",font=("Verdana", 10))

        # make error message
        self.errorLabel = tk.Label(self, text = "Errors: ")
        self.errorLabel.grid(row=1, column=0, padx=10, pady=10)
        self.errorLabel.config(font=("Verdana", 10),fg="#AA0000")
        self.errorMessage = tk.Label(self, text = "")
        self.errorMessage.grid(row=1, column=1, columnspan=7, padx=10, pady=10)
        self.errorMessage.config(font=("Verdana", 10),fg="#AA0000")

        # make output message
        self.outputLabel = tk.Label(self, text = "Outputs: ")
        self.outputLabel.grid(row=2, column=0, padx=10, pady=10)
        self.outputLabel.config(font=("Verdana", 10),fg="#00AA00")
        self.outputMessage = tk.Label(self, text = "")
        self.outputMessage.grid(row=2, column=1, columnspan=7, padx=10, pady=10)
        self.outputMessage.config(font=("Verdana", 10),fg="#00AA00")

        # make divider
        self.separator = tk.Frame(self, bg="#AA0000")
        self.separator.grid(row=3, column=0, columnspan=8, padx=10, pady=10, sticky='nswe')

        # make file picker info label
        self.filePickInfoLabel = tk.Label(self, text = "Select files for X and Y data to enable data import and analysis. Default start directory is set in the record.py module.")
        self.filePickInfoLabel.grid(row=4, column=0, columnspan=8, padx=10, pady=10)
        self.filePickInfoLabel.config(font=("Verdana", 10),fg="#000000")

        # make widgets for X data import
        self.filePickXButton = tk.Button(self, text = "Select X Data",command = self.get_x_data,state = tk.NORMAL)
        self.filePickXButton.grid(row=5, column=0, padx=10, pady=10)
        self.filePickXButton.config(bg="#AAAAAA",font=("Verdana", 10))
        self.filePickXDataLabel = tk.Label(self, text = "No file selected")
        self.filePickXDataLabel.grid(row=5, column=1, columnspan=7, padx=10, pady=10)
        self.filePickXDataLabel.config(font=("Verdana", 10),fg="#000000")

        # make widgets for X column selection
        self.filePickXColLabel = tk.Label(self, text = "Select column to use for X data:")
        self.filePickXColLabel.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
        self.filePickXColLabel.config(font=("Verdana", 10),fg="#000000")
        self.filePickXColEntry = tk.Entry(self)
        self.filePickXColEntry.grid(row=6, column=2, padx=10, pady=10)
        self.filePickXColButton = tk.Button(self, text = "Set X Column",command = self.set_x_column,state = tk.NORMAL)
        self.filePickXColButton.grid(row=6, column=3, padx=10, pady=10)
        self.filePickXColButton.config(bg="#AAAAAA",font=("Verdana", 10))
        self.filePickXColHeadLabel = tk.Label(self, text = "No column selected")
        self.filePickXColHeadLabel.grid(row=6, column=4, columnspan=4, padx=10, pady=10)
        self.filePickXColHeadLabel.config(font=("Verdana", 10),fg="#000000")

        # make widgets for Y data import
        self.filePickYButton = tk.Button(self, text = "Select Y Data",command = self.get_y_data,state = tk.NORMAL)
        self.filePickYButton.grid(row=7, column=0, padx=10, pady=10)
        self.filePickYButton.config(bg="#AAAAAA",font=("Verdana", 10))
        self.filePickYDataLabel = tk.Label(self, text = "No file selected")
        self.filePickYDataLabel.grid(row=7, column=1, columnspan=7, padx=10, pady=10)
        self.filePickYDataLabel.config(font=("Verdana", 10),fg="#000000")

        # make widgets for Y column selection
        self.filePickYColLabel = tk.Label(self, text = "Select column to use for Y data:")
        self.filePickYColLabel.grid(row=8, column=0, columnspan=2, padx=10, pady=10)
        self.filePickYColLabel.config(font=("Verdana", 10),fg="#000000")
        self.filePickYColEntry = tk.Entry(self)
        self.filePickYColEntry.grid(row=8, column=2, padx=10, pady=10)
        self.filePickYColButton = tk.Button(self, text = "Set Y Column",command = self.set_y_column,state = tk.NORMAL)
        self.filePickYColButton.grid(row=8, column=3, padx=10, pady=10)
        self.filePickYColButton.config(bg="#AAAAAA",font=("Verdana", 10))
        self.filePickYColHeadLabel = tk.Label(self, text = "No column selected")
        self.filePickYColHeadLabel.grid(row=8, column=4, columnspan=4, padx=10, pady=10)
        self.filePickYColHeadLabel.config(font=("Verdana", 10),fg="#000000")

        # make divider
        self.separator = tk.Frame(self, bg="#00AA00")
        self.separator.grid(row=9, column=0, columnspan=8, padx=10, pady=10, sticky='nswe')

        # # make start/stop buttons
        # self.importDataButton = tk.Button(self, text = "Import data",command = self.import_data,state = tk.DISABLED)
        # self.importDataButton.grid(row=3, column=0, padx=10, pady=10)
        # self.importDataButton.config(bg="#FFAAAA",font=("Verdana", 10))
        # self.runNumericalButton = tk.Button(self, text = "Run numerical analysis",command = self.run_numbers,state = tk.DISABLED)
        # self.runNumericalButton.grid(row=3, column=1, padx=10, pady=10)
        # self.runNumericalButton.config(bg="#AAFFAA",font=("Verdana", 10))
        # self.runGraphicalButton = tk.Button(self, text = "Make graph",command = self.make_graph,state = tk.DISABLED)
        # self.runGraphicalButton.grid(row=3, column=2, padx=10, pady=10)
        # self.runGraphicalButton.config(bg="#AAFFAA",font=("Verdana", 10))

        # # make graph title input
        # self.plotTitleLabel = tk.Label(self, text = "Set plot title:")
        # self.plotTitleLabel.grid(row=3, column=3, padx=10, pady=10)
        # self.plotTitleLabel.config(font=("Verdana", 10),fg="#000000")
        # self.plotTitleEntry = tk.Entry(self)
        # self.plotTitleEntry.grid(row=3, column=4, padx=10, pady=10)


        # # make divider
        # self.separator = tk.Frame(self, bg="#00AA00")
        # self.separator.grid(row=8, column=0, columnspan=8, padx=10, pady=10, sticky='nswe')
        # make plot
        fig,ax = plt.subplots(figsize=(4,3))
        canvas=FigureCanvasTkAgg(fig,master=self.master)
        canvas.get_tk_widget().grid(row=10,column=0,columnspan=8)
        canvas.draw()

        self.plotbutton=tk.Button(text="plot", command=lambda: self.plot(canvas,ax))
        self.plotbutton.grid(row=11,column=4)

    def empty_plot(self,ax):
        ax.clear()

    def plot(self,canvas,ax):
        c = ['r','b','g']  # plot marker colors
        ax.clear()
        ax.plot(self.x_data,self.y_data,marker='o', color='r')
        canvas.draw()

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
        try:
            selected_file = filedialog.askopenfilename()
            if selected_file == "":
                self.display_error_text("No file selected")
            else:
                self.clear_error_text()
        except:
            self.display_error_text("File selection not successful")
        return selected_file
    
    def import_data(self,filestring):
        try:
            imported_data,data_type = analysis.import_data(filestring)
            data_type_str = files.DATA_DESCRIPTORS[data_type]
            self.display_output_text("%s-time data imported"%data_type_str)
        except:
            self.display_error_text("Data import not successful")
        return imported_data
        
    def get_x_data(self):
        self.x_file = self.start_file_picker()
        self.filePickXDataLabel.config(text=self.x_file)
        self.x_data_all = self.import_data(self.x_file)

    def get_y_data(self):
        self.y_file = self.start_file_picker()
        self.filePickYDataLabel.config(text=self.y_file)
        self.y_data_all = self.import_data(self.y_file)

    def set_x_column(self):
        self.clear_error_text()
        try:
            curr_col = int(self.filePickXColEntry.get())
            headers = analysis.import_headers(self.x_file)
            if curr_col == "":
                self.display_error_text("Enter a column to use from the X data file.")
            else:
                self.x_data = self.x_data_all[:,curr_col]
                header_string = "COLUMN: " + headers[curr_col]
                self.filePickXColHeadLabel.config(text=header_string)
        except:
            self.display_error_text("Column must be an integer.")

    def set_y_column(self):
        self.clear_error_text()
        try:
            curr_col = int(self.filePickYColEntry.get())
            headers = analysis.import_headers(self.y_file)
            if curr_col == "":
                self.display_error_text("Enter a column to use from the Y data file.")
            else:
                self.y_data = self.y_data_all[:,curr_col]
                header_string = "COLUMN: " + headers[curr_col]
                self.filePickYColHeadLabel.config(text=header_string)
        except:
            self.display_error_text("Column must be an integer.")
    
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

# open and run application
def run_GUI():
    root = tk.Tk()
    app_title = 'Plot Test Data'
    app = Application(app_title,master=root)
    app.after(MS_DELAY, app.check_condition)
    app.mainloop()

if __name__ == "__main__":
    # N.B.: since the import of other force_tester modules is an implicit relative import when this module is run directly,
    # to run this directly without errors, you have to run as a module and with qualified name i.e.:
    # python -m force_tester.gui_plots
    # Also, run FROM THE DIRECTORY ABOVE force_tester
    # See: https://peps.python.org/pep-0338/#import-statements-and-the-main-module

    run_GUI()