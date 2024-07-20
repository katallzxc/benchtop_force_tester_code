'''
CROP v0
automatically remove pre-test and post-test datapoints based on force data values (near zero) and rate of change

2024-06-29 17:15- I'm generally OK with how crop is going (but still need a GUI to have user confirm)
but I don't think I like having the nearzero crop after the end slope crop after all--I'd like to reverse that decision.
'''
import numpy as np
import matplotlib.pyplot as plt
import logging
import time

from force_tester.helpers import files
from force_tester.helpers import conversions

logger = logging.getLogger(__name__)
logging.basicConfig(filename='crop_output.log', level=logging.INFO)
 
def Z_test(data_array,threshold=5):
    # Get median and standard deviation
    median = np.median(data_array)
    stddev = np.std(data_array)
    # logger.info("Data mean is {0}, median is {1}, and stddev is {2}.".format(np.mean(data_array),median,stddev))
    
    # Compute Z scores for all data and select outliers above threshold for Z
    Z = abs(data_array - median)/stddev
    outlier_inds = np.where(Z > threshold)[0]
    # logger.info("Outliers detected at {0} with Z scores of {1}".format(outlier_inds,Z[outlier_inds]))
    return np.asarray(outlier_inds,dtype='int')

def get_quartiles(data):
    ordered_data = np.sort(data)
    num_ordered_pts = len(ordered_data)
    quartile1 = ordered_data[int((25/100)*num_ordered_pts)]
    quartile3 = ordered_data[int((75/100)*num_ordered_pts)]
    return quartile1,quartile3

def nonzero_IQR_test(data,factors=(5,3),min_iqr=0.05,min_t3=0.01,exclude_zero_in_quartiles=True):
    # order data and get quartiles
    if exclude_zero_in_quartiles:
        unordered_nonzero_data = data[data != 0]
    else:
        unordered_nonzero_data = data
    q1,q3 = get_quartiles(unordered_nonzero_data)
    iqr = max(q3 - q1, min_iqr)
    # logger.info("Q1 is {0}, Q3 is {1}, and minimum IQR is {2}, so IQR is {3}".format(q1,q3,min_iqr,iqr))
    
    # define IQR rule thresholds
    t1 = q1 - factors[0]*iqr
    t3 = max(q3 + factors[1]*iqr,min_t3)
    # logger.info("With factors of {0} and {1}, thresholds are {2} and {3}".format(factors[0],factors[1],t1,t3))
    
    # pull outliers with IQR rule
    q1_outliers = np.where(data < t1)[0]
    q3_outliers = np.where(data > t3)[0]
    # logger.info("Based on IQR, outliers are {0} and {1}".format(data[q1_outliers],data[q3_outliers]))
    
    outlier_inds = []
    for ind in q1_outliers: outlier_inds.append(ind)
    for ind in q3_outliers: outlier_inds.append(ind)
    return np.asarray(outlier_inds,dtype='int')

def spike_test(data):
    pass

def detect_outliers(use_value_based_methods,test_data,col_to_check=2):
    # Pull relevant data col and initialize outlier index array
    data = test_data[:,col_to_check]
    # outlier_indices = []

    if use_value_based_methods:
        Z_rule_outliers = Z_test(data)
        # for ind in Z_rule_outliers:
        #     outlier_indices.append(ind)
        IQR_rule_outliers = nonzero_IQR_test(data)
        # for ind in IQR_rule_outliers:
        #    outlier_indices.append(ind)
    else:
        spike_outliers = mark_outliers(data)
        # for ind in spike_outliers:
        #     outlier_indices.append(ind)
    return Z_rule_outliers,IQR_rule_outliers #outlier_indices

def mark_outliers(data,data_col=2,num_avging_pts=3,proportional_threshold=0.1):
    outlier_indices = []
    data_spread = np.max(data[:,data_col]) - np.min(data[:,data_col])
    data_change_threshold = abs(data_spread*proportional_threshold)
    logger.info("Data spread is {0} and threshold for value change to signify event is {1}".format(data_spread,data_change_threshold))

    # original ROC-based approach
    # for i in range(num_avging_pts-1,len(data)):
    #     pre_avg = np.average(data[i-num_avging_pts+1:i,data_col])
    #     post_avg = np.average(data[i+1:i+num_avging_pts,data_col])

    #     delta = data[i,data_col]-data[i-1,data_col]
    #     if abs(delta) > data_change_threshold:
    #         print("Large data change found at index {0} with delta {1} more than threshold value {2}.".format(i,delta,data_change_threshold))
            
    #         if abs(post_avg-pre_avg) < data_change_threshold:
    #             print("Outlier detected: from avg of {0} to value of {1} to avg of {2}".format(pre_avg,data[i,data_col],post_avg))
    #             outlier_ind = i
    #             outlier_indices.append(outlier_ind)
    #         else:
    #             print("No outlier: from avg of {0} to value of {1} to avg of {2}".format(pre_avg,data[i,data_col],post_avg))
    return outlier_indices

