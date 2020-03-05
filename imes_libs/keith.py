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
# from PyQt5.QtWidgets import QMainWindow, QFileDialog
# from PyQt5.QtCore import QThreadPool, pyqtSignal, QRunnable

import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from pymeasure.instruments.keithley import Keithley2400
fontsize = 12


def initialize(device_address):
    '''Set up Keithley device using the GPIB address of the multimeter.
    This can be done using a GPIB-to-USB cable connecting the Keithley
    to the PC and setting the GPIB address on the Keithley front panel.
    Example inputs:
        device_address = 'GPIB::24'
    Returns a device instance.
    '''
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


def apply_bias(dev, bias):
    # Apply constant voltage bias on multimeter, with bias in volts.
    dev.enable_source()
    dev.source_voltage = bias
    dev.apply_voltage


def remove_bias(keith_dict):
    # Turn off voltage bias.
    keith_dict['keith_dev'].source_voltage = 0
    keith_dict['keith_dev'].disable_source()
    keith_dict['actual_bias'].setText('0')
    keith_dict['current_display'].setText('--')


def get_current(dev):
    # Use multimeter (dev=initialize(device_address)to get current.
    return dev.current


def close(dev):
    # Close communication with multimeter (dev=initialize(device_address))
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
        except:
            keith_dict['output_box'].append('Keithley could not connect.')
            keith_dict['output_box'].append('Try checking address and cable.')
            keith_dict['keithley_on'].setChecked(False)

    if not keith_dict['keithley_on'].isChecked():  # if checkbox was unchecked
        keith_dict['keithley_on'].setChecked(False)
        try:
            close(keith_dict['keith_dev'])
        except:
            pass
        keith_dict['electrical_box'].setEnabled(False)
        keith_dict['menu_electrical'].setEnabled(False)
        keith_dict['keith_address'].setEnabled(True)
        keith_dict['output_box'].append('Keithley disconnected.')


def print_iv_biases(keith_dict):
    # Print biases for I-V measurements in the output box
    iv_biases, _ = get_bias_voltages(float(keith_dict['max_bias'].value()),
                                     int(keith_dict['voltage_steps'].value()))
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
    _, cv_biases = get_bias_voltages(float(keith_dict['max_bias'].value()),
                                     int(keith_dict['voltage_steps'].value()))
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
        keith_dict['measure_bias_seq_now'].setEnabled(False)
        keith_dict['keith_busy'] = True

        bias = float(keith_dict['set_bias'].value())
        apply_bias(keith_dict['keith_dev'], bias)

        current0 = get_current(keith_dict['keith_dev'])
        # save results to file
        df['bias'].iloc[df_i] = str(bias)
        df['current'].iloc[df_i] = str(current0)
        # display on GUI
        keith_dict['actual_bias'].setText(
                str(np.round(bias, decimals=8)))
        keith_dict['current_display'].setText(
                str(np.round(current0, decimals=11)))

    if not keith_dict['measure_current_now'].isChecked():  # if current stopped
        remove_bias(keith_dict)
        keith_dict['actual_bias'].setText('0')
        keith_dict['current_display'].setText('--')
        keith_dict['measure_iv_now'].setEnabled(True)
        keith_dict['measure_cv_now'].setEnabled(True)
        keith_dict['measure_bias_seq_now'].setEnabled(True)
        keith_dict['output_box'].append(
                'Current measurement stopped.')
        keith_dict['keith_busy'] = False
        plt.close()


def plot_current(df):
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


