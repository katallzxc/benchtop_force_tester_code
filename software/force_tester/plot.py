''' PLOT v0.0 - Katie Allison
Hatton Lab force testing platform data plotting code

Created: 2024-02-21
Updated: 2024-02-21

This code imports raw data from saved data files and turns it into (various types of) usable graphs. Also used by GUI to display analysis information.

Data inputs:
- 
Notes:
- https://jakevdp.github.io/PythonDataScienceHandbook/04.09-text-and-annotation.html
- https://matplotlib.org/stable/gallery/text_labels_and_annotations/annotation_demo.html
'''
import numpy as np
import matplotlib.pyplot as plt
import os

from force_tester import record

from force_tester.helpers import files

# set root and subfolder locations and file type constant
DATA_INPUT_PATH = files.get_path(include_analysis_folder=False)
PLOT_OUTPUT_PATH = files.get_path(include_analysis_folder=True)
PLOT_EXT = ".png"

class Plotter:
    DEFAULT_LINETYPES = ['r','g','b','k','c','m','y','r--','g--','b--','k--','c--','m--','y--','r-.','g-.']
    PLOT = 9
    PLOT_FIT = 90
    PLOT_MIN,PLOT_MAX = 91,92
    PLOT_START,PLOT_END = 93,94
    PLOT_NOTE = 95
    PLOT_MULTISERIES = 96

    PLOT_DESCRIPTORS = {
        PLOT_FIT:'fitline',
        PLOT_MIN:'minline',
        PLOT_MAX:'maxline',
        PLOT_START:'startline',
        PLOT_END:'endline',
        PLOT_NOTE:'annotated',
        PLOT_MULTISERIES:'multiseries'
    }  

    def __init__(self,fig_size=(7,5),lines=DEFAULT_LINETYPES):
        # set up plot size and line order
        self.fig,self.ax = plt.subplots(figsize=fig_size)
        self.linetypes = lines
        self.plot_path = PLOT_OUTPUT_PATH
        # reset data series index and make lists for data filenames and arrays
        self.data_series_ind = 0
        self.data_files = []
        self.data_series = []
        # reset analysis series index and make list for analysis data arrays
        self.analysis_series_ind = 0
        self.analysis_series = []
        self.analysis_descriptors = Plotter.PLOT_DESCRIPTORS
        self.analysis_entries = []
        # reset legend entry index and make list for legend entry/corresp. index/corresp. type tuples
        self.legend_ind = 0
        self.legend_entries = []

    def get_analysis_objects(self):
        self.analyzer_dict = {
            Plotter.PLOT_FIT: PlotFit(self.analysis_descriptors[Plotter.PLOT_FIT]),
            Plotter.PLOT_MIN:'minline',
            Plotter.PLOT_MAX:'maxline',
            Plotter.PLOT_START:'startline',
            Plotter.PLOT_END:'endline',
            Plotter.PLOT_NOTE:'annotated',
            Plotter.PLOT_MULTISERIES:None
        }

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
        
    def add_analysis_series(self,data_arr):
        self.analysis_series.append(data_arr)
        self.analysis_series_ind += 1

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

    def plot_analysis_series(self,data,legend,src_data_ind=None,cols=(0,1),line=None,add_new=True):
        # if this data is being plotted for the first time, add to data and legend lists
        if add_new:
            self.add_legend_entry(legend,self.analysis_series_ind,is_analysis=True)
            self.add_data_series(data)

        # split data into independent and dependent coords
        indep_data = data[:,cols[0]]
        dep_data = data[:,cols[1]]

        # plot series
        if line is None:
            line = self.get_next_linetype(src_data_ind,is_analysis=True)
        self.ax.plot(indep_data, dep_data, line, label=legend)
    
    def analyze_series(self,series_data,analysis_details):
        #series_data = (indep_data,dep_data,lin,leg)
        analysis_desc_list = analyze_plot(self.ax,series_data,analysis_details)
        return analysis_desc_list
    
    def parse_analysis_code(self,series_data,analysis_code):
        #series_data = (indep_data,dep_data,lin,leg)
        analyzer_obj = self.analyzer_dict[analysis_code]
        if analysis_code == Plotter.PLOT_FIT:
            data,legend = analyzer_obj.get_fit_plot_data(series_data)
        elif analysis_code == Plotter.PLOT_MIN:
            data,legend = analyzer_obj.get_fit_plot_data(series_data)
        elif analysis_code == Plotter.PLOT_MAX:
            data,legend = analyzer_obj.get_fit_plot_data(series_data)
        elif analysis_code == Plotter.PLOT_START:
            data,legend = analyzer_obj.get_fit_plot_data(series_data)
        elif analysis_code == Plotter.PLOT_END:
            data,legend = analyzer_obj.get_fit_plot_data(series_data)
        self.analysis_entries.append(self.analysis_descriptors[analysis_code])
        return analysis_code

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

