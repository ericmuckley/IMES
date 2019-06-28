# -*- coding: utf-8 -*-
"""
This module allows communication to a SARK-110 portable antenna analyzer for
measurements of impedance of a quartz crystal microbalance (QCM). Portions of
this code were written by Melchor Valera under an MIT License (see copyright
and premission notice below).

Code is provided by Melchor Varela on Github at
https://github.com/EA4FRB/sark110-python/blob/master/src/sark110.py
--------------------------------------------------------------------
  This file is a part of the
  "SARK110 Antenna Vector Impedance Analyzer" software

  MIT License
  @author Copyright (c) 2018 Melchor Varela - EA4FRB

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included
  in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
---------------------------------------------------------------------

Packages required:
struct
pywinusb
threading
numpy
matplotlib
datetime
PyQt5
time

Created on Fri Jan 25 11:29:05 2019
@author: ericmuckley@gmail.com
"""
# from PyQt5 import QtCore  # for multi-threading

import time
import numpy as np
import pywinusb.hid as hid
import threading
import struct
import matplotlib.pyplot as plt
import datetime
import pandas as pd

# Code written by Melchor Valera: ------------------------------------------

rcv = [0xff] * 19
event = threading.Event()


def shortToBytes(n):
    """
    short to buffer array
    :param n:
    :return:
    """
    b = bytearray([0, 0])
    b[0] = n & 0xFF
    n >>= 8
    b[1] = n & 0xFF
    return b


def intToBytes(n):
    """
    int to buffer array
    :param n:
    :return:
    """
    b = bytearray([0, 0, 0, 0])
    b[0] = n & 0xFF
    n >>= 8
    b[1] = n & 0xFF
    n >>= 8
    b[2] = n & 0xFF
    n >>= 8
    b[3] = n & 0xFF
    return b


def rx_handler(data):
    """
    Handler called when a report is received
    :param data:
    :return:
    """
    global rcv
    rcv = data.copy()
    event.set()


def sark_open():
    """
    Opens the device
    :return: handler
    """
    target_vendor_id = 0x0483
    target_product_id = 0x5750
    filter = hid.HidDeviceFilter(vendor_id=target_vendor_id,
                                 product_id=target_product_id)
    device = filter.get_devices()[0]
    if not device:
        return
    else:
        device.open()
        device.set_raw_data_handler(rx_handler)
        return device


def sark_close(device):
    """
    Closes the device
    :param device:  handler
    :return:
    """
    device.close()


def sark_reset(device):
    """
    :param device:      handler
    :return:
    """
    report = device.find_output_reports()[0]
    snd = [0x0] * 19
    snd[1] = 50
    event.clear()
    report.set_raw_data(snd)
    report.send()
    event.wait()
    return rcv[1] == 79


def sark_version(device):
    """
    Sends the sark110 get version command.
    :param device:  handler
    :return:        prot, ver
    """
    report = device.find_output_reports()[0]
    snd = [0x0] * 19
    snd[1] = 1
    event.clear()
    report.set_raw_data(snd)
    report.send()
    event.wait()
    if rcv[1] != 79:
        return 0, ''
    prot = (rcv[3] << 8) & 0xFF00
    prot += rcv[2] & 0xFF
    ver = [0x0] * 15
    ver[:] = rcv[4:]
    return prot, ver


def sark_measure(device, freq, cal=True, samples=1):
    """
    Takes one measurement sample at the specified frequency
    :param device:  handler
    :param freq:    frequency in hertz; 0 to turn-off the generator
    :param cal:     True to get OSL calibrated data;
                    False to get uncalibrated data
    :param samples: number of samples for averaging
    :return: rs, xs
    """
    report = device.find_output_reports()[0]
    snd = [0x0] * 19
    snd[1] = 2
    b = intToBytes(freq)
    snd[2] = b[0]
    snd[3] = b[1]
    snd[4] = b[2]
    snd[5] = b[3]
    if cal:
        snd[6] = 1
    else:
        snd[6] = 0
    snd[7] = samples
    event.clear()
    report.set_raw_data(snd)
    report.send()
    event.wait()
    if rcv[1] != 79:
        return 'Nan', 'Nan'
    b = bytearray([0, 0, 0, 0])
    b[0] = rcv[2]
    b[1] = rcv[3]
    b[2] = rcv[4]
    b[3] = rcv[5]
    rs = struct.unpack('f', b)
    b[0] = rcv[6]
    b[1] = rcv[7]
    b[2] = rcv[8]
    b[3] = rcv[9]
    xs = struct.unpack('f', b)
    return rs, xs


