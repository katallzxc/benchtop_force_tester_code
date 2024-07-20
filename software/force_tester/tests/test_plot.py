
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import plot
import numpy as np
from plot import Plotter

def test_plot(Pltr):
    xy_data = np.array([[1,2],[2,8],[3,24]])
    Pltr.plot_data_series(("testfile1","testfile2"),xy_data,"test vals",(0,1),None)
    Pltr.fully_label_plot("test title",("textx","testy"))
    xy_data2 = np.array([[1,7],[2,-2],[3,6]])
    Pltr.plot_data_series(("testfiled12","testfile22"),xy_data2,"test vals 2",(0,1),None)
    xy_data_fit = Pltr.analyze_series(xy_data2,)
    Pltr.plot_data_series(("testfile12","testfile22"),xy_data2,"test vals 2",(0,1),None)
    Pltr.show_plot()

if __name__ == "__main__":
    test_plot(Plotter())