class PlotFit:
    def __init__(self,filestring):
        self.file_str = filestring
        self.legend_str = 'line of best fit'

    def get_fit_coeffs(self,indep,dep,fit_degree):
        return np.polyfit(indep,dep,fit_degree)

    def get_fit_curve(self,indep_data,dep_data,degree=1):
        fit_coeffs = self.get_fit_coeffs(indep_data,dep_data,degree)
        if degree == 1:
            return np.poly1d(fit_coeffs)(indep_data)
        else:
            print("Plot fitting not set up for non-linear fit!")
            raise ValueError

    def get_fit_plot_data(self,indep_data,dep_data,legend_addon=""):
        fit_line = self.get_fit_curve(indep_data,dep_data)
        if legend_addon != "":
            fit_legend = '{0} ({1})'.format(self.legend_str,legend_addon)
        else:
            fit_legend = self.legend_str
        return fit_line,fit_legend

class PlotMin:
    def __init__(self,filestring):
        self.file_str = filestring
        self.legend_str = 'global minimum'

    def get_min_coords(self,indep,dep):
        local_min = np.min(dep)
        local_min_pos = indep[np.argmin(dep)]
        return (local_min_pos,local_min)

    def get_min_line(self,indep_data,dep_data):
        min_coords = self.get_min_coords(indep_data,dep_data)
        return np.poly1d([0,min_coords[1]])(indep_data)

    def get_min_indicator(self,indep_data,dep_data):
        min_coords = self.get_min_coords(indep_data,dep_data)
        arrow_pos = min_coords
        text_pos = (min_coords[0], min_coords[1] - 1)
        arrow_settings = dict(facecolor='black',shrink=0.05)
        return (arrow_pos,text_pos,arrow_settings)

    def get_min_plot_data(self,indep_data,dep_data,legend_addon=""):
        min_line = self.get_min_line(indep_data,dep_data)
        # plot_obj.annotate(note_str, xy=arrow_pos, xytext=text_pos,arrow_props=arrow_settings)
        if legend_addon != "":
            min_legend = '{0} ({1})'.format(self.legend_str,legend_addon)
        else:
            min_legend  = self.legend_str
        return min_line,min_legend