def remove_outliers(original_data,outlier_data):
    #TODO: make capable of taking 2D inputs
    # initialize bool array
    num_original_pts = len(original_data)
    retained_indices = np.ones((num_original_pts,), dtype=bool)

    # mark points to remove as false in bool array
    for outlier_type in outlier_data:
        outlier_locations = outlier_data[outlier_type][1]
        if len(outlier_locations) > 0: 
            retained_indices[outlier_locations] = False

    # remove marked outlier points and return
    retained_data = original_data[retained_indices,:]
    num_retained_pts = len(retained_data)
    return retained_data, (num_original_pts,num_retained_pts)

def return_moving_avg(all_data,data_col=2,window_len=10):
    data = all_data[:,data_col]
    running_avg = np.hstack((all_data[:,0:data_col],np.zeros((len(all_data),1))))
    first_ind,last_ind = (window_len - 1, len(data))
    for i in range(first_ind,last_ind):
        # compute local running average
        window_data = data[i-window_len+1:i]
        running_avg[i,data_col] = np.average(window_data)
    return running_avg[first_ind:,:]

def return_rate(all_data,data_col=2,pts_to_use=2):
    data = all_data[:,data_col]
    rate_data = np.hstack((all_data[:,0:data_col],np.zeros((len(all_data),1))))
    first_ind,last_ind = (pts_to_use - 1, len(data))
    for i in range(first_ind,last_ind):
        # compute local rate of change
        rate_data[i,data_col] = (data[i] - data[i-pts_to_use+1]) /pts_to_use
    return rate_data[first_ind:,:]

def detect_end_slope(rate_data,rate_thresholds,index_shift):
    slope_threshold,flat_threshold = rate_thresholds
    # find last point in rate data that is above rate threshold
    spike_point_inds = np.flatnonzero(rate_data > slope_threshold)
    if len(spike_point_inds) > 0:
        slope_end = spike_point_inds[-1]
        non_consecutive_spike_points = np.flatnonzero(np.diff(spike_point_inds)>1)
        if len(non_consecutive_spike_points) > 0:
            first_non_consecutive_ind = non_consecutive_spike_points[-1]
            slope_start_ind = spike_point_inds[first_non_consecutive_ind + 1]
        else:
            # breakpoint()
            slope_start_ind = spike_point_inds[0]
        
        # flat_rate = np.flatnonzero(abs(rate_data[:slope_end]) < flat_threshold)
        # if len(flat_rate) > 0:
        #     print("Guess with consecutive bump pts is {0}, guess with close to 0 is {1}".format(slope_start_ind,flat_rate[-1]))
            # breakpoint()
            # slope_start_ind = flat_rate[-1] - index_shift
        return slope_start_ind
    else:
        print("Rate of change does not surpass threshold of {0} at any point".format(slope_threshold))
        return 0
    
def check_end_slope(data,end_slope_candidate):
    rng = len(data) - end_slope_candidate
    post_avg = np.average(data[end_slope_candidate:,2])
    pre_start = max(0,end_slope_candidate - rng)
    pre_avg = np.average(data[pre_start:end_slope_candidate,2])
    # if post_avg > pre_avg:
    #     print("TRUE")
    if post_avg <= pre_avg:
        print(":(")
        print("Pre is {0}, post is {1} (RANGE: {2})".format(pre_avg,post_avg,rng))

def detect_crop_points(all_data,data_col=2,window_len=10,threshold_factor=0.1,min_pos=0):
    # set threshold for data delta based on data spread and threshold factor
    data = all_data[min_pos:,data_col]
    q1,q3 = get_quartiles(data)
    iqr = q3 - q1
    data_spread = np.max(data) - np.min(data)
    # data_change_threshold = abs(data_spread*threshold_factor)
    # logger.info("Data spread is {0} and threshold delta for event is {1}".format(data_spread,data_change_threshold))
    data_change_threshold = abs(iqr*threshold_factor)
    logger.info("IQR is {0} and threshold delta for event is {1}".format(iqr,data_change_threshold))

    # initialize lists for event indices and crop point indices
    event_found = False
    event_indices = []
    crop_indices = []

    # slide window across data from left to right and check for events (large deltas) with different prior and posterior running averages
    first_ind = max(min_pos,window_len-1)
    last_ind = len(data)
    for i in range(first_ind,last_ind):
        # compute local running average
        window_data = data[i-window_len+1:i]
        running_avg = np.average(window_data)

        # if not already in detected event range, check local delta against event threshold
        if not event_found:
            delta = data[i] - data[i-2]
            if abs(delta) > data_change_threshold:
                #breakpoint()
                logger.info("Index {0}: delta {1} > event threshold {2}. Current running avg is {3}".format(i,delta,data_change_threshold,running_avg))
                event_found = True
                prior_avg = running_avg
                event_ind = i
                event_end_ind = (i + window_len - 1)
                event_indices.append(event_ind + min_pos)

        # if in detected event range and at end of posterior window,
        # check if prior and posterior running averages differ enough to ID a crop point
        elif event_found:
            if i > event_end_ind:
                posterior_avg = running_avg
                change_in_avg = abs(posterior_avg - prior_avg)
                if change_in_avg > data_change_threshold:
                    logger.info("Crop point found! Avg was {0} at index {1} and is {2} at index {3}".format(prior_avg,event_ind,posterior_avg,i))
                    crop_indices.append(event_ind + min_pos)
                else:
                    logger.info("Condition not met: post-event average {0} has delta of {1}".format(posterior_avg,change_in_avg))
                event_found = False
    return crop_indices,event_indices

