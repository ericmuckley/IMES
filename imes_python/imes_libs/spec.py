# -*- coding: utf-8 -*-
"""
This module allows communication with an Ocean Optics USB4000 spectormeter.
The spectrometer device will not be found unless 'libusb-1.0.dll' DLL library
file is correctly imported (see import lines).

Created on Thu Nov 29 11:14:57 2018
@author: ericmuckley@gmail.com
"""

import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
# from scipy.signal import savgol_filter

# manually fix pyUSB installation for import of Ocean Optics Spectometer
# DO NOT CHANGE THE ORDER OF THE FOLLOWING LINES OR DEVICE WILL NOT BE FOUND
import usb.backend.libusb1
# THIS LINE MUST POINT TO APPROPRIATE DLL LIBRARY FILE 'libusb-1.0.dll'
backend = usb.backend.libusb1.get_backend(
        find_library=lambda x: 'libusb-1.0.dll')
dev = usb.core.find(backend=backend)
import seabreeze
seabreeze.use('pyseabreeze')
import seabreeze.spectrometers as sb
fontsize = 12


def initialize_spectrometer(spec_dict):
    # connect to Ocean Optics USB4000 spectrometer
    sm = sb.Spectrometer(sb.list_devices()[0])
    # print(sm.pixels)
    return sm


def spec_checked(spec_dict):
    # run this when spectrometer checkbox on GUI is checked or unchecked
    # open spectrometer
    if spec_dict['spec_on'].isChecked():

        # try to connect to spectrometer
        try:
            sm = sb.Spectrometer(sb.list_devices()[0])
            spec_dict['output_box'].append('Spectrometer connected.')
            spec_dict['optical_box'].setEnabled(True)
            sm.close()
        except NameError:
            spec_dict['output_box'].append('No spectrometer found.')
            spec_dict['spec_on'].setChecked(False)
            spec_dict['optical_box'].setEnabled(False)

    # close spectrometer
    if not spec_dict['spec_on'].isChecked():
        spec_dict['output_box'].append('Spectrometer disconnected.')
        spec_dict['optical_box'].setEnabled(False)


def get_spec(spec_dict):
    '''acquire optical spectrum from OceanOptics spectrometer 'device', using
    integration time 'int_time' and filtering'''

    spec_dict['measure_button'].setEnabled(False)
    # connect to Ocean Optics USB4000 spectrometer
    sm = sb.Spectrometer(sb.list_devices()[0])

    spec_dict['output_box'].append('Measuring optical spectrum...')
    # set measurement integration time in microseconds
    int_time = int(spec_dict['spec_int_time'].value())
    sm.integration_time_micros(int_time)
    # set wavelengths in nm
    wl0 = sm.wavelengths()[10:-185]
    # measure intensities
    int0 = sm.intensities(correct_dark_counts=False,
                          correct_nonlinearity=False)[10:-185]
    sm.close()
    spec_time = time.strftime('%Y-%m-%d_%H-%M-%S_')
    spec_dict['output_box'].append('Optical spectrum measurement complete.')

    max_intensity = np.round(np.amax(int0), decimals=3)
    wavelength_at_max = np.round(wl0[np.argmax(int0)], decimals=3)
    spec_dict['max_intensity'].setText(str(max_intensity))
    spec_dict['wavelength_at_max'].setText(str(wavelength_at_max))

    '''
    if spec_dict['smoothing'] is None:
        intensities_smooth = np.empty_like(wavelengths)
    if spec_dict['smoothing'] == 'savgol':
        intensities_smooth = savgol_filter(intensities, 11, 1)

        intensities_smooth = spline_fit(wavelengths)
    else:
        pass
    '''

    # append new data to optical dataframe. first create empty cells to fill.
    spec_dict['optical_df']['wavelength_'+spec_time] = np.repeat('', 9999)
    spec_dict['optical_df']['intensity_'+spec_time] = np.repeat('', 9999)
    # now fill empty cells with new data
    spec_dict['optical_df']['wavelength_'+spec_time].iloc[
                                            :len(wl0)] = wl0.astype(str)
    spec_dict['optical_df']['intensity_'+spec_time].iloc[
                                            :len(wl0)] = int0.astype(str)
    # save optical data to file
    spec_dict['optical_df'].to_csv(spec_dict[
            'save_file_dir']+'/'+spec_dict[
                    'start_date']+'_optical.csv', index=False)

    spec_dict['measure_button'].setEnabled(True)


def plot_optical_spectra(spec_dict):
    # view all optical data in one plot
    # get optical data file
    filename = spec_dict['save_file_dir']+'/'+spec_dict[
            'start_date']+'_optical.csv'
    df = pd.read_csv(filename)
    plt.ion
    # plt.show()
    fig_opt = plt.figure(30)
    fig_opt.clf()
    # loop over each I-V measurement
    for i in range(0, len(df.columns)-1, 2):
        colors = cm.jet(np.linspace(0, 1, len(df.columns)-1))

        plt.plot(df.iloc[:, i].astype(float),
                 df.iloc[:, i+1].astype(float),
                 lw=1,
                 c=colors[int(i/2)],
                 label=str(int(i/2)))
    plt.xlabel('Wavelength', fontsize=fontsize)
    plt.ylabel('Optical intensity', fontsize=fontsize)
    plt.legend()
    fig_opt.canvas.set_window_title(
            'Displaying '+str(int(len(df.columns)/2))+' optical spectra')
    plt.tight_layout()
    plt.draw()


def optical_rh_seq(spec_dict):
    # measure optical spectra prepeatedly during RH sequence
    spec_dict['spec_busy'] = True
    get_spec(spec_dict)
    wait_time = float(spec_dict['set_spec_pause'].value())*60
    time.sleep(wait_time)
    spec_dict['spec_busy'] = False


def optical_vac_seq(spec_dict):
    # measure optical spectra prepeatedly during vacuum sequence
    spec_dict['spec_busy'] = True
    get_spec(spec_dict)
    wait_time = float(spec_dict['set_spec_pause'].value())*60
    time.sleep(wait_time)
    spec_dict['spec_busy'] = False


# TEST SPECTROMETER CONTROL BY RUNNING THIS MODULE
if __name__ == '__main__':

    # open connectino to device
    sm = sb.Spectrometer(sb.list_devices()[0])

    # set measurement integration time in microseconds
    sm.integration_time_micros(1000)
    # set wavelengths in nm
    wavelengths = sm.wavelengths()[10:-185]
    # measure intensities
    intensities = sm.intensities(correct_dark_counts=False,
                                 correct_nonlinearity=False)[10:-185]
    sm.close()

    # plt.scatter(wavelengths, intensities, s=2, c='k', alpha=0.2)
    # plt.show()
