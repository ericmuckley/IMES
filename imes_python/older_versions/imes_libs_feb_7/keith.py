# -*- coding: utf-8 -*-
"""
This module allows communication to a Keithley-2400 series multimeter for
setting up arrays of voltage biases for I-V and C-V measurements and
executing I-V and C-V measurements.

Packages required:
time
numpy
pymeasure
matplotlib
PyQt5
pandas

Created on Tue Jan 15 17:33:40 2019
@author: ericmuckley@gmail.com
"""

from PyQt5 import QtCore  # for multi-threading
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
fontsize = 12


def initialize(device_address):
    '''Set up Keithley device using the GPIB address of the multimeter.
    This can be done using a GPIB-to-USB cable connecting the Keithley
    to the PC and setting the GPIB address on the Keithley front panel.
    Example inputs:
        device_address = 'GPIB::24'
    Returns a device instance.
    '''
    from pymeasure.instruments.keithley import Keithley2400
    dev = Keithley2400(device_address)
    dev.reset()
    dev.use_front_terminals()
    dev.measure_current(current=0.1)  # set current compliance
    return dev


def get_bias_voltages(v_max, v_steps):
    '''Create an array of bias voltages to measure during I-V and
    C-V measurements. v_max is the maximum bias and v_steps are the number
    of voltage steps to measure at between 0 bias and the maximum bias.
    Example inputs:
        v_max = 1
        v_steps = 10
    Returns a two-tuple of arrays: one for I-V and one for C-V measurements.
    '''
    bias_array = np.linspace(0, v_max, num=v_steps)
    biases_iv = np.concatenate((-bias_array[::-1],
                                bias_array[1:]))
    biases_cv = np.concatenate((bias_array,
                                bias_array[::-1][1:],
                                -bias_array[1:],
                                -bias_array[::-1][1:],
                                bias_array[1:],
                                bias_array[::-1][1:]))
    return biases_iv, biases_cv


def measure_bias_sequence(dev, bias_seq):
    '''Apply voltage bias which changes over time and measure
    current continuously over the bias sequence. The sequence
    should be a 2D numpy array where the first column is time
    in minutes and the second column is applied bias.
    Example inputs:
        dev = initialize(device_address)
        sequence = np.array([[2,0],
                             [5,1],
                             [4,0]])
        This example sequence would apply 0V bias for 2 mintes,
        then 1V bias for 5 minutes, then 0V bias for 4 minutes.
    Returns an 2D array with columns containing times, biases,
    and measured currents.
    '''
    step_lengths = bias_seq[:, 0]*60  # step durations in minutes
    step_biases = bias_seq[:, 1]
    # create empty array to hold measured data
    bias_seq_results = np.empty((0, 3))
    seq_start_time = time.time()
    for i in range(len(bias_seq)):
        step_start_time = time.time()
        while time.time() - step_start_time < step_lengths[i]:
            # apply bias and measure current
            apply_bias(dev, step_biases[i])
            current0 = dev.current
            # add results to saved bias array
            bias_seq_results = np.vstack((bias_seq_results,
                                          [time.time() - seq_start_time,
                                           step_biases[i], current0]))
    remove_bias(dev)
    return bias_seq_results


def apply_bias(dev, bias):
    '''Apply constant voltage bias on multimeter.
    Example inputs:
        dev = initialize(device_address)
        bias = 1
    '''
    dev.enable_source()
    dev.source_voltage = bias
    dev.apply_voltage


def remove_bias(dev):
    '''Turn off voltage bias.
    Example inputs:
        dev = initialize(device_address)
    '''
    dev.source_voltage = 0
    dev.disable_source()


def get_current(dev):
    '''Use multimeter to take a single reading of electrical current.
    Example inputs:
        dev = initialize(device_address)
    Returns a single current reading.
    '''
    return dev.current