def analyze_plot(plot_obj,series_data,analysis_params):
    pass
    # def add_indicator_max(plot_obj,indep_data,dep_data,curr_linetype,legend,use_line):
    #     # get max
    #     local_max = np.max(dep_data)
    #     local_max_pos = indep_data[np.argmax(dep_data)]

    #     # plot max
    #     note_str = 'global maximum'
    #     if use_line:
    #         max_line = np.poly1d([0,local_max])(indep_data)
    #         legend_str = '{0} ({1})'.format(note_str,legend)
    #         plot_obj.plot(indep_data, max_line,curr_linetype, label=legend_str)
    #     else:
    #         arrow_settings = dict(facecolor='black',shrink=0.05)
    #         arrow_pos = (local_max_pos, local_max)
    #         text_pos = (local_max_pos, local_max + 1)
    #         plot_obj.annotate(note_str, xy=arrow_pos, xytext=text_pos,arrow_props=arrow_settings)
    #     return [0,local_max]

    # def add_indicator_start(plot_obj,indep_data,dep_data,curr_linetype,legend,use_line,start_pos):
    #     note_str = 'start'
    #     if use_line:
    #         start_line = np.poly1d([start_pos,0])(indep_data)
    #         legend_str = '{0} ({1})'.format(note_str,legend)
    #         plot_obj.plot(indep_data, start_line,curr_linetype, label=legend_str)
    #     else:
    #         start_ind = np.asarray(indep_data==start_pos).nonzero()[0][0]
    #         start_val = dep_data[start_ind]
    #         arrow_settings = dict(facecolor='black',shrink=0.05)
    #         arrow_pos = (start_pos, start_val)
    #         text_pos = (start_pos - 1, start_val)
    #         plot_obj.annotate(note_str, xy=arrow_pos, xytext=text_pos,arrow_props=arrow_settings)
    #     return [start_pos,0]

    # def add_indicator_end(plot_obj,indep_data,dep_data,curr_linetype,legend,use_line,end_pos):
    #     note_str = 'end'
    #     if use_line:
    #         end_line = np.poly1d([end_pos,0])(indep_data)
    #         legend_str = '{0} ({1})'.format(note_str,legend)
    #         plot_obj.plot(indep_data, end_line,curr_linetype, label=legend_str)
    #     else:
    #         end_ind = np.asarray(indep_data==end_pos).nonzero()[0][0]
    #         end_val = dep_data[end_ind]
    #         arrow_settings = dict(facecolor='black',shrink=0.05)
    #         arrow_pos = (end_pos, end_val)
    #         text_pos = (end_pos + 1, end_val)
    #         plot_obj.annotate(note_str, xy=arrow_pos, xytext=text_pos,arrow_props=arrow_settings)
    #     return [end_pos,0]

    # # Add annotations and analysis (e.g., line of best fit) if applicable
    # analysis_strings = []
    # if analysis_params[PLOT_FIT][0]:
    #     analysis_strings.append(PLOT_DESCRIPTORS[PLOT_FIT])
    #     add_fit_line(plot_obj,*series_data,analysis_params[PLOT_FIT][1])
    # elif analysis_params[PLOT_MIN][0]:
    #     analysis_strings.append(PLOT_DESCRIPTORS[PLOT_FIT])
    #     add_indicator_min(plot_obj,*series_data,analysis_params[PLOT_MIN][1])
    # elif analysis_params[PLOT_MAX][0]:
    #     analysis_strings.append(PLOT_DESCRIPTORS[PLOT_MAX])
    #     add_indicator_max(plot_obj,*series_data,analysis_params[PLOT_MAX][1])
    # elif analysis_params[PLOT_START][0]:
    #     analysis_strings.append(PLOT_DESCRIPTORS[PLOT_START])
    #     add_indicator_start(plot_obj,*series_data,analysis_params[PLOT_START][1],analysis_params[PLOT_START][2])
    # elif analysis_params[PLOT_END][0]:
    #     analysis_strings.append(PLOT_DESCRIPTORS[PLOT_END])
    #     add_indicator_end(plot_obj,*series_data,analysis_params[PLOT_END][1],analysis_params[PLOT_END][2])
    # return analysis_strings