def measure_iv(keith_dict, df, df_i):
    # Measure I-V curve
    keith_dict['measure_iv_now'].setEnabled(False)
    keith_dict['measure_cv_now'].setEnabled(False)
    keith_dict['measure_current_now'].setEnabled(False)
    keith_dict['measure_bias_seq_now'].setEnabled(False)
    keith_dict['set_bias'].setEnabled(False)
    keith_dict['max_bias'].setEnabled(False)
    keith_dict['voltage_steps'].setEnabled(False)
    keith_dict['keith_busy'] = True
    iv_biases, _ = get_bias_voltages(float(keith_dict['max_bias'].value()),
                                     int(keith_dict['voltage_steps'].value()))
    current_list = np.empty_like(iv_biases)
    keith_dict['output_box'].append('Measuring I-V...')
    iv_time = time.strftime('%Y-%m-%d_%H-%M-%S_')
    keith_dict['new_data'] = None
    # loop through each applied voltage level
    for v_i, v0 in enumerate(iv_biases):
        # apply voltage
        apply_bias(keith_dict['keith_dev'], v0)
        time.sleep(0.2)
        # read current
        current_list[v_i] = get_current(keith_dict['keith_dev'])

        keith_dict['new_data'] = np.column_stack(
                (iv_biases, current_list))[:v_i]
        keith_dict['actual_bias'].setText(str(np.round(v0, decimals=8)))
        keith_dict['current_display'].setText(
                str(np.round(current_list[v_i], decimals=11)))

    remove_bias(keith_dict)
    keith_dict['actual_bias'].setText('0')
    keith_dict['current_display'].setText('--')

    keith_dict['output_box'].append('I-V measurement complete.')
    keith_dict['measure_iv_now'].setEnabled(True)
    keith_dict['measure_cv_now'].setEnabled(True)
    keith_dict['set_bias'].setEnabled(True)
    keith_dict['max_bias'].setEnabled(True)
    keith_dict['voltage_steps'].setEnabled(True)
    keith_dict['measure_bias_seq_now'].setEnabled(True)
    keith_dict['measure_current_now'].setEnabled(True)
    keith_dict['new_data'] = None
    # append new data to I-V dataframe. first create empty cells to fill.
    # this is done so I-V curves with different lengths can be appended
    keith_dict['iv_df']['bias_'+iv_time] = np.repeat('', 999)
    keith_dict['iv_df']['current_'+iv_time] = np.repeat('', 999)
    # now fill empty cells with new data
    keith_dict['iv_df']['bias_'+iv_time].iloc[
                                    :len(iv_biases)] = iv_biases.astype(str)
    keith_dict['iv_df']['current_'+iv_time].iloc[
                                    :len(iv_biases)] = current_list.astype(str)
    # save I-V data to file
    keith_dict['iv_df'].to_csv(
            keith_dict['save_file_dir']+'/'+keith_dict[
                                        'start_date']+'_iv.csv', index=False)
    # save max current to main df
    max_current = np.amax(current_list)
    df['max_iv_current'].iloc[df_i] = str(max_current)
    if keith_dict['keith_seq_running'] is True:
        pass
    else:
        keith_dict['keith_busy'] = False
    # view_iv_data(keith_dict)
    # plt.pause(2)
    # plt.close()


def measure_cv(keith_dict, df, df_i):
    # Measure C-V curve
    keith_dict['measure_iv_now'].setEnabled(False)
    keith_dict['measure_cv_now'].setEnabled(False)
    keith_dict['measure_current_now'].setEnabled(False)
    keith_dict['measure_bias_seq_now'].setEnabled(False)
    keith_dict['set_bias'].setEnabled(False)
    keith_dict['max_bias'].setEnabled(False)
    keith_dict['voltage_steps'].setEnabled(False)
    keith_dict['keith_busy'] = True
    keith_dict['new_data'] = None
    _, cv_biases = get_bias_voltages(float(keith_dict['max_bias'].value()),
                                     int(keith_dict['voltage_steps'].value()))
    current_list = np.empty_like(cv_biases)
    keith_dict['output_box'].append('Measuring C-V...')
    iv_time = time.strftime('%Y-%m-%d_%H-%M-%S_')

    # loop through each applied voltage level
    for v_i, v0 in enumerate(cv_biases):
        # apply voltage
        apply_bias(keith_dict['keith_dev'], v0)
        time.sleep(0.2)
        # read current
        current_list[v_i] = get_current(keith_dict['keith_dev'])
        keith_dict['actual_bias'].setText(str(np.round(v0, decimals=8)))
        keith_dict['current_display'].setText(
                str(np.round(current_list[v_i], decimals=11)))
    keith_dict['output_box'].append('C-V measurement complete.')
    remove_bias(keith_dict)
    keith_dict['actual_bias'].setText('0')
    keith_dict['current_display'].setText('--')
    keith_dict['measure_iv_now'].setEnabled(True)
    keith_dict['measure_cv_now'].setEnabled(True)
    keith_dict['set_bias'].setEnabled(True)
    keith_dict['max_bias'].setEnabled(True)
    keith_dict['voltage_steps'].setEnabled(True)
    keith_dict['measure_current_now'].setEnabled(True)
    keith_dict['measure_bias_seq_now'].setEnabled(True)
    keith_dict['new_data'] = None
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

    # save capacitance to main df
    capacitance, max_cv_current = get_capacitance(cv_biases, current_list)
    df['cv_area'].iloc[df_i] = str(capacitance)
    df['max_cv_current'].iloc[df_i] = str(max_cv_current)
    if keith_dict['keith_seq_running'] is True:
        pass
    else:
        keith_dict['keith_busy'] = False