def get_current_array(dev, bias_array):
    '''Use multimeter to measure current under a range of different
    bias voltages. These bias voltages may come from the output of the
    function "bias_voltages".
    Example inputs:
        dev = initialize(device_address)
        bias_array = [-1, -0.5, 0, 0.5, 1]
    Outputs an array of currents.
    '''
    dev.enable_source()
    current_list = np.empty_like(bias_array)
    # loop through each applied voltage level
    for v0_i, v0 in enumerate(bias_array):
        # apply voltage
        dev.source_voltage = v0
        dev.apply_voltage
        time.sleep(0.1)
        # read current
        current_list[v0_i] = dev.current
    dev.source_voltage = 0
    dev.disable_source()
    return current_list


def close(dev):
    '''Close communication with Keithley multimeter.
    Example inputs:
        dev = initialize(device_address)
    '''
    dev.disable_source()
    dev.shutdown()

# These functions were pulled from GUI window and interact directly with GUI


def checked(keith_dict):
    # This function triggers when Keithley box is checked/unchecked on GUI
    if keith_dict['keithley_on'].isChecked():  # if checkbox was checked
        try:
            keith_dict['keith_dev'] = initialize(
                    keith_dict['keith_address'].text())
            keith_dict['electrical_box'].setEnabled(True)
            keith_dict['menu_electrical'].setEnabled(True)
            keith_dict['keith_address'].setEnabled(False)
            keith_dict['output_box'].append('Keithley connected.')
        except NameError:
                keith_dict['output_box'].append('Keithley could not connect.')
    if not keith_dict['keithley_on'].isChecked():  # if checkbox was unchecked
        try:
            close(keith_dict['keith_dev'])
        except NameError:
            pass
        keith_dict['electrical_box'].setEnabled(False)
        keith_dict['menu_electrical'].setEnabled(False)
        keith_dict['keith_address'].setEnabled(True)
        keith_dict['output_box'].append('Keithley disconnected.')


def print_iv_biases(keith_dict):
    # Print biases for I-V measurements in the output box
    iv_biases, _ = get_bias_voltages(keith_dict['max_bias'].value(),
                                     keith_dict['voltage_steps'].value())
    keith_dict['output_box'].append('IV biases = '+format(iv_biases))
    plt.ion
    fig_iv_b = plt.figure(3)
    fig_iv_b.clf()
    plt.plot(np.arange(len(iv_biases))+1, iv_biases,
             c='k', lw=1, marker='o', markersize=5)
    plt.xlabel('Point number', fontsize=fontsize)
    plt.ylabel('Bias (V)', fontsize=fontsize)
    fig_iv_b.canvas.set_window_title('Biases for I-V measurements')
    plt.tight_layout()
    plt.draw()


def print_cv_biases(keith_dict):
    # Print biases for C-V measurements in the output box
    _, cv_biases = get_bias_voltages(keith_dict['max_bias'].value(),
                                     keith_dict['voltage_steps'].value())
    keith_dict['output_box'].append('CV biases = '+format(cv_biases))
    plt.ion
    fig_cv_b = plt.figure(4)
    fig_cv_b.clf()
    plt.plot(np.arange(len(cv_biases))+1, cv_biases,
             c='k', lw=1, marker='o', markersize=5)
    plt.xlabel('Point number', fontsize=fontsize)
    plt.ylabel('Bias (V)', fontsize=fontsize)
    fig_cv_b.canvas.set_window_title('Biases for C-V measurements')
    plt.tight_layout()
    plt.draw()


def get_current_continuously(keith_dict, df, df_i):
    # Measure current continuously using Keithley multimeter.
    if keith_dict['measure_current_now'].isChecked():  # if current started
        keith_dict['measure_iv_now'].setEnabled(False)
        keith_dict['measure_cv_now'].setEnabled(False)
        keith_dict['keithley_busy'] = True

        apply_bias(keith_dict['keith_dev'],
                   keith_dict['set_bias'].value())

        current0 = get_current(keith_dict['keith_dev'])
        # save results to file
        df['bias'].iloc[df_i] = str(keith_dict['set_bias'].value())
        df['current'].iloc[df_i] = str(current0)

        keith_dict['current_display'].setText(
                str(np.round(current0, decimals=11)))

        if df_i % 3 == 0:
            QtCore.QCoreApplication.processEvents()  # handle threading

            # plot current over time
            plt.ion
            fig_current = plt.figure(5)
            fig_current.clf()
            df_current = df[df['current'] != '']
            plt.plot(pd.to_numeric(df_current['time']),
                     pd.to_numeric(df_current['current']),
                     c='r', lw=1)
            plt.xlabel('Elapsed time (min)', fontsize=fontsize)
            plt.ylabel('Current (A)', fontsize=fontsize)
            fig_current.canvas.set_window_title('Sample current')
            plt.tight_layout()
            plt.draw()

    if not keith_dict['measure_current_now'].isChecked():  # if current stopped
        remove_bias(keith_dict['keith_dev'])
        keith_dict['measure_iv_now'].setEnabled(True)
        keith_dict['measure_cv_now'].setEnabled(True)
        keith_dict['output_box'].append(
                'Current measurement stopped.')
        keith_dict['keithley_busy'] = False


