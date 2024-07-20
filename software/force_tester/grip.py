''' MOVE_GRIPPER v0.0 - Katie Allison
Hatton Lab Robotiq 2f-85 gripper control class definition

Created: 2023-07-12
Updated: 2023-07-12

This is the main function for gripper control from a PC.
'''
from robotiq_modbus_controller.driver import RobotiqModbusRtuDriver

# # for code from STARS lab repo
# from spatialmath.base import skew

class RobotiqGripper:
    OPEN = 255
    CLOSED = 0
    GRIPPER_2F85_MASS = 0.9 #Kg

    def __init__(self, device='COM5', pos=0, speed=1, force=1):
        self.driver = RobotiqModbusRtuDriver(device)
        self.driver.connect()
        self.driver.reset()
        self.driver.activate()
        self.driver.move(pos, speed, force)
        # TODO: verify whether 255 = open is true, conflicting info in STARS lab repo
        # -> update if blocks in open_gradual and close_gradual to exclude extraneous elifs

    def move(self, pos, speed, force):
        self.driver.move(pos, speed, force)
        #TODO: check if speed and force arguments can be neglected

    def open(self, speed, force):
        self.driver.move(self.OPEN, speed, force)

    def open_gradual(self, speed, force, pos_inc, pos_curr, pos_final=OPEN):
        # check direction of position increment
        if pos_curr < pos_final:
            pos_inc = abs(pos_inc)
        elif pos_curr > pos_final:
            pos_inc = -abs(pos_inc)
        else:
            return
        
        # move gripper in stages
        for next_pos in range(pos_curr, pos_final, pos_inc):
            self.driver.move(next_pos,speed,force)
    
    def close(self, speed, force):
        self.driver.move(self.CLOSED, speed, force)
    
    def close_gradual(self, speed, force, pos_inc, pos_curr, pos_final=CLOSED):
        # check direction of position increment
        if pos_curr < pos_final:
            pos_inc = abs(pos_inc)
        elif pos_curr > pos_final:
            pos_inc = -abs(pos_inc)
        else:
            return
        
        # move gripper in stages
        for next_pos in range(pos_curr, pos_final, pos_inc):
            self.driver.move(next_pos,speed,force)

    # def get_expected_wrench(gripper_mass, gripper_com, gravity):
    #     # this fcn taken from STARS lab repo file Hammer_Demo.py
    #     forces = gripper_mass*gravity
    #     torques= gripper_mass*skew(gripper_com) @ gravity
    #     return forces, torques

if __name__ == "__main__":
    gripper = RobotiqGripper(device='COM5')