def get_sweep_rates(keith_dict):
    # get the designated C-V sweep rates from GUI
    rates_string = keith_dict['cv_sweep_rates'].text()
    rates_list_string = rates_string.split(',')
    rates_list = [float(rate) for rate in rates_list_string]
    return rates_list


def measure_multi_cv(keith_dict, df, df_i):
    # Measure C-V curve
    keith_dict['measure_iv_now'].setEnabled(False)
    keith_dict['measure_cv_now'].setEnabled(False)
    keith_dict['measure_current_now'].setEnabled(False)
    keith_dict['measure_bias_seq_now'].setEnabled(False)
    keith_dict['set_bias'].setEnabled(False)
    keith_dict['max_bias'].setEnabled(False)
    keith_dict['voltage_steps'].setEnabled(False)
    keith_dict['keith_busy'] = True
    _, cv_biases = get_bias_voltages(float(keith_dict['max_bias'].value()),
                                     int(keith_dict['voltage_steps'].value()))
    keith_dict['output_box'].append('Measuring C-V...')
    iv_time = time.strftime('%Y-%m-%d_%H-%M-%S_')
    # get sweep rates
    rates_list = get_sweep_rates(keith_dict)
    # calculate appropriate delays per point to result in the sweep rates
    delta_v = cv_biases[1] - cv_biases[0]
    delays = [delta_v / rate for rate in rates_list]
    # append new data to C-V dataframe. first create empty cells to fill.
    # this is done so C-V curves with different lengths can be appended
    keith_dict['cv_df']['bias_'+iv_time] = np.repeat('', 1000)
    # now fill empty cells with new data
    keith_dict['cv_df']['bias_'+iv_time].iloc[
                                    :len(cv_biases)] = cv_biases.astype(str)
    keith_dict['new_data'] = None
    # loop through each sweep rate
    for delay_i, delay0 in enumerate(delays):
        rate0 = rates_list[delay_i]
        save_rate = '_'+str(np.round(rate0, decimals=3))+'V/s_'
        current_list = np.zeros_like(cv_biases)
        # loop through each applied voltage level
        for v_i, v0 in enumerate(cv_biases):
            # apply voltage
            apply_bias(keith_dict['keith_dev'], v0)
            time.sleep(delay0)
            # read current
            current_list[v_i] = get_current(keith_dict['keith_dev'])
            keith_dict['actual_bias'].setText(str(np.round(v0, decimals=8)))
            keith_dict['current_display'].setText(
                    str(np.round(current_list[v_i], decimals=11)))

            keith_dict['new_data'] = np.column_stack(
                    (cv_biases, current_list))[:v_i]

        # append new data to C-V dataframe. first create empty cells to fill.
        # this is done so C-V curves with different lengths can be appended
        keith_dict['cv_df']['current_'+save_rate+iv_time] = np.repeat('', 1000)
        keith_dict['cv_df']['current_'+save_rate+iv_time].iloc[
                :len(cv_biases)] = current_list.astype(str)
    # save C-V data to file
    keith_dict['cv_df'].to_csv(
            keith_dict['save_file_dir']+'/'+keith_dict[
                                        'start_date']+'_cv.csv', index=False)
    # save capacitance to main df
    capacitance, max_cv_current = get_capacitance(cv_biases, current_list)
    df['cv_area'].iloc[df_i] = str(capacitance)
    df['max_cv_current'].iloc[df_i] = str(max_cv_current)
    keith_dict['output_box'].append('C-V measurement complete.')
    remove_bias(keith_dict)
    keith_dict['actual_bias'].setText('0')
    keith_dict['current_display'].setText('--')
    keith_dict['measure_iv_now'].setEnabled(True)
    keith_dict['measure_cv_now'].setEnabled(True)
    keith_dict['set_bias'].setEnabled(True)
    keith_dict['max_bias'].setEnabled(True)
    keith_dict['voltage_steps'].setEnabled(True)
    keith_dict['measure_current_now'].setEnabled(True)
    keith_dict['measure_bias_seq_now'].setEnabled(True)
    keith_dict['new_data'] = None
    if keith_dict['keith_seq_running'] is True:
        pass
    else:
        keith_dict['keith_busy'] = False