def measure_iv(keith_dict):
    # Measure I-V curve
    keith_dict['measure_iv_now'].setEnabled(False)
    keith_dict['measure_cv_now'].setEnabled(False)
    keith_dict['keithley_busy'] = True
    iv_biases, _ = get_bias_voltages(keith_dict['max_bias'].value(),
                                     keith_dict['voltage_steps'].value())
    current_list = np.empty_like(iv_biases)
    keith_dict['output_box'].append('Measuring I-V...')
    iv_time = time.ctime()

    # loop through each applied voltage level
    for v_i, v0 in enumerate(iv_biases):
        QtCore.QCoreApplication.processEvents()  # handle threading
        # apply voltage
        apply_bias(keith_dict['keith_dev'], v0)
        # read current
        current_list[v_i] = get_current(keith_dict['keith_dev'])
        keith_dict['current_display'].setText(
                str(np.round(current_list[v_i], decimals=11)))
        if v_i % 5 == 0:
            # plot results over time
            plt.ion
            fig_iv = plt.figure(17)
            fig_iv.clf()
            plt.plot(iv_biases[:v_i], current_list[:v_i], c='k', lw=1)
            plt.xlabel('Bias V)', fontsize=fontsize)
            plt.ylabel('Current (A)', fontsize=fontsize)
            fig_iv.canvas.set_window_title('I-V measurement')
            plt.tight_layout()
            plt.draw()

    keith_dict['output_box'].append('I-V measurement complete.')
    remove_bias(keith_dict['keith_dev'])
    keith_dict['keithley_busy'] = False

    keith_dict['measure_iv_now'].setEnabled(True)
    keith_dict['measure_cv_now'].setEnabled(True)
    keith_dict['output_box'].append(
                'I-V measurement stopped.')

    # append new data to I-V dataframe. first create empty cells to fill.
    # this is done so I-V curves with different lengths can be appended
    keith_dict['iv_df']['bias_'+iv_time] = np.repeat('', 99)
    keith_dict['iv_df']['current_'+iv_time] = np.repeat('', 99)
    # now fill empty cells with new data
    keith_dict['iv_df']['bias_'+iv_time].iloc[
                                    :len(iv_biases)] = iv_biases.astype(str)
    keith_dict['iv_df']['current_'+iv_time].iloc[
                                    :len(iv_biases)] = current_list.astype(str)
    # save I-V data to file
    keith_dict['iv_df'].to_csv(
            keith_dict['save_file_dir']+'/'+keith_dict[
                                        'start_date']+'_iv.csv', index=False)


