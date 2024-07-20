''' FRICTION v0.0 - Katie Allison
Hatton Lab force testing platform data code for analyzing frictional properties (mainly estimated CoF)
Created: 2024-04-22

This code is used by analysis.py to compute coefficient of friction for force test data.
'''
import numpy as np

GRAVITY_CONSTANT = 9.81

def horizontal_component(force,angle_in_deg):
    angle_in_rad = np.deg2rad(angle_in_deg)
    return force*np.cos(angle_in_rad)

def vertical_component(force,angle_in_deg):
    angle_in_rad = np.deg2rad(angle_in_deg)
    return force*np.sin(angle_in_rad)

def normal_force(mass,applied_force,applied_force_angle=0):
    gravitational_force = mass*GRAVITY_CONSTANT
    applied_force_vertical = vertical_component(applied_force,applied_force_angle)
    normal_force = gravitational_force + applied_force_vertical
    return normal_force

def coefficient_of_friction(sled_mass,avg_force,force_angle=0):
    Fn = normal_force(sled_mass,avg_force,force_angle)
    Fa = horizontal_component(avg_force,force_angle)
    coeff = Fa/Fn
    return coeff

def compute_coefficient_of_friction(test_parameters,force_stats):
    test_mass,test_angle = test_parameters
    avg_force,avg_force_uncertainty = force_stats
    CoF = coefficient_of_friction(test_mass,avg_force,test_angle)
    #TODO: implement uncertainty in CoF
    return CoF

if __name__ == "__main__":
    compute_coefficient_of_friction()