def get_capacitance(biases, currents):
    # calculate capacitance from C-V measurement
    # trim biases to only include a single C-V loop
    start_i = np.argmax(biases)
    end_i = np.argmax(biases[np.arange(len(biases)) != np.argmax(biases)]) + 1
    bias_loop = biases[start_i:end_i]
    current_loop = currents[start_i:end_i]
    # calculate integral (area) of C-V current loop
    tot_area = np.trapz(current_loop, x=bias_loop)
    capacitance = tot_area
    max_cv_current = np.amax(current_loop)
    return capacitance, max_cv_current


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
    # plt.show()
    fig_ivb = plt.figure(30)
    fig_ivb.clf()
    # loop over each I-V measurement
    for i in range(0, len(iv_data.columns)-1, 2):
        colors = cm.jet(np.linspace(0, 1, len(iv_data.columns)-1))

        plt.plot(iv_data.iloc[:, i].astype(float),
                 iv_data.iloc[:, i+1].astype(float)*1e9,
                 c=colors[int(i/2)],
                 label=str(int(i/2)))
    plt.xlabel('Bias V)', fontsize=fontsize)
    plt.ylabel('Current (nA)', fontsize=fontsize)
    plt.legend()
    fig_ivb.canvas.set_window_title(
            'Displaying '+str(int(len(iv_data.columns)/2))+' I-V measurements')
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
    # loop over each C-V measurement
    for i in range(0, len(cv_data.columns)-1, 2):
        colors = cm.jet(np.linspace(0, 1, len(cv_data.columns)-1))
        plt.plot(cv_data.iloc[:, i].astype(float),
                 cv_data.iloc[:, i+1].astype(float),
                 c=colors[int(i/2)],
                 label=str(int(i/2)))
    plt.xlabel('Bias (V)', fontsize=fontsize)
    plt.ylabel('Current (A)', fontsize=fontsize)
    plt.legend()
    fig_cvb.canvas.set_window_title(
            'Displaying '+str(int(len(cv_data.columns)/2))+' C-V measurements')
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
        colors = cm.jet(np.linspace(0, 1, len(bs_data.columns)-1))

        plt.plot(bs_data.iloc[:, i].astype(float),
                 bs_data.iloc[:, i+2].astype(float),
                 c=colors[int(i/3)],
                 label=str(int(i/3)))
    plt.xlabel('Time (min)', fontsize=fontsize)
    plt.ylabel('Current (A)', fontsize=fontsize)
    plt.legend()
    fig_bsd.canvas.set_window_title(
            'Displaying '+str(int(len(bs_data.columns)/2))+' bias sequences')
    plt.tight_layout()
    plt.draw()


def iv_max_vs_time(keith_dict, df, df_i):
    # plot I-V maximum current vs time
    plt.ion
    fig_current = plt.figure(60)
    fig_current.clf()
    df_current = df[df['max_iv_current'] != '']
    plt.plot(pd.to_numeric(df_current['time']),
             pd.to_numeric(df_current['max_iv_current']),
             c='r', lw=1)
    plt.xlabel('Elapsed time (min)', fontsize=fontsize)
    plt.ylabel('Max. I-V current (A)', fontsize=fontsize)
    fig_current.canvas.set_window_title('Max. I-V current')
    plt.tight_layout()
    plt.draw()


def cv_max_vs_time(keith_dict, df, df_i):
    # plot I-V maximum current vs time
    plt.ion
    fig_current = plt.figure(60)
    fig_current.clf()
    df_current = df[df['max_cv_current'] != '']
    plt.plot(pd.to_numeric(df_current['time']),
             pd.to_numeric(df_current['max_cv_current']),
             c='r', lw=1)
    plt.xlabel('Elapsed time (min)', fontsize=fontsize)
    plt.ylabel('Max. C-V current (A)', fontsize=fontsize)
    fig_current.canvas.set_window_title('Max. C-V current')
    plt.tight_layout()
    plt.draw()


def cv_area_vs_time(keith_dict, df, df_i):
    # plot I-V maximum current vs time
    plt.ion
    fig_current = plt.figure(60)
    fig_current.clf()
    df_current = df[df['cv_area'] != '']
    plt.plot(pd.to_numeric(df_current['time']),
             pd.to_numeric(df_current['cv_area']),
             c='r', lw=1)
    plt.xlabel('Elapsed time (min)', fontsize=fontsize)
    plt.ylabel('C-V area (V A)', fontsize=fontsize)
    fig_current.canvas.set_window_title('C-V area')
    plt.tight_layout()
    plt.draw()