def measure_cv(keith_dict):
    # Measure C-V curve
    keith_dict['measure_iv_now'].setEnabled(False)
    keith_dict['measure_cv_now'].setEnabled(False)
    keith_dict['keithley_busy'] = True
    _, cv_biases = get_bias_voltages(keith_dict['max_bias'].value(),
                                     keith_dict['voltage_steps'].value())
    current_list = np.empty_like(cv_biases)
    keith_dict['output_box'].append('Measuring C-V...')
    iv_time = time.ctime()

    # loop through each applied voltage level
    for v_i, v0 in enumerate(cv_biases):
        QtCore.QCoreApplication.processEvents()  # handle threading
        # apply voltage
        apply_bias(keith_dict['keith_dev'], v0)
        # read current
        current_list[v_i] = get_current(keith_dict['keith_dev'])
        keith_dict['current_display'].setText(
                str(np.round(current_list[v_i], decimals=11)))
        if v_i % 5 == 0:
            # plot results over time
            plt.ion
            fig_cv = plt.figure(7)
            fig_cv.clf()
            plt.plot(cv_biases[:v_i], current_list[:v_i], c='k', lw=1)
            plt.xlabel('Bias V)', fontsize=fontsize)
            plt.ylabel('Current (A)', fontsize=fontsize)
            fig_cv.canvas.set_window_title('C-V measurement')
            plt.tight_layout()
            plt.draw()

    keith_dict['output_box'].append('C-V measurement complete.')
    remove_bias(keith_dict['keith_dev'])
    keith_dict['keithley_busy'] = False

    keith_dict['measure_iv_now'].setEnabled(True)
    keith_dict['measure_cv_now'].setEnabled(True)
    keith_dict['output_box'].append(
                'C-V measurement stopped.')

    # append new data to C-V dataframe. first create empty cells to fill.
    # this is done so C-V curves with different lengths can be appended
    keith_dict['cv_df']['bias_'+iv_time] = np.repeat('', 1000)
    keith_dict['cv_df']['current_'+iv_time] = np.repeat('', 1000)
    # now fill empty cells with new data
    keith_dict['cv_df']['bias_'+iv_time].iloc[
                                    :len(cv_biases)] = cv_biases.astype(str)
    keith_dict['cv_df']['current_'+iv_time].iloc[
                                    :len(cv_biases)] = current_list.astype(str)
    # save C-V data to file
    keith_dict['cv_df'].to_csv(
            keith_dict['save_file_dir']+'/'+keith_dict[
                                        'start_date']+'_cv.csv', index=False)


def bias_table_to_df(keith_dict):
    # convert bias sequence table on GUI to pandas dataframe
    # create empty dataframe
    bias_df = pd.DataFrame(
            columns=['time', 'bias'],
            index=range(keith_dict['bias_seq_table'].rowCount()))

    # populate dataframe
    for rowi in range(keith_dict['bias_seq_table'].rowCount()):
        for colj in range(keith_dict['bias_seq_table'].columnCount()):
            new_entry = keith_dict['bias_seq_table'].item(rowi, colj).text()
            bias_df.iloc[rowi, colj] = new_entry
    # delete empty rows
    bias_df = bias_df[bias_df['time'] != '0'].astype(float)
    return bias_df


def plot_bias_seq(keith_dict):
    # plot the bias sequence
    try:  # retrieve the sequence from the GUI bias table
        bias_seq = bias_table_to_df(keith_dict).values
        seq_time = bias_seq[:, 0]
        plot_seq_time = np.insert(np.cumsum(seq_time), 0, 0)
        seq_bias = bias_seq[:, 1]
        plot_seq_bias = np.insert(seq_bias, 0, seq_bias[0])
        fig_seq = plt.figure(9)
        plt.cla()
        plt.ion()
        plt.plot(plot_seq_time, plot_seq_bias,
                 c='r', drawstyle='steps', alpha=1)
        plt.xlabel('Time (min)', fontsize=fontsize)
        plt.ylabel('Bias (V)', fontsize=fontsize)
        plt.tight_layout()
        fig_seq.canvas.set_window_title('Bias sequence')
        fig_seq.show()
    except NameError:
        keith_dict['output_box'].append('Bias sequence not valid.')


def view_iv_data(keith_dict):
    # view all I-V data in one plot
    # get IV data file
    iv_file = keith_dict['save_file_dir']+'/'+keith_dict[
            'start_date']+'_iv.csv'
    iv_data = pd.read_csv(iv_file)
    plt.ion
    fig_ivb = plt.figure(30)
    fig_ivb.clf()
    # loop over each I-V measurement
    for i in range(0, len(iv_data.columns)-1, 2):
        plt.plot(iv_data.iloc[:, i].astype(float),
                 iv_data.iloc[:, i+1].astype(float))
    plt.xlabel('Bias V)', fontsize=fontsize)
    plt.ylabel('Current (A)', fontsize=fontsize)
    fig_ivb.canvas.set_window_title(
            'Displaying '+str(len(iv_data.columns)/2)+' I-V measurements',
            fontsize=fontsize)
    plt.tight_layout()
    plt.draw()