def import_headers(filename1,filename2="",print_headers=True):
    def get_file_headers(filename):
        base_filename = files.get_base_filename_from_path(filename,remove_ext=False)
        file_path = os.path.join(DATA_INPUT_PATH, base_filename)
        file_headers = np.genfromtxt(file_path,delimiter=files.FILE_DELIM,dtype='str',max_rows=1)
        return file_headers
    
    # get headers for time and data from first file
    headers = get_file_headers(filename1)

    # if second file is given, combine data headers from both files (dropping time headers)
    if filename2 != "":
        headers2 = get_file_headers(filename2)
        headers = [headers[0],headers[2],headers2[2]]
        if print_headers: print("Headers are: %s"%str(headers))
    return headers

def get_plot_axis_labels(type1,type2,col1,col2,filename1,filename2="",is_scaled=True):
    # import headers from file
    header_arr = import_headers(filename1,filename2)

    # get header strings to use as axis labels
    if is_scaled:
        # if data is scaled to standard units, replace units from header strings
        unit1 = record.DATA_STANDARD_UNITS[type1]
        unit2 = record.DATA_STANDARD_UNITS[type2]
        label1 = header_arr[col1].split("[")[0] + unit1
        label2 = header_arr[col2].split("[")[0] + unit2
    else:
        label1 = header_arr[col1]
        label2 = header_arr[col2]
    return label1,label2

def get_plot_log(plot_dimensions,num_series=1,list_linetypes=Plotter.DEFAULT_LINETYPES):
    log_dict = {
        "timestamp": files.get_timestamp(),
        "num series": num_series,
        "files": [],
        "legend entries": [],
        "available linetypes": list_linetypes,
        "size": plot_dimensions,
        "data size": []
    }
    return log_dict

def get_plot_filename(type1,type2,filename1,plot_desc,plot_analysis_desc_list=[],alt_filename=""):
    def get_comparison_name_from_types(type1,type2):
        comparison_name = "{1}vs{0}".format(record.DATA_TYPE_NAMES[type1], record.DATA_TYPE_NAMES[type2])
        return comparison_name
    
    def get_plot_desc_string(comparison_string,plot_desc_string,analysis_list):
        full_plot_desc = "{0}_{1}".format(comparison_string,plot_desc_string)
        for desc_string in analysis_list:
            full_plot_desc += "_" + desc_string
        return full_plot_desc

    # get base cropped or user-provided filename
    if alt_filename != "": # use string for filename if provided by user (usually when data from multiple tests is combined)
        base_filename = alt_filename
    else: # otherwise, use the base string (test description + timestamp) from data file used to make plot
        base_filename = files.crop_data_type_from_filename(filename1)
    filename = files.get_base_filename_from_path(base_filename,remove_ext=True)

    # get plot description string
    comparison_name = get_comparison_name_from_types(type1,type2)
    full_plot_desc = get_plot_desc_string(comparison_name,plot_desc,plot_analysis_desc_list)

    # assemble filename
    ext = PLOT_EXT
    new_filename = "{0}_{1}{2}".format(filename,full_plot_desc,ext)
    return new_filename

def export_plot(plot_filename):
    filepath = os.path.join(PLOT_OUTPUT_PATH, plot_filename)
    plt.savefig(filepath)
    return True

def export_plot_log(log_dict,plot_title,axis_labels,list_analysis_actions,save_path):
    # Add plot information to dictionary
    log_dict["title"] = plot_title
    log_dict["labels"] = str(axis_labels)
    log_dict["analysis"] = str(list_analysis_actions)
    log_dict["filepath"] = save_path

    # Export log dictionary
    plot_log_df = record.format_log(log_dict)
    save_name = files.get_base_filename_from_path(save_path,True)
    record.export_outputs(plot_log_df,PLOT_OUTPUT_PATH,save_name,log_dict["timestamp"],is_log=True)
    return save_name