# The following code enables fast aquisition by using half-float precision
# --------------half float decompress -------------------------


def half2Float(byte1, byte2):
    hfs = (byte2 << 8) & 0xFF00
    hfs += byte1 & 0xFF
    temp = _half2Float(hfs)
    str = struct.pack('I', temp)
    return struct.unpack('f', str)[0]


def _half2Float(float16):
    s = int((float16 >> 15) & 0x00000001)   # sign
    e = int((float16 >> 10) & 0x0000001f)   # exponent
    f = int(float16 & 0x000003ff)           # fraction

    if e == 0:
        if f == 0:
            return int(s << 31)
        else:
            while not (f & 0x00000400):
                f = f << 1
                e -= 1
            e += 1
            f &= ~0x00000400
        # print(s,e,f)
    elif e == 31:
        if f == 0:
            return int((s << 31) | 0x7f800000)
        else:
            return int((s << 31) | 0x7f800000 | (f << 13))

    e = e + (127 - 15)
    f = f << 13
    return int((s << 31) | (e << 23) | f)


def sark_measure_ext(device, freq, step, cal=True, samples=1):
    """
    Takes four measurement samples starting at the specified frequency and
    incremented at the specified step.
    Uses half float, so a bit less precise
    :param device:  handler
    :param freq:    frequency in hertz; 0 to turn-off the generator
    :param step:    step in hertz
    :param cal:     True to get OSL calibrated data;
                    False to get uncalibrated data
    :param samples: number of samples for averaging
    :return: rs, xs  four vals
    """
    report = device.find_output_reports()[0]
    snd = [0x0] * 19
    snd[1] = 12
    b = intToBytes(freq)
    snd[2] = b[0]
    snd[3] = b[1]
    snd[4] = b[2]
    snd[5] = b[3]
    b = intToBytes(step)
    snd[8] = b[0]
    snd[9] = b[1]
    snd[10] = b[2]
    snd[11] = b[3]
    if cal:
        snd[6] = 1
    else:
        snd[6] = 0
    snd[7] = samples
    event.clear()
    report.set_raw_data(snd)
    report.send()
    event.wait()
    if rcv[1] != 79:
        return 'Nan', 'Nan'
    rs = [0x0] * 4
    xs = [0x0] * 4

    rs[0] = half2Float(rcv[2], rcv[3])
    xs[0] = half2Float(rcv[4], rcv[5])
    rs[1] = half2Float(rcv[6], rcv[7])
    xs[1] = half2Float(rcv[8], rcv[9])
    rs[2] = half2Float(rcv[10], rcv[11])
    xs[2] = half2Float(rcv[12], rcv[13])
    rs[3] = half2Float(rcv[14], rcv[15])
    xs[3] = half2Float(rcv[16], rcv[17])

    return rs, xs


# code written by Eric Muckley: ------------------------------------------


def get_f_d(f_array, g_array, calc_d=False):
    '''From the QCM conductance spectra containing frequency array (f_array)
    and conductance array (g_array), determine resonant frequency (f0)
    and dissipation (D). F0 is the frequency at which the conductance is
    maximum, and D is calculated from width of the resonance peak.
    To obain D, the peak must first be fit to a Lorentzian distribution
    so that peak width can be extracted. This peak fitting may be
    problematic for poorly-defined peaks, so the argument "calc_d" is
    optional and defaults to "False".
    Example inputs:
        freq_array = [4990444, 4990445, 4990446, 4990447, 4990448]
        band_width = [1.01, 1.02, 1.03, 1.025, 1.02]
        calc_d = False
    Returns the reonant frequency (f0) in Hz,
    and energy dissipation (d0) (unitless).
    '''
    # check if arrays are same length
    if len(f_array) != len(g_array):
        f0, d0 = 0, 0
        print('Error: Frequency and conductance arrays must be same length!')
    # get peak position (f0)
    else:
        f0 = f_array[np.argmax(g_array)]

    # get dissipation (d0)
    if not calc_d:
        d0 = 0
    else:
        d0 = 0

    return f0, d0


def get_band(band_center, band_width, band_points=1000):
    '''Construct an array of frequencies to measure across based on
    the frequency band center in Hz, band width in Hz, and number of points.
    Example inputs:
        band_center = 5e6
        band_width = 500000
        band_points = 1000
    Returns an array of frequency values in Hz.
    '''
    band = np.linspace(band_center - band_width/2,
                       band_center + band_width/2,
                       num=int(band_points)).astype(int)
    return band