def crop_data_between_inds(original_data,crop_inds):
    num_crop_inds = len(crop_inds)
    if num_crop_inds >= 2:
        left_ind = crop_inds[0]
        right_ind = crop_inds[-1]
        cropped_data = original_data[left_ind:right_ind,:]
        return cropped_data
    else:
        logger.warning("Only {0} crop indices provided: {1}! Cannot crop between indices.".format(num_crop_inds,crop_inds))
        return original_data

def crop_fake_data(data,time_col=1):
    crop_indices = []

    breakpoint()
    # crop any fake data (data where all columns, including time, are 0)
    near_zero_time_inds = np.asarray(abs(data[:,time_col])<=1e-9).nonzero()[0]
    if len(near_zero_time_inds) > 0:
        crop_indices.append(near_zero_time_inds[0])
        cropped_data = data[:near_zero_time_inds[0],:]
    else:
        cropped_data = data
    return cropped_data, crop_indices

def get_nearzero_length(data,count_threshold=5,value_threshold=0.02):
    # initialize nonzero length and check threshold on initial near-zero points
    length_nearzero_region = 0
    start_threshold = data[0:count_threshold]
    threshold_met = np.all(abs(start_threshold) <= value_threshold)

    # if enough near-zero points are present in a row, get the total length
    if threshold_met:
        far_from_zero = np.flatnonzero(abs(data) > value_threshold)
        if len(far_from_zero) > 0:
            length_nearzero_region = far_from_zero[0]
    return length_nearzero_region

def crop_nearzero_data(all_data,nonzero_lengths=None):
    if nonzero_lengths == None:
        cropped_data = all_data
    else:
        starting_length,ending_length = nonzero_lengths
        cropped_data = all_data[starting_length:ending_length+1,:]
    return cropped_data

def crop_nearzero_plot(test_data,crop_inds=None,save_plt=True,show_plot=True,ttl="",plot_size=(12,6),x_col=1,y_col=2):
    fig,axes = plt.subplots(2,1,figsize=plot_size)

    # Get raw data (with converted units)
    yd = test_data[:,y_col]
    xd = test_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]

    # Plot raw data with crop points marked
    ax = axes[0]
    ax.plot(xd, yd, 'k', label='raw data')
    ax.vlines(xd[crop_inds],np.min(yd),np.max(yd),'r',':',label="near-zero region crop pos")
    ax.legend()
    ax.set_title(ttl)

    # Get cropped data
    cropped_data = crop_nearzero_data(test_data,tuple(crop_inds))
    yc = cropped_data[:,y_col]
    xc = cropped_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]

    # Plot cropped data
    ax = axes[1]
    ax.plot(xc, yc, 'k', label='cropped data')
    ax.legend()
            
    if save_plt:
        plt.tight_layout()
        plot_save_name = files.get_generic_filename(ttl,True,"CropOutlierTesting",".png")
        plt.savefig(plot_save_name)
        print("Saved as %s"%plot_save_name)
    if show_plot and (len(yc)!=len(yd)):
        plt.show()
    plt.close()

def test_crop_nearzero(ignore_list):
    def quick_import(filename):
        filepath = files.assemble_path(filename)
        data_arr = np.loadtxt(filepath,delimiter=files.FILE_DELIM,skiprows=1)
        return data_arr
    
    # plot moving avg for each force data file not in ignore list
    num_plotted = 0
    test_file_list = files.get_file_list_from_path("force")
    num_files_to_try = len(test_file_list)

    for test_file_ind in range(0, num_files_to_try):
        test_file = test_file_list[test_file_ind]
        if test_file in ignore_list:
            print("%s skipped (identified as noisy)"%test_file)
        else:
            # get start and end crop data
            test_data = quick_import(filename=test_file)
            fwd_data = test_data[:,2]
            start_crop_ind = get_nearzero_length(fwd_data)
            bwd_data = np.flip(fwd_data)
            end_crop_ind = len(bwd_data) - (get_nearzero_length(bwd_data) + 1)
            
            # Plot data as raw data, data without outliers, and cropped data
            data_title = files.get_base_filename_from_path(test_file,remove_ext=True)
            data_title = "NearZeroCrop" + data_title
            crop_nearzero_plot(test_data,[start_crop_ind,end_crop_ind],show_plot=True,save_plt=True,ttl=data_title)
            num_plotted += 1