def measure_bias_seq(keith_dict, df, df_i):
    # Measure current over time using Keithley multimeter and
    # a sequence of changing voltage biases according to times
    # listed on the bias table on GUI.
    bias_seq = bias_table_to_df(keith_dict).values
    # step durations in minutes
    step_lengths = bias_seq[:, 0]*60
    step_biases = bias_seq[:, 1]
    keith_dict['output_box'].append('Measuring bias sequence...')
    keith_dict['measure_iv_now'].setEnabled(False)
    keith_dict['measure_cv_now'].setEnabled(False)
    keith_dict['measure_current_now'].setEnabled(False)
    keith_dict['set_bias'].setEnabled(False)
    keith_dict['max_bias'].setEnabled(False)
    keith_dict['voltage_steps'].setEnabled(False)
    keith_dict['keith_busy'] = True
    # create empty array to hold measured data
    bs_results = np.empty((0, 3))
    bs_time = time.strftime('%Y-%m-%d_%H-%M-%S_')
    bs_start_time = time.time()

    for i in range(len(bias_seq)):
        step_start_time = time.time()

        while time.time() - step_start_time < step_lengths[i]:
            # apply bias and measure current
            apply_bias(keith_dict['keith_dev'], step_biases[i])
            time.sleep(0.2)
            current0 = get_current(keith_dict['keith_dev'])

            keith_dict['actual_bias'].setText(
                    str(np.round(step_biases[i], decimals=8)))
            keith_dict['current_display'].setText(
                    str(np.round(current0, decimals=11)))

            # make new row of data to append
            new_row = [(time.time() - bs_start_time)/60,
                       step_biases[i],
                       current0]
            # add results to saved bias array
            bs_results = np.vstack((bs_results, new_row))

    remove_bias(keith_dict)
    keith_dict['actual_bias'].setText('0')
    keith_dict['current_display'].setText('--')
    keith_dict['output_box'].append('Bias sequence complete.')
    keith_dict['measure_iv_now'].setEnabled(True)
    keith_dict['measure_cv_now'].setEnabled(True)
    keith_dict['measure_current_now'].setEnabled(True)
    keith_dict['set_bias'].setEnabled(True)
    keith_dict['max_bias'].setEnabled(True)
    keith_dict['voltage_steps'].setEnabled(True)
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
    if keith_dict['keith_seq_running'] is True:
        pass
    else:
        keith_dict['keith_busy'] = False
    # view_bs_data(keith_dict)
    # plt.pause(2)
    # plt.close()


def keith_rh_seq(keith_dict, df, df_i):
    # measure keithley functions during RH sequence
    keith_dict['keith_busy'] = True
    keith_dict['keith_seq_running'] = True
    if keith_dict['iv_rh_seq'].isChecked():
        measure_iv(keith_dict, df, df_i)
        time.sleep(2)
    if keith_dict['cv_rh_seq'].isChecked():
        measure_multi_cv(keith_dict, df, df_i)
        time.sleep(2)
    if keith_dict['bs_rh_seq'].isChecked():
        measure_bias_seq(keith_dict, df, df_i)
        time.sleep(2)
    time.sleep(float(keith_dict['pause_after_cycle'].value())*60)
    keith_dict['keith_busy'] = False
    keith_dict['keith_seq_running'] = False


def keith_vac_seq(keith_dict, df, df_i):
    # measure keithley functions during vacuum sequence
    keith_dict['keith_busy'] = True
    keith_dict['keith_seq_running'] = True
    if keith_dict['iv_vac_seq'].isChecked():
        measure_iv(keith_dict, df, df_i)
        keith_dict['keith_busy'] = True
        time.sleep(2)
    if keith_dict['cv_vac_seq'].isChecked():
        measure_multi_cv(keith_dict, df, df_i)
        keith_dict['keith_busy'] = True
        time.sleep(2)
    if keith_dict['bs_vac_seq'].isChecked():
        measure_bias_seq(keith_dict, df, df_i)
        keith_dict['keith_busy'] = True
        time.sleep(2)
    time.sleep(float(keith_dict['pause_after_cycle'].value())*60)
    keith_dict['keith_busy'] = False
    keith_dict['keith_seq_running'] = False


if __name__ == '__main__':
    print('testing device...')
    dev = Keithley2400('GPIB2::24')
    dev.reset()
    dev.use_front_terminals()
    dev.measure_current(current=0.1)  # set current compliance
    close(dev)
    print('test successful')