def get_bands_using_n(f0=5e6, n_list=[1], band_points=1000):
    '''Construct an array of frequencies to measure across based on
    the frequency band center in Hz, band width in Hz, and number of points.
    Instead of the user specifying the band center and band width,
    appropriate band center and width are estimated based on the
    fundamental resonant frequency (f0) and harmonic number (n) of the QCM.
    The function accepts a list of harmonics and returns a band center (bc),
    bandwidth (bw), and actual array of frequency values in the band (band).
    Example inputs:
        f0 = 5e6
        n = [1, 3, 5]
        band_points = 1000
    Returns a dictionary of and centers, widths, and frequency arrays.
    Each dictionary key corresponds to one harmonic.
    '''
    # create empty dictionary to hold everything
    band_dict = {}
    # loop through each harmonic
    for n0 in n_list:
        # create dictionaries to hold band center, width, and frequencies
        band_dict[str(n0)] = {}
        # determine band center and band width based on harmonic number
        band_center = int(0.99*f0*n0 - 10000*(n0-1))
        band_width = 20000 + 10000*(n0-1)
        # construct frequency band
        band = np.linspace(band_center - band_width/2,
                           band_center + band_width/2,
                           num=int(band_points)).astype(int)
        # band center
        band_dict[str(n0)]['bc'] = band_center
        # band width
        band_dict[str(n0)]['bw'] = band_width
        # actual band, in Hz
        band_dict[str(n0)]['band'] = band
    return band_dict


def get_conductance(rs, xs):
    '''Calculate series conductance from series resistance (Rs) and
    series reactance (Xs) measured by the SARK-110. Can also be used to
    calculate complex impedance, complex admittance, and susceptance.
    Example inputs:
        rs = 1.03405
        xs = -0.9348
    Returns series conductance value.
    '''
    # complex impedance
    Z = np.add(rs, 1j*xs)
    # complex admittance
    Y = np.reciprocal(Z)
    # susceptance
    # B = np.imag(Y)
    # conductance
    G = np.real(Y)
    return G


def get_fast_g(device, freq, step, cal=True, avg=1):
    '''
    ADAPTED FROM sark_measure_ext() FUNCTION:

    Takes four measurement samples starting at the specified frequency and
    incremented at the specified step.
    Uses half float, so a bit less precise
    :param device:  handler
    :param freq:    frequency in hertz; 0 to turn-off the generator
    :param step:    step in hertz
    :param cal:     True to get OSL calibrated data;
                    False to get uncalibrated data
    :param samples: number of samples for averaging
    :return: rs, xs  four vals

    Measures conductange (G) using series resistance (Rs)
    and series reactance (Xs) from SARK-110 with averaging (if specified).
    The value of "avg" is the number of measurements which is used for
    each average, where 1 corresponds to no averaging.
    The function requires frequency and step, where frequency is the first
    frequency to measure, and step is the frequency interval to measure
    at next. The function returns" 4 values of conductance (G), which are
    spaced at frequencies 1 step apart.
    Example inputs:
        device = sark_device
        freq = 5e6
        step = 10
        cal = True
        avg = 4
    Returns series conductance value.
    '''
    report = device.find_output_reports()[0]
    snd = [0x0] * 19
    snd[1] = 12
    b = intToBytes(freq)
    snd[2] = b[0]
    snd[3] = b[1]
    snd[4] = b[2]
    snd[5] = b[3]
    b = intToBytes(step)
    snd[8] = b[0]
    snd[9] = b[1]
    snd[10] = b[2]
    snd[11] = b[3]
    if cal:
        snd[6] = 1
    else:
        snd[6] = 0
    snd[7] = avg
    event.clear()
    report.set_raw_data(snd)
    report.send()
    event.wait()
    if rcv[1] != 79:
        return 'Nan', 'Nan'
    rs = [0x0] * 4
    xs = [0x0] * 4

    rs[0] = half2Float(rcv[2], rcv[3])
    xs[0] = half2Float(rcv[4], rcv[5])
    rs[1] = half2Float(rcv[6], rcv[7])
    xs[1] = half2Float(rcv[8], rcv[9])
    rs[2] = half2Float(rcv[10], rcv[11])
    xs[2] = half2Float(rcv[12], rcv[13])
    rs[3] = half2Float(rcv[14], rcv[15])
    xs[3] = half2Float(rcv[16], rcv[17])

    # calculate conductance from 4-array of rs and xs
    g = [get_conductance(rs[i], xs[i]) for i in range(4)]

    return g