def moving_avg_plot(test_data,running_avg_dict=None,save_plt=True,show_plot=True,ttl="",plot_size=(12,6),x_col=1,y_col=2):
    fig,ax = plt.subplots(figsize=plot_size)
    
    # Plot raw data with pre-outlier crop points marked
    yd = test_data[:,y_col]
    xd = test_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
    ax.plot(xd, yd, 'k', label='raw data')

    # Add indicators for events if given
    if not running_avg_dict is None:
        for avg_set in running_avg_dict:
            avg_data = running_avg_dict[avg_set][1]
            ya = avg_data[:,y_col]
            xa = avg_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
            ax.plot(xa, ya, color=running_avg_dict[avg_set][0],linestyle='--', label='running average (w={0})'.format(avg_set))

    ax.legend()
    ax.set_title(ttl)
            
    if save_plt:
        plt.tight_layout()
        plot_save_name = files.get_generic_filename(ttl,True,"CropOutlierTesting",".png")
        plt.savefig(plot_save_name)
        print("Saved as %s"%plot_save_name)
    if show_plot: 
        plt.show()
    plt.close()

def test_moving_avg(ignore_list):
    def quick_import(filename):
        filepath = files.assemble_path(filename)
        data_arr = np.loadtxt(filepath,delimiter=files.FILE_DELIM,skiprows=1)
        return data_arr
    
    # plot moving avg for each force data file not in ignore list
    num_plotted = 0
    test_file_list = files.get_file_list_from_path("force")
    num_files_to_try = len(test_file_list)

    for test_file_ind in range(0, num_files_to_try):
        test_file = test_file_list[test_file_ind]
        if test_file in ignore_list:
            print("%s skipped (identified as noisy)"%test_file)
        else:
            window_sizes = [10,20,50]
            line_colours = ['r','g','b','k','c','m','y']
            avg_dict = {}
            avg_round = -1

            # get running avg data
            test_data = quick_import(filename=test_file)
            for wsize in window_sizes:
                avg_round += 1
                avg_data = return_moving_avg(test_data,2,wsize)
                avg_dict[wsize] = (line_colours[avg_round],avg_data)
            
            # Plot data as raw data, data without outliers, and cropped data
            data_title = files.get_base_filename_from_path(test_file,remove_ext=True)
            data_title = "RunningAvg" + data_title
            moving_avg_plot(test_data,avg_dict,show_plot=False,save_plt=True,ttl=data_title)
            num_plotted += 1

