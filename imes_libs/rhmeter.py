# -*- coding: utf-8 -*-
"""
This module allows communication to a Sper Scientific RH/Temp
SD Card Datalogger model 800021. The meter steams relative humidity
and temeprature readings through a serial port.

Packages required:
serial

Created on Wed Jan 16 17:39:06 2019
@author: ericmuckley@gmail.com
"""


def initialize(device_address):
    '''Set up device using the COM port of the RH meter.
    Example inputs:
        device_address = 'COM73'
    Returns a device instance.
    '''
    import serial
    dev = serial.Serial(port=device_address)
    return dev


def read(dev):
    '''Read relative humidity (RH) and temperature from meter. The meter
    sends data through 32 serial bytes which must be formatted.
    This function should not be called more than once every 2 seconds
    due to data buffering issues.
    Example inputs:
        dev = initialize(device_address)
    Returns a two-tuple of RH (%) and temperature (C).
    '''
    # flush buffer to speed up data acquisition
    dev.flushInput()
    # read 32 bytes from device
    rhmeter_output = dev.read(32)
    # read raw bytes corresponding to rh and temp
    raw_rh, raw_temp, _ = rhmeter_output.decode().split('\r')
    # trim excess bytes
    rh = float(raw_rh[11:])
    temp = float(raw_temp[11:])
    # convert raw byte readings into floats (see device manual for details)
    rh = rh / (float(raw_rh[6])*10)
    temp = temp / (float(raw_temp[6])*10)
    return rh, temp


def close(dev):
    '''Close the serial device.
    Example inputs:
        device_address = 'COM73'
    '''
    dev.close()