def measure_g(device, freq, cal=True, avg=1):
    '''Measures series resistance (Rs) and series reactance (Xs) using
    SARK-110 with averaging (if specified). These values are converted
    to series conductance (G). The value of "avg" is the number of
    measurements which is used for each average, where 1 corresponds to
    no averaging.
    Example inputs:
        device = sark_device
        freq = 5e6
        cal = True
        avg = 4
    Returns series conductance value.
    '''
    report = device.find_output_reports()[0]
    snd = [0x0] * 19
    snd[1] = 2
    b = intToBytes(freq)
    snd[2] = b[0]
    snd[3] = b[1]
    snd[4] = b[2]
    snd[5] = b[3]
    if cal:
        snd[6] = 1
    else:
        snd[6] = 0
    snd[7] = avg
    event.clear()
    report.set_raw_data(snd)
    report.send()
    event.wait()
    if rcv[1] != 79:
        return 'Nan', 'Nan'
    b = bytearray([0, 0, 0, 0])
    b[0] = rcv[2]
    b[1] = rcv[3]
    b[2] = rcv[4]
    b[3] = rcv[5]
    rs = float(struct.unpack('f', b)[0])
    b[0] = rcv[6]
    b[1] = rcv[7]
    b[2] = rcv[8]
    b[3] = rcv[9]
    xs = float(struct.unpack('f', b)[0])

    G = get_conductance(rs, xs)
    return G

# ---- The following functions are used to communicate with PyQT GUI -------


def checked(sark_dict):
    # This function triggers when SARK-110 checkbox status changes.
    if sark_dict['sark_on'].isChecked():  # if SARK checkbox was checked
        try:
            sark_dict['sark_dev'] = sark_open()
            sark_dict['menu_qcm'].setEnabled(True)
            sark_dict['qcm_box'].setEnabled(True)
            sark_dict['output_box'].append('SARK-110 connected.')
        except NameError:
            sark_dict['output_box'].append('SARK-110 could not connect.')
    if not sark_dict['sark_on'].isChecked():  # if SARK checkbox was unchecked
        try:
            sark_close(sark_dict['sark_dev'])
            sark_dict['menu_qcm'].setEnabled(False)
            sark_dict['qcm_box'].setEnabled(False)
            sark_dict['output_box'].append('SARK-110 disconnected.')
        except NameError:
            pass


def get_selected_harmonics(sark_dict):
    # Get a list of the harmonics which are selected on the GUI.
    n_selected = []
    for n0 in sark_dict['n_on_fields']:
        if sark_dict['n_on_fields'][n0].isChecked():
            n_selected.append(int(n0))
    return n_selected


'''
def measure_band(device, band_center, band_width, band_points, avg=1):
    # Measure conductance spectrum across a single frequency band
    band = np.linspace(band_center - band_width/2,
                       band_center + band_width/2,
                       num=int(band_points)).astype(int)
    band_step = band[2] - band[1]  # get frequency interval in band
    # create array to hold the data
    spec = np.zeros((band_points, 2))
    spec[:, 0] = band

    # loop over each point in frequency band
    for f0_i in range(0, len(band), 4):
        # QtCore.QCoreApplication.processEvents()  # handle threading
        # measure conductance at each frequency
        g_vec = get_fast_g(device, band[f0_i], band_step, avg=avg)

        spec[f0_i:f0_i+4, 1] = g_vec  # save conductance values
    return spec
'''


def measure_band(sark_dict, band_center, band_width):
    # Measure conductance spectrum across a single frequency band
    device = sark_dict['sark_dev']
    band_points = int(sark_dict['set_band_points'].text())
    avg = int(sark_dict['set_qcm_averaging'].text())

    band = np.linspace(band_center - band_width/2,
                       band_center + band_width/2,
                       num=int(band_points)).astype(int)
    band_step = band[2] - band[1]  # get frequency interval in band

    # create array to hold the data
    spec = np.zeros((band_points, 2))
    spec[:, 0] = band

    # loop over each point in frequency band
    for f0_i in range(0, len(band), 4):
        # QtCore.QCoreApplication.processEvents()  # handle threading
        # measure conductance at each frequency
        g_vec = get_fast_g(device, band[f0_i], band_step, avg=avg)

        spec[f0_i:f0_i+4, 1] = g_vec  # save conductance values

        sark_dict['actual_frequency'].setText(str(band[f0_i]/1e6))
        sark_dict['actual_conductance'].setText(str(g_vec[0]*1e3))

    return spec


