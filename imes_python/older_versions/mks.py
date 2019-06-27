# -*- coding: utf-8 -*-
"""
This module controls the MKS 600 series (651) pressure controller,
which should be connected to the MKS butterfly valve and MKS
pressure transducers.

author: ericmuckley@gmail.com
"""


import time
import visa
import numpy as np



def set_valve_pos(dev, position):
    # set the butterfly valve position using MKS 651 pressure controller
    # select setpoint C
    dev.write('D3')
    # set setpoint C to valve mode
    dev.write('T30')
    # set setpoint C position of valve in terms of % open
    dev.write('S3'+str(position))
    

def set_pressure(dev, pressure):
    # set pressure using MKS 651 pressure controller
    # select setpoint D
    dev.write('D3')
    # set setpoint D to pressure mode
    dev.write('T31')
    # set setpoint D pressure in terms of % of total range
    dev.write('S3'+str(pressure/10))


def get_valve_pos(dev):
    # get valve position from MKS 600 pressure controller using device name
    valve_pos_str = dev.query('R6').rstrip()[1:]
    return np.round(float(valve_pos_str), decimals=1)


def get_pressure(dev):
    # get pressure reading from MKS 600 pressure controller using device name
    # read the pressure
    press_str = dev.query('R5').rstrip()[1:]
    return np.round(float(press_str)*10, decimals=5)


if __name__ == '__main__':

    rm = visa.ResourceManager()
    # list all resources connected to PC
    # print(rm.list_resources())

    # create instance of MKS instrument
    mks = rm.open_resource('COM12', timeout=5)

    valve_mode = False

    if valve_mode:
        # set valve to valve mode
        set_valve_pos(mks, 0)

    else:
        # set valve to pressure mode
        set_pressure(mks, 0.5)

    print('pressure: %f' % get_pressure(mks))
    print('valve position: %f' % get_valve_pos(mks))
    mks.close()