def view_cv_data(keith_dict):
    # view all C-V data in one plot
    cv_file = keith_dict['save_file_dir']+'/'+keith_dict[
            'start_date']+'_cv.csv'
    cv_data = pd.read_csv(cv_file)
    plt.ion
    fig_cvb = plt.figure(31)
    fig_cvb.clf()
    # loop over each I-V measurement
    for i in range(0, len(cv_data.columns)-1, 2):
        plt.plot(cv_data.iloc[:, i].astype(float),
                 cv_data.iloc[:, i+1].astype(float))
    plt.xlabel('Bias V)', fontsize=fontsize)
    plt.ylabel('Current (A)', fontsize=fontsize)
    fig_cvb.canvas.set_window_title(
            'Displaying '+str(len(cv_data.columns)/2)+' C-V measurements')
    plt.tight_layout()
    plt.draw()


def view_bs_data(keith_dict):
    # view all bias-sequence data in one plot
    # get BS data file
    bs_file = keith_dict['save_file_dir']+'/'+keith_dict[
            'start_date']+'_bs.csv'
    bs_data = pd.read_csv(bs_file)
    plt.ion
    fig_bsd = plt.figure(32)
    fig_bsd.clf()
    # loop over each I-V measurement
    for i in range(0, len(bs_data.columns)-1, 3):
        plt.plot(bs_data.iloc[:, i].astype(float),
                 bs_data.iloc[:, i+2].astype(float))
    plt.xlabel('Time (min)', fontsize=fontsize)
    plt.ylabel('Current (A)', fontsize=fontsize)
    fig_bsd.canvas.set_window_title(
            'Displaying '+str(len(bs_data.columns)/2)+' bias sequences',
            fontsize=fontsize)
    plt.tight_layout()
    plt.draw()


def measure_bias_seq(keith_dict):
    # Measure current over time using Keithley multimeter and
    # a sequence of changing voltage biases according to times
    # listed on the bias table on GUI.
    bias_seq = bias_table_to_df(keith_dict).values
    # step durations in minutes
    step_lengths = bias_seq[:, 0]*60
    step_biases = bias_seq[:, 1]

    keith_dict['measure_iv_now'].setEnabled(False)
    keith_dict['measure_cv_now'].setEnabled(False)
    keith_dict['output_box'].append('Measuring bias sequence...')
    keith_dict['keithley_busy'] = True
    # create empty array to hold measured data
    bs_results = np.empty((0, 3))
    bs_time = time.ctime()
    bs_start_time = time.time()

    for i in range(len(bias_seq)):
        step_start_time = time.time()

        while time.time() - step_start_time < step_lengths[i]:
            QtCore.QCoreApplication.processEvents()  # handle threading

            # apply bias and measure current
            apply_bias(keith_dict['keith_dev'], step_biases[i])
            current0 = get_current(keith_dict['keith_dev'])
            keith_dict['current_display'].setText(
                    str(np.round(current0, decimals=11)))

            # make new row of data to append
            new_row = [(time.time() - bs_start_time)/60,
                       step_biases[i],
                       current0]
            # add results to saved bias array
            bs_results = np.vstack((bs_results, new_row))

            # plot the bias over time
            plt.ion
            fig_bs = plt.figure(6)
            fig_bs.clf()
            plt.plot(bs_results[:, 0], bs_results[:, 2], c='k', lw=1)
            plt.xlabel('Elapsed time (min)', fontsize=fontsize)
            plt.ylabel('Current (A)', fontsize=fontsize)
            fig_bs.canvas.set_window_title('Current during bias sequence')
            plt.tight_layout()
            plt.draw()

    remove_bias(keith_dict['keith_dev'])
    keith_dict['output_box'].append('Bias sequence complete.')
    keith_dict['keithley_busy'] = False
    keith_dict['measure_iv_now'].setEnabled(True)
    keith_dict['measure_cv_now'].setEnabled(True)
    # append new data to bias seq dataframe. #first create empty cells to
    # fill so bias sequences with different lengths can be appended
    keith_dict['bs_df']['time_'+bs_time] = np.repeat('', 10000)
    keith_dict['bs_df']['bias_'+bs_time] = np.repeat('', 10000)
    keith_dict['bs_df']['current_'+bs_time] = np.repeat('', 10000)
    # now fill empty cells with new data
    keith_dict['bs_df']['time_'+bs_time].iloc[
            :(len(bs_results))] = bs_results[:, 0].astype(str)
    keith_dict['bs_df']['bias_'+bs_time].iloc[
            :(len(bs_results))] = bs_results[:, 1].astype(str)
    keith_dict['bs_df']['current_'+bs_time].iloc[
            :(len(bs_results))] = bs_results[:, 2].astype(str)
    # save bias seq data to file
    keith_dict['bs_df'].to_csv(
            keith_dict['save_file_dir']+'/'+keith_dict[
                    'start_date']+'_bs.csv', index=False)