def RoC_plot(test_data,rate_dict=None,save_plt=True,show_plot=True,ttl="",plot_size=(12,6),x_col=1,y_col=2):
    fig,axes = plt.subplots(2,1,figsize=plot_size)
    
    # Plot raw data with pre-outlier crop points marked
    ax = axes[0]
    if type(test_data) is tuple:
        yd = test_data[0][:,y_col]
        xd = test_data[0][:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
        ax.plot(xd, yd, 'k', label='raw data')
        ys = test_data[1][:,y_col]
        xs = test_data[1][:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
        ax.plot(xs, ys, 'm', label='smoothed data')

    else:
        yd = test_data[:,y_col]
        xd = test_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
        ax.plot(xd, yd, 'k', label='raw data')

    ax.legend()
    ax.set_title(ttl)

    # Plot rate of change
    ax = axes[1]
    if not rate_dict is None:
        for rate_set in rate_dict:
            rate_data = rate_dict[rate_set][1]
            ya = rate_data[:,y_col]
            xa = rate_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
            ax.plot(xa, ya, color=rate_dict[rate_set][0],label='rate (across {0} pts)'.format(rate_set))
            end_slope_crop_ind = rate_dict[rate_set][2]
            ax.vlines(xa[end_slope_crop_ind],np.min(ya),np.max(ya),rate_dict[rate_set][0],':',label="end slope crop pos (across {0} pos)".format(rate_set))
            
    RoC_threshold = 0.005
    ax.hlines(RoC_threshold,0,np.max(xa),'y',':',label="Slope threshold val={0}".format(RoC_threshold))

    ax.legend()
            
    if save_plt:
        plt.tight_layout()
        plot_save_name = files.get_generic_filename(ttl,True,"CropOutlierTesting",".png")
        plt.savefig(plot_save_name)
        print("Saved as %s"%plot_save_name)
    if show_plot: 
        plt.show()
    plt.close()

def test_RoC(ignore_list):
    def quick_import(filename):
        filepath = files.assemble_path(filename)
        data_arr = np.loadtxt(filepath,delimiter=files.FILE_DELIM,skiprows=1)
        return data_arr
    
    # plot moving avg for each force data file not in ignore list
    num_plotted = 0
    test_file_list = files.get_file_list_from_path("force")
    num_files_to_try = len(test_file_list)

    for test_file_ind in range(0, num_files_to_try):
        test_file = test_file_list[test_file_ind]
        if test_file in ignore_list:
            print("%s skipped (identified as noisy)"%test_file)
        else:
            average_sample_pt_sep = [3,5,10,15]
            line_colours = ['r','g','b','c','m','y','k']
            rate_dict = {}
            rate_round = -1

            # get running avg data
            test_data = quick_import(filename=test_file)
            for sep in average_sample_pt_sep:
                rate_round += 1
                rate_data = return_rate(test_data,2,sep)
                rate_dict[sep] = (line_colours[rate_round],rate_data)
            
            # Plot data as raw data, data without outliers, and cropped data
            data_title = files.get_base_filename_from_path(test_file,remove_ext=True)
            data_title = "RateofChange_" + data_title
            RoC_plot(test_data,rate_dict,show_plot=False,save_plt=True,ttl=data_title)
            num_plotted += 1

def test_RoC_after_smoothing(ignore_list):
    def quick_import(filename):
        filepath = files.assemble_path(filename)
        data_arr = np.loadtxt(filepath,delimiter=files.FILE_DELIM,skiprows=1)
        return data_arr
    
    # plot moving avg for each force data file not in ignore list
    num_plotted = 0
    test_file_list = files.get_file_list_from_path("force")
    num_files_to_try = len(test_file_list)

    for test_file_ind in range(0, num_files_to_try):
        test_file = test_file_list[test_file_ind]
        if test_file in ignore_list:
            print("%s skipped (identified as noisy)"%test_file)
        else:
            average_sample_pt_sep = [10,15]
            moving_average_smoothing_range = 4
            line_colours = ['r','g','b','c','m','y','k']
            rate_dict = {}
            rate_round = -1

            # get running avg data
            test_data = quick_import(filename=test_file)
            for sep in average_sample_pt_sep:
                rate_round += 1
                smoothed_data = return_moving_avg(test_data,2,moving_average_smoothing_range)
                rate_data = return_rate(smoothed_data,2,sep)
                rate_dict[sep] = (line_colours[rate_round],rate_data)
            
            # Plot data as raw data, data without outliers, and cropped data
            data_title = files.get_base_filename_from_path(test_file,remove_ext=True)
            data_title = "RateofChangePostSmoothing_" + data_title
            RoC_plot((test_data,smoothed_data),rate_dict,show_plot=False,save_plt=True,ttl=data_title)
            num_plotted += 1

def end_RoC_crop_after_smoothing(ignore_list):
    def quick_import(filename):
        filepath = files.assemble_path(filename)
        data_arr = np.loadtxt(filepath,delimiter=files.FILE_DELIM,skiprows=1)
        return data_arr
    
    # plot moving avg for each force data file not in ignore list
    num_plotted = 0
    test_file_list = files.get_file_list_from_path("force")
    num_files_to_try = len(test_file_list)

    for test_file_ind in range(0, num_files_to_try):
        test_file = test_file_list[test_file_ind]
        if test_file in ignore_list:
            print("%s skipped (identified as noisy)"%test_file)
        else:
            average_sample_pt_sep = [10,15]
            moving_average_smoothing_range = 4
            line_colours = ['r','g','b','c','m','y','k']
            rate_dict = {}
            rate_round = -1

            # get running avg data
            test_data = quick_import(filename=test_file)
            for sep in average_sample_pt_sep:
                rate_round += 1

                # smooth data and compute rate of change (across separation sep)
                smoothed_data = return_moving_avg(test_data,2,moving_average_smoothing_range)
                rate_data = return_rate(smoothed_data,2,sep)

                # select end crop point
                slope_thresholds = (0.005,0.001)
                end_slope_ind = detect_end_slope(rate_data[:,-1],slope_thresholds,sep)
                rate_dict[sep] = (line_colours[rate_round],rate_data,end_slope_ind)
            
            # Plot data as raw data, data without outliers, and cropped data
            data_title = files.get_base_filename_from_path(test_file,remove_ext=True)
            data_title = "EndCrop_RateofChangePostSmoothing_" + data_title
            RoC_plot((test_data,smoothed_data),rate_dict,show_plot=False,save_plt=True,ttl=data_title)
            num_plotted += 1

def simple_plot(test_data,initial_crop_dict=None,outlier_dict=None,final_crop_dict=None,show_plt=True,save_plt=True,ttl="",plot_size=(12,6),x_col=1,y_col=2):
    num_subplot_rows = 2
    num_subplot_cols = 2
    fig,axes = plt.subplots(num_subplot_rows,num_subplot_cols,figsize=plot_size)
    
    # Plot raw data with outliers marked
    ax = axes[0,0]
    yd = test_data[:,y_col]
    if x_col is None:
        xd = None
        ax.plot(yd, 'k', label='raw data')
    else:
        xd = test_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
        ax.plot(xd, yd, 'k', label='raw data')

    # Add indicators for outliers
    if len(outlier_dict) > 0:
        for outlier_type in outlier_dict:
            # pull outlier data from dict
            outlier_marker = outlier_dict[outlier_type][0]
            outlier_inds = outlier_dict[outlier_type][1]
            num_outliers = len(outlier_inds)

            # scatter plot outlier points
            ax.scatter(xd[outlier_inds],yd[outlier_inds],marker=outlier_marker, label="{0} rule outliers ({1})".format(outlier_type,num_outliers))
    
    ax.legend()
    # ax.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
    ax.set_title("Raw data with outlier candidates marked")

    ###################################################################
    # Plot data with near-zero data cropped and rate-based crop positions indicated
    ax = axes[0,1]

    # remove outliers from data and plot
    retained_data = remove_outliers(test_data,outlier_dict)[0]
    yo = retained_data[:,y_col]
    if x_col is None:
        ax.plot(yo, 'k', label='clean data')
    else:
        xo = retained_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
        ax.plot(xo,yo, 'k', label='clean data')

    # Add indicators for rate-based crop positions
    if len(final_crop_dict) > 0:
        for crop_attempt in final_crop_dict:
            # pull crop data from dict
            crop_colour = final_crop_dict[crop_attempt][0]
            crop_inds = final_crop_dict[crop_attempt][1]
            num_crop_pos = len(crop_inds)
            # breakpoint()

            # plot lines at crop positions
            ymin,ymax=np.min(yo),np.max(yo)
            ax.vlines(xo[crop_inds],ymin,ymax,crop_colour,'--',label="end slope crop at {0}".format(crop_inds))
    
    # q1,q3 = get_quartiles(crop_data[:,y_col])
    # iqr = np.round(q3 - q1,3)
    # ax.hlines(-iqr,0,np.max(xc),'m',':',label="IQR={0}".format(iqr))

    # start_threshold = 0.1
    # ax.vlines(start_threshold,ymin,ymax,'y',':',label="min={0}".format(start_threshold))
    
    limits = ax.get_xlim()
    ax.legend()
    # ax.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
    ax.set_title("Data with outliers removed, with end slope crop position marked")

    ###################################################################
    # Plot data with outliers removed and near-zero crop points indicated
    ax = axes[1,0]

    # pull crop data from dict
    for crop_attempt in final_crop_dict:
        crop_data = final_crop_dict[crop_attempt][2]

        # plot cropped data
        yc = crop_data[:,y_col]
        if x_col is None:
            ax.plot(yc, label='data with end slope cropped')
        else:
            xc = crop_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
            ax.plot(xc,yc, 'k',label='data with end slope cropped')

    # Add indicators for near-zero crop positions
    for crop_attempt in initial_crop_dict:
        near_zero_crop_colour = initial_crop_dict[crop_attempt][0]
        near_zero_crop_inds = initial_crop_dict[crop_attempt][1]
        ax.vlines(xd[near_zero_crop_inds],np.min(yo),np.max(yo),near_zero_crop_colour,':',label="near-zero crop pos with threshold {0}".format(crop_attempt))

    ax.legend()
    ax.set_title("After end slope cropping, with near-zero crop points marked")

    # ###################################################################
    # # Plot data with near-zero data cropped and rate-based crop positions indicated
    # ax = axes[1,0]

    # # pull crop data from dict
    # for crop_attempt in initial_crop_dict:
    #     crop_data = initial_crop_dict[crop_attempt][2]

    #     # plot cropped data
    #     yc = crop_data[:,y_col]
    #     if x_col is None:
    #         ax.plot(yc, label='initial crop')
    #     else:
    #         xc = crop_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
    #         ax.plot(xc,yc, 'k',label='initial crop')

    # # Add indicators for rate-based crop positions
    # if len(final_crop_dict) > 0:
    #     for crop_attempt in final_crop_dict:
    #         # pull crop data from dict
    #         crop_colour = final_crop_dict[crop_attempt][0]
    #         crop_inds = final_crop_dict[crop_attempt][1]
    #         num_crop_pos = len(crop_inds)

    #         # plot lines at crop positions
    #         ymin,ymax=np.min(yc),np.max(yc)
    #         ax.vlines(xc[crop_inds],ymin,ymax,crop_colour,'--',label="end slope crop".format(crop_attempt,num_crop_pos))
    
    # # q1,q3 = get_quartiles(crop_data[:,y_col])
    # # iqr = np.round(q3 - q1,3)
    # # ax.hlines(-iqr,0,np.max(xc),'m',':',label="IQR={0}".format(iqr))

    # # start_threshold = 0.1
    # # ax.vlines(start_threshold,ymin,ymax,'y',':',label="min={0}".format(start_threshold))
    
    # limits = ax.get_xlim()
    # ax.legend()
    # # ax.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
    # ax.set_title("After near-zero cropping, with end slope (rate-based) crop pos")

    # ###################################################################
    # Plot data with outliers removed and crop applied 
    ax = axes[1,1]
    y_shift = 0
    # breakpoint()
    if len(initial_crop_dict) > 0:
        for crop_attempt in initial_crop_dict:
            # pull crop data from dict
            crop_data = initial_crop_dict[crop_attempt][2]
            num_cropped = initial_crop_dict[crop_attempt][3]
            if num_cropped > 0:
                # use hacky vertical shift to make it easier to see different crop data
                yc = crop_data[:,y_col]
                yc -= y_shift
                y_shift += abs(np.max(yc) - np.min(yc))

                # plot lines at crop positions
                # plt_label = 'crop,w={0},rmv {1}'.format(crop_attempt,num_cropped)
                plt_label = 'Data with near-zero edges cropped'
                if x_col is None:
                    ax.plot(yc, label=plt_label)
                else:
                    xc = crop_data[:,x_col]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
                    ax.plot(xc,yc, label=plt_label)

    ax.set_xlim(limits)  
    ax.legend()
    ax.set_title("Post crop data")

    ###################################################################
    fig.suptitle(ttl)
    if save_plt:
        plt.tight_layout()
        plot_save_name = files.get_generic_filename(ttl,True,"CropOutlierTesting",".png")
        plt.savefig(plot_save_name)
        # print("Saved as %s"%plot_save_name)
        if show_plt: plt.show()
        plt.close()
    else:
        plt.close()

def active_crop_control(original_file,original_data,end_crop_data,outlier_data,nearzero_crop_data,plot_title):
    simple_plot(test_data=original_data,initial_crop_dict=end_crop_data,outlier_dict=outlier_data,final_crop_dict=nearzero_crop_data,ttl=plot_title)

def test_crop(ignore_list,mark_all_events=True):
    def quick_import(filename):
        filepath = files.assemble_path(filename)
        data_arr = np.loadtxt(filepath,delimiter=files.FILE_DELIM,skiprows=1)
        return data_arr
    
    # set crop variables
    # window_sizes = [5,10,20,50]
    threshold_proportion = 0.5
    min_crop_start_time = 0.1
    average_sample_pt_sep = 10
    moving_average_smoothing_range = 4
    crop_points_found,num_plotted = 0,0
    
    # get list of force data files
    test_file_list = files.get_file_list_from_path("force")
    num_files_to_try = len(test_file_list)

    # start log
    logger.info(":"*150)
    # logger.info("::::::::::::::::::::TESTING IQR-BASED CROP on {0} files at {1} with {2} pts in moving average and threshold proportion = {3} of IQR:::::::::::::::::".format(
        # num_files_to_try,time.strftime("%Y-%m-%d %H:%M", time.gmtime()),window_sizes,threshold_proportion))
    logger.info("::::::::::::::::::::TESTING END SLOPE CROP on {0} files at {1} with {2} pt spread in rate calc:::::::::::::::::".format(
        num_files_to_try,time.strftime("%Y-%m-%d %H:%M", time.gmtime()),average_sample_pt_sep))

    # test crop and outlier code on each data file
    for test_file_ind in range(0, num_files_to_try):
        logger.info("="*70)

        # get filename and check if in ignore list
        test_file = test_file_list[test_file_ind]
        if test_file in ignore_list:
            logger.info("%s skipped (identified as noisy)"%test_file)
            print("%s skipped (identified as noisy)"%test_file)

        else:
            # Initialize variables and import data
            print("{0}/{1}: {2}".format(test_file_ind+1,num_files_to_try,test_file))
            # breakpoint()
            logger.info("File {0}/{1}: {2}".format(test_file_ind+1,num_files_to_try,test_file))
            test_data = quick_import(filename=test_file)
            time_in_seconds = test_data[:,1]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
            min_start_crop_pos = np.flatnonzero(time_in_seconds > min_crop_start_time)[0]

            # Get outliers and add to dictionary
            outlier_Z_pos,outlier_IQR_pos = detect_outliers(True,test_data)
            total_outlier_count = len(outlier_Z_pos) + len(outlier_IQR_pos)
            outlier_data = {"Z": ("x",outlier_Z_pos), "IQR": (".",outlier_IQR_pos)}
            pre_crop_retained_data = remove_outliers(test_data,outlier_data)[0]
            
            # Initialize crop tracking variables
            crop_round = -1
            initial_crop_data = {}
            final_crop_data = {}
            line_colours = ['r','g','b','c','y','k','m']
            #TODO: fix, hacky

            # Get rate-based crop positions and add to dictionary
            multiple_pts_found = False

            # smooth data and compute rate of change (across separation sep)
            smoothed_data = return_moving_avg(pre_crop_retained_data,2,moving_average_smoothing_range)
            rate_data = return_rate(smoothed_data,2,average_sample_pt_sep)

            # select end crop point
            slope_thresholds = (0.005,0.001)
            end_slope_crop_ind = detect_end_slope(rate_data[:,-1],slope_thresholds,average_sample_pt_sep)
            check_end_slope(pre_crop_retained_data,end_slope_crop_ind)
            logger.info("Crop position is {0} with {1} outliers.".format(end_slope_crop_ind, total_outlier_count))
            if end_slope_crop_ind > 0: 
                multiple_pts_found = True
                crop_points_found += 1

            # crop data
            crop_round += 1
            cropped_data = pre_crop_retained_data[0:end_slope_crop_ind]
            num_pts_removed = len(pre_crop_retained_data) - len(cropped_data)
            final_crop_data[average_sample_pt_sep] = (line_colours[crop_round],[end_slope_crop_ind],cropped_data,num_pts_removed)

            # Get value-based crop positions
            initial_crop_threshold = 0.02
            fwd_data = cropped_data[:,2]
            start_crop_ind = get_nearzero_length(fwd_data,value_threshold=initial_crop_threshold)
            bwd_data = np.flip(fwd_data)
            end_crop_ind = len(bwd_data) - (get_nearzero_length(bwd_data) + 1)
            nearzero_cropped_data = crop_nearzero_data(cropped_data,(start_crop_ind,end_crop_ind))
            num_pts_removed = len(cropped_data) - len(nearzero_cropped_data)
            crop_round += 1
            initial_crop_data[initial_crop_threshold] = (line_colours[crop_round],[start_crop_ind,end_crop_ind],nearzero_cropped_data,num_pts_removed)
            
            # for wsize in window_sizes:
            #     # Get crop points
            #     crop_pos,event_pos = detect_crop_points(nearzero_cropped_data,data_col=2,window_len=wsize,threshold_factor=threshold_proportion,min_pos=min_start_crop_pos)
            #     logger.info("Crop positions are {0} with {1} outliers.".format(crop_pos, total_outlier_count))
            #     crop_points_found += len(crop_pos)
            #     if len(crop_pos) > 1: multiple_pts_found = True

            #     # Crop data
            #     cropped_data = crop_data_between_inds(nearzero_cropped_data,crop_pos)
            #     crop_round += 1
            #     num_pts_removed = len(nearzero_cropped_data) - len(cropped_data)
            #     final_crop_data[wsize] = (line_colours[crop_round],crop_pos,cropped_data,num_pts_removed)
            
            # Plot data as raw data, data without outliers, and cropped data
            data_title = files.get_base_filename_from_path(test_file,remove_ext=True)
            # nearzero_left_crop = pre_crop_retained_data[start_crop_ind,1]*conversions.UNIT_SCALES[conversions.TIME_TYPE]
            # print(nearzero_left_crop)
            # if multiple_pts_found and nearzero_left_crop < 0.1:
            simple_plot(test_data,initial_crop_data,outlier_data,final_crop_data,show_plt=False,save_plt=True,ttl=data_title)
            num_plotted += 1
    logger.info("{0} CROP POINTS FOUND IN {1} FILES! :::::::::::::::::::::::::::::".format(crop_points_found,num_plotted))
    # print("{0} of {1} had multiple crop points".format(num_plotted,num_files_to_try-len(ignore_list)))

if __name__ == "__main__":
    # N.B.: since the import of other force_tester modules is an implicit relative import when this module is run directly,
    # to run this directly without errors, you have to run as a module and with qualified name i.e.:
    # python -m force_tester.helpers.crop
    # Also, run FROM THE DIRECTORY ABOVE force_tester
    # See: https://peps.python.org/pep-0338/#import-statements-and-the-main-module
    files_to_skip = ["shearAcryliconAcrylic_20240301_1610_force.csv","shearAcryliconAcrylic_20240301_1613_force.csv",
                    "shearAcryliconAcrylic_20240301_1624_force.csv","shearAcryliconAcrylic_20240305_1808_force.csv",
                    "shearAcryliconPaperSupportedCable_20240305_1919_force.csv", "shearAcryliconPaperUnsupportedCable_20240305_1917_force.csv",
                    "shearAcryliconPaperUnZeroedCalibratedNewRunContactAccidental_20240305_1921_force.csv",
                    "shearAcryliconPaper_20240305_1923_force.csv","shearAcryliconPLA_20240305_1841_force.csv",
                    "shearAcryliconPLA_20240305_1843_force.csv","shearFAILED_20240301_1606_force.csv","shearNOloadNOpower_20240305_1924_force.csv",
                    "shearNOLoad_20240207_1253_force.csv","shearNOLOAD_20240301_1626_force.csv", "shearNOLOAD_20240301_1627_force.csv","shearNOload_20240302_1745_force.csv",
                    "shearNOload_20240305_1851_force.csv","shearNOLoad_20240414_1641_force.csv","shearNOLoad_20240414_1645_force.csv","shearNoLoad_20240411_1810_force.csv",
                    "shearNOload_20240302_1753_force.csv"
                    ]
    test_crop(files_to_skip)
    # test_moving_avg(files_to_skip)
    # test_crop_nearzero(files_to_skip)
    # end_RoC_crop_after_smoothing(files_to_skip)