def find_resonances(sark_dict):
    # Find resonance frequencies at selected QCM frequency bands
    n_list = get_selected_harmonics(sark_dict)
    sark_dict['sark_busy'] = True
    sark_dict['measure_bands'].setEnabled(False)
    sark_dict['find_resonances'].setEnabled(False)
    # loop through each selected harmonic
    for n in n_list:
        # QtCore.QCoreApplication.processEvents()  # handle threading

        band_start_time = time.time()
        sark_dict['output_box'].append(
                'Searching for n = '+str(n)+' resonance...')
        # estimate band location based on harmonic number
        bandcenter = int(sark_dict['set_f0'].text())*1e6*n - (5e4*n)
        bandwidth = 500000*n

        spec = measure_band(sark_dict, bandcenter, bandwidth)

        # get resonant frequency of band
        f0 = spec[np.argmax(spec[:, 1]), 0]
        sark_dict['output_box'].append(
                'n = '+str(n)+' resonance found at '+str(int(f0))+' Hz')
        # update GUI displays
        sark_dict['bc_fields'][str(n)].setText(str(int(f0)))
        sark_dict['f0_displays'][str(n)].setText(str(int(f0)))
        # suggested bandwidths to populate GUI with
        sark_dict['bw_fields'][str(n)].setText(str(int(bandwidth/2)))

        # plot band and resonance frequency
        plt.ion
        fig_qcm = plt.figure(100)
        fig_qcm.clf()
        plt.plot(spec[:, 0]/1e6, spec[:, 1],
                 c='k', lw=4, alpha=0.3)
        plt.axvline(x=f0/1e6, lw=1, c='r')
        plt.xlabel('Frequency (Hz)', fontsize=12)
        plt.ylabel('Conductance (S)', fontsize=12)
        plt.title('Detected n = '+str(n)+' resonance', fontsize=12)
        fig_qcm.canvas.set_window_title('QCM resonance')
        plt.tight_layout()
        plt.draw()
        plt.pause(1)
        plt.close()

        band_time = int(time.time() - band_start_time)
        sark_dict['sec_per_band'].setText(str(band_time))

    sark_dict['output_box'].append('Resonance search complete.')
    sark_dict['sark_busy'] = False
    sark_dict['measure_bands'].setEnabled(True)
    sark_dict['find_resonances'].setEnabled(True)