'''
# this function measures a bias sequence based on points per step,
not time per step.

def measure_bias_seq(keith_dict):
        # Measure current over time using Keithley multimeter.
        # Voltage bias is applied over time according to bias table on GUI.
        # retrieve the sequence from the GUI bias table
        bs_array = bias_table_to_df(keith_dict).values
        bs_biases = np.repeat(bs_array[:, 1], bs_array[:, 0].astype(int))

        keith_dict['measure_iv_now'].setEnabled(False)
        keith_dict['measure_cv_now'].setEnabled(False)
        keith_dict['output_box'].append('Measuring bias sequence...')
        # create empty array to hold measured data
        bs_results = np.empty((0, 3))
        keith_dict['keithley_busy'] = True
        bs_time = time.ctime()
        bs_start_time = time.time()

        for bs_i, bs_v0 in enumerate(bs_biases):
            QtCore.QCoreApplication.processEvents()  # handle threading
            # apply bias and measure current
            apply_bias(keith_dict['keith_dev'], bs_v0)
            current0 = get_current(keith_dict['keith_dev'])
            keith_dict['current_display'].setText(
                    str(np.round(current0, decimals=11)))
            # add results to saved bias array
            bs_results = np.vstack((bs_results,
                                    [(time.time() - bs_start_time)/60,
                                     bs_v0, current0]))
            # plot the bias over time
            plt.ion
            fig_bs = plt.figure(6, figsize=(4, 3))
            fig_bs.clf()
            plt.plot(bs_results[:, 0], bs_results[:, 2], c='k', lw=1)
            plt.xlabel('Elapsed time (min)', fontsize=fontsize)
            plt.ylabel('Current (A)', fontsize=fontsize)
            fig_bs.canvas.set_window_title('Current during bias sequence')
            plt.tight_layout()
            plt.draw()

        remove_bias(keith_dict['keith_dev'])
        keith_dict['output_box'].append('Bias sequence complete.')
        keith_dict['keithley_busy'] = False
        keith_dict['measure_iv_now'].setEnabled(True)
        keith_dict['measure_cv_now'].setEnabled(True)
        # append new data to bias seq dataframe. #first create empty cells to
        # fill so bias sequences with different lengths can be appended
        keith_dict['bs_df']['time_'+bs_time] = np.repeat('', 10000)
        keith_dict['bs_df']['bias_'+bs_time] = np.repeat('', 10000)
        keith_dict['bs_df']['current_'+bs_time] = np.repeat('', 10000)
        # now fill empty cells with new data
        keith_dict['bs_df']['time_'+bs_time].iloc[
                :(len(bs_results))] = bs_results[:, 0].astype(str)
        keith_dict['bs_df']['bias_'+bs_time].iloc[
                :(len(bs_results))] = bs_results[:, 1].astype(str)
        keith_dict['bs_df']['current_'+bs_time].iloc[
                :(len(bs_results))] = bs_results[:, 2].astype(str)
        # save bias seq data to file
        keith_dict['bs_df'].to_csv(
                keith_dict['save_file_dir']+'/'+keith_dict[
                        'start_date']+'_bs.csv', index=False)

'''