# def make_graph_x_vs_t(filename,plot_title,test_data,plot_desc,analysis_params,plot_size=(7,5),col_inds=(1,2),data_scaled=True,show_plt=True,filename_replacement=""):
    # Create plot object and plot log
    linetypes = Plotter.DEFAULT_LINETYPES
    fig,ax = plt.subplots(figsize=plot_size)
    plot_log_dict = get_plot_log(plot_size,linetypes)
    try:
        # Plot data, with analysis annotations and labels
        analysis_actions = plot_series(ax,test_data,col_inds,linetypes[0],'true data',analysis_params)

        # Label axes based on filenames
        data_types = (files.TIME_TYPE,files.get_data_type_from_path(filename))
        axis_labels = get_plot_axis_labels(*data_types,*col_inds,filename,is_scaled=data_scaled)
        label_plot(ax,plot_title,axis_labels)

        # Export plot and plot log
        filename = get_plot_filename(*data_types,filename,plot_desc,analysis_actions,filename_replacement)
        export_plot(filename)
        export_plot_log(plot_log_dict,plot_title,axis_labels,analysis_actions,filename)

        # Show plot
        if show_plt:plt.show()
        return plt

    except:
        print("plot failed")
        return False
    
def make_graph_x_vs_y(file1,file2,plot_title,test_data,plot_desc,plot_size=(7,5),x_col=1,y_col=2,data_scaled=True,show_plt=True,fit_line=True,min_shown=True,filename_replacement=""):
    breakpoint()
    # Set linetypes and start list of analysis actions
    linetypes = Plotter.DEFAULT_LINETYPES
    plot_analysis_actions = []

    # Create plot object and plot log
    fig,ax = plt.subplots(figsize=plot_size)
    plot_log_dict = get_plot_log(plot_size,linetypes)

    # Split up data and start list of analysis actions
    xd = test_data[:,x_col]
    yd = test_data[:,y_col]

    # Get descriptors for axis labels
    data_types = (files.get_data_type_from_path(file1),files.get_data_type_from_path(file2))
    xlabel,ylabel = get_plot_axis_labels(*data_types,x_col,y_col,file1,file2,data_scaled)
    try:
        # Plot data, with line of best fit if applicable
        ax.plot(xd, yd, 'k', label='true data')
        # if fit_line:
        #     ax.plot(xd, np.poly1d(np.polyfit(xd, yd, 1))(xd),'r--', label='line of best fit')
        #     plot_analysis_actions.append(PLOT_DESCRIPTORS[PLOT_FIT])
        # if min_shown:
        #     local_min_ind = np.argmin(yd)
        #     ax.annotate('local minimum', xy=(xd[local_min_ind], yd[local_min_ind]), xytext=(xd[local_min_ind]+1, yd[local_min_ind]),
        #      arrowprops=dict(facecolor='black', shrink=0.05),
        #      )
        #     plot_analysis_actions.append(PLOT_DESCRIPTORS[PLOT_NOTE])

        # Give the graph a title and axis labels
        ax.set_title(plot_title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend()

        # Finish and export plot and plot log
        filename = get_plot_filename(*data_types,file1,plot_desc,plot_analysis_actions,filename_replacement)
        export_plot(filename)
        export_plot_log(plot_log_dict,plot_title,(xlabel,ylabel),plot_analysis_actions,filename)

        # Show plot
        if show_plt:
            plt.show()
        return plt

    except:
        print("plot failed")
        return False
    
def make_multiseries_graph_x_vs_y(plot_title,data_series,plot_desc,plot_size=(7,5),x_col=1,y_col=2,data_scaled=True,show_plt=True,fit_line=False,min_shown=False,filename_replacement=""):
    # split up data and start list of analysis actions
    # input data_series contains list of tuples, with elements (filename1,filename2,testdata,legendtext)
    def axis_label_match(axis,last_label,curr_label):
        labels_match = True
        if last_label != "":
            if last_label != curr_label:
                labels_match = False
                warning_str = "{0} axis label mismatch!".format(axis)
                warning_str = warning_str + "Last label was {0} and current label is {1}".format(last_label,curr_label)
                print(warning_str)
        return labels_match

    # Set linetypes and start list of analysis actions
    linetypes = Plotter.DEFAULT_LINETYPES
    plot_analysis_actions = []

    # Check number of series to plot
    num_data_series = len(data_series)
    if num_data_series > 1:
        #plot_analysis_actions.append(PLOT_DESCRIPTORS[PLOT_MULTISERIES])
        plot_analysis_actions.append('multiseries')

    # Create plot object and plot log
    fig,ax = plt.subplots(figsize=plot_size)
    plot_log_dict = get_plot_log(plot_size,num_data_series,linetypes)

    # Plot each data series in turn
    last_xlabel = ""
    last_ylabel = ""
    try:
        for i in range(0,num_data_series):
            # Unpack data series tuple
            file1,file2,test_data,legend_text = data_series[i]

            # Add input information to plot log
            plot_log_dict["files"].append((file1,file2))
            plot_log_dict["legend entries"].append(legend_text)
            plot_log_dict["data size"].append(np.shape(test_data))

            # Get descriptors for axis labels
            data_types = (files.get_data_type_from_path(file1),files.get_data_type_from_path(file2))
            xlabel,ylabel = get_plot_axis_labels(*data_types,x_col,y_col,file1,file2,data_scaled)

            # Check that axis labels have not changed since last plotted series
            axis_label_match('X',last_xlabel,xlabel)
            axis_label_match('Y',last_ylabel,ylabel)
            last_xlabel,last_ylabel = xlabel,ylabel

            # Plot data
            xd = test_data[:,x_col-1]
            yd = test_data[:,y_col-1]
            ax.plot(xd, yd, linetypes[i% len(linetypes)], label=legend_text)

            # Add annotations and analysis (e.g., line of best fit) if applicable
            # if fit_line:
            #     curr_linetype = '{0}:'.format(linetypes[i])
            #     label_str = 'line of best fit ({0})'.format(legend_text)
            #     ax.plot(xd, np.poly1d(np.polyfit(xd, yd, 1))(xd),curr_linetype, label=label_str)
            #     plot_analysis_actions.append(PLOT_DESCRIPTORS[PLOT_FIT])
            # if min_shown:
            #     local_min_ind = np.argmin(yd)
            #     ax.annotate('local minimum', xy=(xd[local_min_ind], yd[local_min_ind]), xytext=(xd[local_min_ind]+1, yd[local_min_ind]),
            #     arrowprops=dict(facecolor='black', shrink=0.05),
            #     )
            #     plot_analysis_actions.append(PLOT_DESCRIPTORS[PLOT_NOTE])

        # Give the graph a title and axis labels
        ax.set_title(plot_title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend()

        # Finish and export plot and plot log
        filename = get_plot_filename(*data_types,file1,plot_desc,plot_analysis_actions,filename_replacement)
        print("entered name")
        export_plot(filename)
        print("entered export")
        export_plot_log(plot_log_dict,plot_title,(xlabel,ylabel),plot_analysis_actions,filename)

        # Show plot
        if show_plt:
            plt.show()
        return plt

    except:
        print("plot failed")
        return False
    
def command_line_plot(plot_desc_string,repeats=True,write_slope=False,curr_data=None,use_auto_plot=False,auto_plot_title=None):
    def quick_import(filename):
        filepath = files.assemble_path(filename)
        print(filepath)
        data_arr = np.loadtxt(filepath,delimiter=files.FILE_DELIM,skiprows=1)
        data_type = files.get_data_type_from_path(filename)
        return data_arr,data_type
    
    # def restore_plot_analysis_defaults():
    #     plot_analysis_settings = {
    #         # format: (is_on,use_line,value)
    #         PLOT_FIT:   (False,True,None),
    #         PLOT_MIN:   (False,True,None),
    #         PLOT_MAX:   (False,True,None),
    #         PLOT_START: (False,True,0),
    #         PLOT_END:   (False,True,0),
    #         PLOT_NOTE:  (False,None,""),
    #         PLOT_MULTISERIES:(False,None,1)
    #     }
    #     return plot_analysis_settings
    
    # def change_plot_analysis_settings(analysis_dict):
    #     for itm in analysis_dict:
    #         print(analysis_dict[itm])
    #         print(analysis_dict[itm][0])
    #         if analysis_dict[itm][0]:
    #             toggle = input("{0} analysis is currently turned on. Press T to turn off or ENTER to turn on. ".format(PLOT_DESCRIPTORS[itm]))
    #             if toggle == "t" or toggle == "T":
    #                 analysis_dict[itm][0] = False
    #         else:
    #             toggle = input("{0} analysis is currently turned off. Press T to turn on or ENTER to turn off. ".format(PLOT_DESCRIPTORS[itm]))
    #             if toggle == "t" or toggle == "T":
    #                 analysis_dict[itm][0] = True

    #     if analysis_dict[PLOT_START][0]:
    #         analysis_dict[PLOT_START][2] = input("Enter position for start line. ")
    #     if analysis_dict[PLOT_END][0]:
    #         analysis_dict[PLOT_END][2] = input("Enter position for end line. ")
    #     if analysis_dict[PLOT_NOTE][0]:
    #         analysis_dict[PLOT_NOTE][2] = input("Enter annotation. ")
    #     return analysis_dict
    
    done_plotting = False
    num_files_plotted = 0

    while not done_plotting:
        # plot_analysis_settings = restore_plot_analysis_defaults()
        if curr_data is None:
            next_file = input("Enter filename to analyze or press ENTER to finish. ")
        elif use_auto_plot:
            next_file=curr_data
            done_plotting = True
        else:
            next_file = input("Enter filename to analyze, press F to use recent data file (%s), or press ENTER to finish. "%str(curr_data))
            if next_file == "F": 
                next_file = curr_data

        if (next_file == "" or not repeats):
            done_plotting = True

        else:
            # import data and prompt for title
            print(next_file)
            next_data,data_type = quick_import(next_file)
            data_type_str = record.DATA_TYPE_NAMES[data_type]
            if (use_auto_plot and (auto_plot_title is not None)):
                plot_title = auto_plot_title
            else:
                plot_title = input("Enter a plot title to plot %s vs time data or press ENTER to skip plotting. "%data_type_str)

            if write_slope:
                print("Slope was {0} steps/s".format((10**9)*np.polyfit(next_data[:,1],next_data[:,2],1)[0]))

            # plot graph of data (vs time only, not other data arrays)
            if plot_title != "":
                try:
                    new_Plotr = Plotter()
                    new_Plotr.plot_data_series((next_file,""),next_data,"true data",(1,2),None)
                    new_Plotr.fully_label_plot(plot_title,("time",data_type_str))
                    filename = get_plot_filename(data_type,files.TIME_TYPE,next_file,plot_desc_string)
                    new_Plotr.export_plot(filename,show=True)
                    num_files_plotted += 1
                    # plot_analysis = input("Enter A to start plot analysis or press ENTER to skip. ")
                    # if plot_analysis == "a" or plot_analysis == "A":
                    #     pass
                    #     # plot_analysis_settings = change_plot_analysis_settings(plot_analysis_settings)
                except:
                    print("Plotting not successful.")
    return num_files_plotted
    
if __name__ == "__main__":
    # N.B.: since the import of other force_tester modules is an implicit relative import when this module is run directly,
    # to run this directly without errors, you have to run as a module and with qualified name i.e.:
    # python -m force_tester.plot
    # Also, run FROM THE DIRECTORY ABOVE force_tester
    # See: https://peps.python.org/pep-0338/#import-statements-and-the-main-module

    plot_desc = "plot" # should match entry for PLOT in ANALYSIS_DESCRIPTORS in analysis.py
    command_line_plot(plot_desc,write_slope=True)