def measure_bands(sark_dict):
    # Measure accross selected frequency bands using band centers and
    # band widths designated on fields on GUI.
    # get selected harmonics
    n_list = get_selected_harmonics(sark_dict)
    sark_dict['sark_busy'] = True
    sark_dict['measure_bands'].setEnabled(False)
    sark_dict['find_resonances'].setEnabled(False)
    # loop through each selected harmonic
    for n in n_list:
        # QtCore.QCoreApplication.processEvents()  # handle threading

        band_start_time = time.time()

        sark_dict['output_box'].append(
                'Measuring n = '+str(n)+' band...')
        # estimate band location based on harmonic number

        bandcenter = int(sark_dict['bc_fields'][str(n)].text())
        bandwidth = int(sark_dict['bw_fields'][str(n)].text())

        spec = measure_band(sark_dict, bandcenter, bandwidth)

        # get resonant frequency of band
        f0 = spec[np.argmax(spec[:, 1]), 0]
        sark_dict['output_box'].append(
                'Measurement at n = '+str(n)+' band complete.')

        # update GUI displays
        sark_dict['f0_displays'][str(n)].setText(str(int(f0)))
        # for dynamic frequency window,
        # this will change the bandcenter on each loop
        if sark_dict['dynamic_bc'].isChecked():
            sark_dict['bc_fields'][str(n)].setText(str(int(f0)))

        # plot band
        plt.ion
        fig_qcm = plt.figure(101)
        fig_qcm.clf()
        plt.plot(spec[:, 0]/1e6, spec[:, 1]*1e3,
                 c='k', lw=1)
        plt.xlabel('Frequency (MHz)', fontsize=12)
        plt.ylabel('Conductance (mS)', fontsize=12)
        plt.title('n = '+str(n)+' conductance spectrum', fontsize=12)
        fig_qcm.canvas.set_window_title('QCM conductance spectrum')
        plt.tight_layout()
        plt.draw()
        plt.pause(2)
        plt.close()

        sark_dict['output_box'].append('Multi-band measurement complete.')

        # create empty columns to hold data
        sark_dict['qcm_data'][str(n)][[
                'freq__'+time.ctime(),
                'cond__'+time.ctime()]] = pd.DataFrame(np.full((10000, 2), ''))
        # append data to the empty columns
        sark_dict['qcm_data'][str(n)][
                'freq__'+time.ctime()].iloc[
                        :len(spec)] = spec[:, 0].astype(str)
        sark_dict['qcm_data'][str(n)][
                'cond__'+time.ctime()].iloc[
                        :len(spec)] = spec[:, 1].astype(str)

        '''
        print(sark_dict['qcm_data'][
                str(n)][['freq__'+time.ctime(),
                         'cond__'+time.ctime()]].iloc[:5])
        '''

        # save dataframe to file
        spec_filename = sark_dict['save_file_dir']+'/'+sark_dict[
                      'start_date']+'_qcm_n='+str(n).zfill(1)+'_spectra.csv'
        sark_dict['qcm_data'][str(n)].to_csv(spec_filename, index=False)

        # save delta F and delta D parameters from qcm spectra
        sark_dict['qcm_data']['params']['f_'+str(n)].iloc[
                sark_dict['nth_qcm_loop']] = str(int(f0))
        sark_dict['qcm_data']['params']['time'].iloc[
                sark_dict['nth_qcm_loop']] = str(time.ctime())

        params_filename = sark_dict['save_file_dir']+'/'+sark_dict[
                      'start_date']+'_qcm_params.csv'
        sark_dict['qcm_data']['params'].to_csv(params_filename, index=False)

        band_time = int(time.time() - band_start_time)
        sark_dict['sec_per_band'].setText(str(band_time))

    # increment the number of QCM loops which have been measured
    sark_dict['nth_qcm_loop'] += 1
    sark_dict['sark_busy'] = False
    sark_dict['measure_bands'].setEnabled(True)
    sark_dict['find_resonances'].setEnabled(True)
    view_qcm_data(sark_dict)


def view_qcm_data(sark_dict):
    # View delta F and delta D parameters over time.
    params_filename = sark_dict['save_file_dir']+'/'+sark_dict[
                      'start_date']+'_qcm_params.csv'
    try:  # check if qcm data file exists
        df = pd.read_csv(params_filename)
        # select frequency columns
        dff = df[['time', 'f_1', 'f_3', 'f_5', 'f_7', 'f_9',
                  'f_11', 'f_13', 'f_15', 'f_17']]
        # select dissipation columns
        dfd = df[['time', 'd_1', 'd_3', 'd_5', 'd_7', 'd_9',
                  'd_11', 'd_13', 'd_15', 'd_17']]
        plt.ion
        fig_qcm = plt.figure(110)
        fig_qcm.clf()

        # loop over frequency columns
        for col in dff.iloc[:, 1:]:
            # get harmonic number
            n = int(col.split('_')[1])

            f_list = dff[dff[col].notnull()][col].astype(float)

            if len(f_list) > 0:  # check if data was measured at the harmonic
                df_list = np.subtract(f_list, f_list[0])/n
                # format times
                time_list = dff[dff[col].notnull()]['time']
                time_list = [datetime.datetime.strptime(
                        i, "%a %b %d %H:%M:%S %Y")for i in time_list]
                # plot df/n over time
                # print(time_list)
                # print(df_list)
                plt.plot(time_list, df_list, marker='o', label='n='+str(n))
        plt.legend()
        plt.xticks(rotation=90)
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Delta f/n (Hz/cm$^2$)', fontsize=12)
        plt.title('Delta f over time', fontsize=12)
        fig_qcm.canvas.set_window_title('QCM resonance')
        plt.tight_layout()
        plt.draw()
        plt.pause(5)
        plt.close()

        # loop over dissipation columns
        for col in dfd.iloc[:, 1:]:
            n = int(col.split('_')[1])

    except NameError:  # if qcm data file does not exist
        sark_dict['output_box'].append('No QCM data file found.')


