''' STATS v0.0 - Katie Allison
Hatton Lab force testing platform data statistical analysis helper functions

Created: 2024-02-08
Updated: 2024-02-08

This code imports data and returns statistical quantities.
'''
import numpy as np

def get_shape(data):
    return np.shape(data)

def get_mean(data,col=2):
    return np.average(data[:,col])

def get_median(data,col=2):
    return np.median(data[:,col])

def get_min(data,col=2):
    return np.min(data[:,col])

def get_max(data,col=2):
    return np.max(data[:,col])

def get_basic_stats(curr_data,curr_col=2):
    mean = get_mean(curr_data,curr_col)
    median = get_median(curr_data,curr_col)
    min = get_min(curr_data,curr_col)
    max = get_max(curr_data,curr_col)
    return mean,median,min,max

if __name__=="__main__":
    fake_data = np.random.rand(10,3)
    print(get_shape(fake_data))
    print(get_basic_stats(fake_data))