'''

The remaining functions may be used for fitting, smoothing, plotting,
and modeling of measured QCM data.


def update_dict():
    #increases size of dictionary which holds measurement parameters so
    #that new parameters can be appended to each key after every measurement
    #loop

    #add keys for spectra after they have been measured
    if i == 0: pass

    #scan through each dictionary key and expand their sizes
    for key in qcm_dict:
        #for 2D dictionary values, add a row
        if len(np.shape(qcm_dict[key])) == 2:
            qcm_dict[key] = np.vstack((qcm_dict[key],
               np.zeros((1, np.shape(qcm_dict[key])[1]))))
        #for 3D dictionary values, stack an aray to the 3rd dimension
        if len(np.shape(qcm_dict[key])) == 3:
            qcm_dict[key] = np.dstack((qcm_dict[key],
               np.zeros((np.shape(qcm_dict[key])[0],np.shape(qcm_dict[key])[1],
                         1))))

        else: pass



def analyze_peak():
    #analyze peak in SARK-110 spectrum
    #get spline fit for smoothing the spectrum
    g_spline_fit = interp.UnivariateSpline(Sark.band, Sark.g_vec, s=1e-8)
    #fit conductance to spline for smoothing
    g_spline = g_spline_fit(Sark.band)

    #calculate peak position and height
    f_res = Sark.band[np.argmax(g_spline)]

    qcm_dict['f_res'][i,n] = f_res
    qcm_dict['Gmax'][i,n] = np.max(g_spline)
    qcm_dict['f'][:,n,i] = Sark.band
    qcm_dict['g'][:,n,i] = Sark.g_vec
    qcm_dict['g_spline'][:,n,i] = g_spline





def bvd_fit():
    #fit peak to Lorentzian Butterworth Van Dyke equivalent circuit model

    #for first measurement at this harmonic, construct guess for RLC fit
    if i == 0:
        bvd_guess = [0,
                     0,
                     np.max(qcm_dict['g_spline'][:,n,i]),
                     1e-5,
                     qcm_dict['f_res'][n,i]]

    #for subsequent measurements, use previous fit params as guess
    if i > 0:
        bvd_guess = qcm_dict['bvd_fit_params'][:,n,i-1]
        #for G max guess, use measured G max
        bvd_guess[2] = qcm_dict['Gmax'][i,n]
        #for res. freq. guess, use freq at G max
        bvd_guess[4] = qcm_dict['f_res'][i,n]


    #find index of peak
    peak_ind = np.argmax(qcm_dict['f'][:,n,i])

    #set selective fitting window around peak
    fit_win = 60
    f_fit_win = qcm_dict['f'][:,n,i][:peak_ind + fit_win]
    g_fit_win = qcm_dict['g_spline'][:,n,i][:peak_ind + fit_win]

    #fit data to lorentz peak
    try: rlc_params,_ = curve_fit(Sark.single_lorentz,
                               f_fit_win,#f_mat[:,n,i],
                               g_fit_win,#g_mat[:,n,i],
                               bounds=(0,np.inf),
                               p0=bvd_guess)
    except RuntimeError:
        print('BVD FIT FAILED')
        rlc_params = bvd_guess

    #populate matrix of fit parameters
    qcm_dict['bvd_fit_params'][:,n,i] = rlc_params
    qcm_dict['D'][i,n] = rlc_params[3]
    #calculate RLC from Butterworth Van Dyke equivalent circuit
    qcm_dict['R'][i,n] = Sark.single_RLC(rlc_params)[0]
    qcm_dict['L'][i,n] = Sark.single_RLC(rlc_params)[1]
    qcm_dict['C'][i,n] = Sark.single_RLC(rlc_params)[2]

    #calculate fitted curve
    g_fit = Sark.single_lorentz(qcm_dict['f'][:,n,i], *rlc_params)
    qcm_dict['bvd_fit'][:,n,i] = g_fit



def plot_spectrum():
    #plot QCM spectrum with BVD fit
    ls = 16
    plt.rcParams['xtick.labelsize'] = ls
    plt.rcParams['ytick.labelsize'] = ls
    plt.xlabel('Frequency (Hz)', fontsize=ls)
    plt.ylabel('Conductance (mS)', fontsize=ls)
    plt.title('Loop %i, %i%% RH'%(i, RH.val), fontsize=ls)
    plt.plot(Sark.band, Sark.g_vec, label='data')
    plt.plot(Sark.band, qcm_dict['bvd_fit'][:,n,i], label='fit')
    plt.legend(fontsize=14)
    plt.show()



def single_lorentz(freq, Gp, Cp, Gmax, D0, f0):
    # Returns conductance spectrum with single peak.
    # Spectrum calculation is taken from Equation (2) in:
    # Yoon, S.M., Cho, N.J. and Kanazawa, K., 2009. Analyzing spur-distorted
    # impedance spectra for the QCM. Journal of Sensors, 2009.
    # Gp = parallel conductance offset
    # Cp = parallel susceptance offset
    # Gmax = maximum of conductance peak
    # D0 = dissipation
    # f0 = resonant frequency of peak (peak position)
    #construct peak
    peak = Gmax / (1 + (1j/D0)*((freq/f0)-(f0/freq)))
    #add parallel offsets to peak
    Y = Gp + 1j*2*np.pi*freq*Cp + peak
    G = np.real(Y)
    return G


def single_RLC(fit_params0):
    # calculate equivalent circuit parameters from RLC fits
    # from Yoon et al., Analyzing Spur-Distorted Impedance
    # Spectra for the QCM, Eqn. 3.
    #FIT PARAMS = [Gp, Cp, Gmax0, D0, f0]
    G0 = fit_params0[2]
    f0 = fit_params0[4]
    D0 = fit_params0[3]
    R = 1/G0
    L = 1 / (2 * np.pi * f0 * D0 * G0)
    C = 1 / (4 * np.pi**2 * f0**2 * L)
    return R, L, C

def single_exp(x, a, tau, y0):
    #single exponential function with y offset
    return a * np.exp(-(x) / tau) + y0





def plot_all():
    #plot all measured parameters from SARK-110 over time

    keys = ['f_res', 'D']
    titles = ['$\Delta$f/n (Hz/cm$^{2}$)', '$\Delta$D/n']

    for key, title in keys, titles:
        for n, n_i in enumerate(Sark.h_list):
            plt.plot((qcm_dict[key][:,n_i])/n, label=format(n))
        ls = 16
        plt.rcParams['xtick.labelsize'] = ls
        plt.rcParams['ytick.labelsize'] = ls
        plt.xlabel('Time', fontsize=ls)
        plt.ylabel(title, fontsize=ls)
        plt.legend()
        plt.show()





def plot_rlc_params(dic, overtone_list, iteration_num):
    #realtime plotting of RLC parameters, deltaF, and deltaD
    ls = 16
    fig, axarr = plt.subplots(5, sharex=True)
    axarr[0].set_ylabel('$\Delta$f/n (Hz/cm$^{2}$)', fontsize=ls)
    axarr[1].set_ylabel('$\Delta$D/n (x10$^{6}$)', fontsize=ls)
    axarr[2].set_ylabel('$\Delta$R/n ($\Omega$)', fontsize=ls)
    axarr[3].set_ylabel('$\Delta$L/n (mH)', fontsize=ls)
    axarr[4].set_ylabel('$\Delta$C/n (fF)', fontsize=ls)
    axarr[4].set_xlabel('Elapsed time (minutes)', fontsize=ls)
    for h in range(len(Sark.h_list)):
        axarr[0].plot(dic['elapsed_time'][:i, 1],
                (np.array(
                dic['f_res'][:i, h]) - dic['f_res'][0,h])/Sark.h_list[h],
                label='n='+format(Sark.h_list[h]))
        axarr[1].plot(dic['elapsed_time'][:i, 1],
                (np.array(dic['D'][:i, h]) - dic['D'][0,h])*1e6/Sark.h_list[h],
                label='n='+format(Sark.h_list[h]))
        axarr[2].plot(dic['elapsed_time'][:i, 1],
                 (np.array(dic['R'][:i, h]) - dic['R'][0,h])/Sark.h_list[h],
                 label='n='+format(Sark.h_list[h]))
        axarr[3].plot(dic['elapsed_time'][:i, 1],
                (np.array(dic['L'][:i, h]) - dic['L'][0,h])*1e3/Sark.h_list[h],
                label='n='+format(Sark.h_list[h]))
        axarr[4].plot(dic['elapsed_time'][:i, 1],
                (np.array(
                dic['C'][:i, h]) - dic['C'][0,h])*1e15/Sark.h_list[h],
                label='n='+format(Sark.h_list[h]))
    axarr[4].legend(loc='upper left', ncol=2)
    fig.set_size_inches(6,10)
    fig.subplots_adjust(left=.25, right=.95, bottom=.08, top=.98, hspace=0)
    plot_param_filename = Directory.figs+'qcm_params_'+str(
                                                    i).rjust(4, '0')+'.png'
    plt.savefig(plot_param_filename, format='png', dpi=150)
    plt.show()

'''
