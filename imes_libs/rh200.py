# -*- coding: utf-8 -*-
"""
This module communicates with the L&C Science RH-200 relative
humidity generator. The functions which control the generator
are written as National Instruments NIDAQ Tasks, which are provided
by the manufacturer. This module uses a Python library written by NI
to control the NIDAQMX tasks and control the RH generator.

The module also provides methods related to creating RH sequences
for automated long-term  control of the RH-200.

Packages required:
time
numpy
PyQt5
nidaqmx

Created on Fri Feb 1 11:13:59 2019
@author: ericmuckley@gmail.com
"""

from PyQt5 import QtWidgets
import warnings
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time
import numpy as np
import nidaqmx
fontsize = 12

# suppress NI DAQ warning:
# Finite acquisition or generation has been stopped before the requested
# number of samples were acquired or generated.
# error_buffer.value.decode("utf-8"), error_code)
# DaqWarning: Warning 200010 occurred.
warnings.filterwarnings('ignore', category=nidaqmx.DaqWarning)

# ---------these functions are related to controlling the RH-200

# Connect to NI DAQ system (viewable in National Instruments Measurement and
# Automation Explorer (NI-MAX))


def initialize():
    # Initialize RH-200 humidity generator. Returns a dictionary of
    # NI DAQ tasks required for controlling the RH-200 humidity generator.
    # system = nidaqmx.system.system.System()
    # create persisted task for dew point meter ('AI DP')
    dp_ptask = nidaqmx.system.storage.persisted_task.PersistedTask(
            'AI DP')
    dp_task = dp_ptask.load()
    # create persisted tasks for analog output wet and dry tasks
    ao_wet_ptask = nidaqmx.system.storage.persisted_task.PersistedTask(
            'AO WET')
    ao_wet_task = ao_wet_ptask.load()
    ao_dry_ptask = nidaqmx.system.storage.persisted_task.PersistedTask(
            'AO DRY')
    ao_dry_task = ao_dry_ptask.load()
    # create persisted tasks for digital output wet, dry, and gas tasks
    do_wet_ptask = nidaqmx.system.storage.persisted_task.PersistedTask(
            'DO WET')
    do_wet_task = do_wet_ptask.load()
    do_dry_ptask = nidaqmx.system.storage.persisted_task.PersistedTask(
            'DO DRY')
    do_dry_task = do_dry_ptask.load()
    do_gas_ptask = nidaqmx.system.storage.persisted_task.PersistedTask(
            'DO GAS')
    do_gas_task = do_gas_ptask.load()

    # create dictionary to hold all task names and loaded tasks
    rh_task_dict = {'dp': dp_task, 'ao_wet': ao_wet_task,
                    'ao_dry': ao_dry_task, 'do_wet': do_wet_task,
                    'do_dry': do_dry_task, 'do_gas': do_gas_task}

    rh_task_dict['dp'].timing.cfg_samp_clk_timing(1, samps_per_chan=2)

    return rh_task_dict


def close(rh_task_dict):
    # Close RH-200 relative humidity generator by looping through loaded
    # tasks and closing each one.
    for task in rh_task_dict:
        try:
            rh_task_dict[task].stop()
        except:
            pass
        try:
            rh_task_dict[task].close()
        except:
            pass


def dp_to_rh(dp, temp=22, decimals=3):
    # Uses the voltage signal output from the RH-200 deq point analyzer
    # and temperature in deg C, and converts to relative humidity in %.
    # Rounds output to the number of decimals specified by 'decimals'.
    dp = dp*20 - 40
    numerator = np.exp((17.625*dp)/(243.04+dp))
    denominator = np.exp((17.625*temp)/(243.04+temp))
    rh = 100*np.divide(numerator, denominator)
    return np.round(rh, decimals=3)


def rh_setpoint_to_volts(setpoint):
    # Converts RH setpoint in % to volts for analog output writing to wet
    # and dry mass flow controllers inside RH-200.
    # Outputs voltages to apply to wet and dry flow contollers.
    # Uses coefficients from calibration polynomial which relates
    # mass flow controller voltage to the actual RH produced.
    bi = -0.4347
    b1 = -48.3857
    b2 = -1.74901
    sp = setpoint
    wet_volts = (np.sqrt((b1**2)-(4*b2*(bi-sp)))+b1)/(2*b2)
    dry_volts = 4 - wet_volts
    return wet_volts, dry_volts


def checked(rh_dict):
    # Triggers when RH-200 box is checked or unchecked on the GUI.
    if rh_dict['rh200_on'].isChecked():  # if box was checked
        try:
            rh_dict['output_box'].append(
                    'RH-200 humidity generator connected')
            rh_dict['menu_rh'].setEnabled(True)
            rh_dict['run_rh_seq'].setEnabled(True)

            # initialize RH generator NIDAQ tasks
            rh_dict['rh_task_dict'] = initialize()

        except NameError:
            rh_dict['output_box'].append(
                    'RH-200 connection failed, please restart kernel.')

    if not rh_dict['rh200_on'].isChecked():  # if box was unchecked
        close(rh_dict['rh_task_dict'])
        rh_dict['set_rh'].setEnabled(False)
        rh_dict['rh_seq_running'] = False
        rh_dict['menu_rh'].setEnabled(False)
        rh_dict['rh_display'].setText('--')
        rh_dict['output_box'].append('RH-200 humidity generator disconnected')


def set_rh(rh_dict, df, df_i):
    # Sets RH and dispays RH on front GUI.
    # try to close NI_DAQ tasks if they are already opened
    try:
        [rh_dict['rh_task_dict'][key].stop() for key in rh_dict['rh_task_dict']]
    except:
        pass
    # try to run RH generator
    try:
        # run Ni-DAQ tasks
        [rh_dict['rh_task_dict'][key].start() for key in rh_dict['rh_task_dict']]
        time.sleep(0.1)
        # read actual dewpoint
        dp = rh_dict['rh_task_dict']['dp'].read()
        # convert depoint to actual RH
        actual_rh = dp_to_rh(dp)
        rh_dict['current_rh'] = float(actual_rh)
        rh_dict['rh_display'].setText(str(actual_rh))
        # get setpoint from GUI
        setpoint = float(rh_dict['set_rh'].value())
        # append values to main GUI dataframe
        df['rh'].iloc[df_i] = str(actual_rh)
        df['rh_setpoint'].iloc[df_i] = str(setpoint)
        # write voltages to mass flow controllers
        wet_volts, dry_volts = rh_setpoint_to_volts(setpoint)
        rh_dict['rh_task_dict']['ao_wet'].write(wet_volts)
        rh_dict['rh_task_dict']['ao_dry'].write(dry_volts)
        rh_dict['rh_task_dict']['do_wet'].write(True)
        rh_dict['rh_task_dict']['do_dry'].write(True)
        rh_dict['rh_task_dict']['do_gas'].write(True)
        # try to close RH generator tasks
        try:
            [rh_dict['rh_task_dict'][key].stop() for key in rh_dict['rh_task_dict']]
        except:
            pass   

        # update RH sequence duration on GUI.
        rh_df = rh_table_to_df(rh_dict)
        seq_time = rh_df['time'].sum()
        rh_dict['tot_rh_seq_time'].setText(
                str(np.round(int(seq_time)/60, decimals=2)))
        
        
        # display estimated sequence end time
        if not rh_dict['rh_seq_running']:
            tot_seq_min = rh_df['time'].sum()
            seq_start_date = datetime.datetime.now()
            seq_end_date = seq_start_date + datetime.timedelta(minutes=tot_seq_min)
            rh_dict['seq_end_time_display'].setText(
                   seq_end_date.strftime('%m-%d %H:%M:%S'))
    except:
        pass


def plot_rh(df, df_i):
    # Plot the RH over time
    rh_df = df[df['rh'] != '']
    setpoint = rh_df['rh_setpoint'].astype(float)
    rh = rh_df['rh'].astype(float)
    rh_time = rh_df['time'].astype(float)
    fig_seq = plt.figure(20)
    plt.cla()
    plt.ion()
    plt.plot(rh_time/60, rh, c='b', label='measured')
    plt.plot(rh_time/60, setpoint, c='r', label='setpoint')
    plt.xlabel('Time (hours)', fontsize=12)
    plt.ylabel('RH (%)', fontsize=12)
    plt.legend(fontsize=12)
    plt.tight_layout()
    fig_seq.canvas.set_window_title('RH over time')
    fig_seq.show()


# -----These functions are related to the RH sequence --------------------


def rh_table_to_df(rh_dict):
    # Convert RH sequence table on GUI to a Pandas dataframe
    # create empty dataframe
    rh_df = pd.DataFrame(
            columns=['time', 'rh'],
            index=range(rh_dict['rh_table'].rowCount()))

    # loop over table entries
    for rowi in range(rh_dict['rh_table'].rowCount()):
        for colj in range(rh_dict['rh_table'].columnCount()):
            # populate dataframe with table entries
            new_entry = rh_dict['rh_table'].item(rowi, colj).text()
            rh_df.iloc[rowi, colj] = new_entry
    # delete empty rows
    rh_df = rh_df[rh_df['time'] != '0']
    return rh_df.astype(float)


def add_rh_step(rh_dict):
    # add a RH step to the end of the RH sequence table

    # get the current table
    rh_df = rh_table_to_df(rh_dict)
    # get the table index to write
    new_index = len(rh_df)
    # get the value of RH to write
    new_rh = rh_dict['rh_to_add'].value()
    # get the new value of time to write
    new_time = 60
    # write to table
    rh_dict['rh_table'].item(new_index, 0).setText(str(new_time))
    rh_dict['rh_table'].item(new_index, 1).setText(str(new_rh))


def plot_rh_seq(rh_dict):
    # plot the RH sequence
    try:
        rh_df = rh_table_to_df(rh_dict)
        seq_time = np.array(rh_df['time'].astype(float))
        plot_seq_time = np.insert(np.cumsum(seq_time), 0, 0)/60
        seq_rh = np.array(rh_df['rh'].astype(float))
        plot_seq_rh = np.insert(seq_rh, 0, seq_rh[0])
        fig_seq = plt.figure(1)
        plt.cla()
        plt.ion()
        plt.fill_between(plot_seq_time,
                         plot_seq_rh,
                         step='pre', alpha=0.6)
        plt.plot(plot_seq_time,
                 plot_seq_rh,
                 c='b', drawstyle='steps', alpha=0)
        plt.xlabel('Time (hours)', fontsize=12)
        plt.ylabel('RH (%)', fontsize=12)
        plt.tight_layout()
        fig_seq.canvas.set_window_title('RH sequence')
        fig_seq.show()
    except NameError:
        rh_dict['output_box'].append('RH sequence not valid.')


def import_rh_seq(rh_dict, seq_name):
    # import RH sequence from file
    imported_seq = pd.read_csv(seq_name)
    # populate table on GUI
    for rowi in range(len(imported_seq)):
        for colj in range(len(imported_seq.columns)):
            rh_dict['rh_table'].setItem(
                    rowi, colj,
                    QtWidgets.QTableWidgetItem(
                            str(imported_seq.iloc[rowi, colj])))
    rh_dict['output_box'].append('RH sequence file imported.')


def export_rh_seq(rh_dict, seq_name):
    # export RH sequence to file
    rh_df = rh_table_to_df(rh_dict)
    rh_df.to_csv(str(seq_name), index=False)
    rh_dict['output_box'].append('RH sequence file exported.')


def clear_rh_seq(rh_dict):
    # clear pressure sequence by populating the sequence table with 0's
    for rowi in range(rh_dict['rh_table'].rowCount()):
        for colj in range(rh_dict['rh_table'].columnCount()):
            rh_dict['rh_table'].setItem(
                    rowi, colj,
                    QtWidgets.QTableWidgetItem('0'))
    rh_dict['output_box'].append('RH sequence cleared.')


def run_rh_seq(rh_dict):
    # run RH sequence
    rh_dict['output_box'].append('RH sequence initiated.')
    rh_dict['rh_seq_running'] = True
    rh_dict['run_rh_seq'].setEnabled(False)
    rh_dict['save_data_now'].setChecked(True)
    rh_dict['set_rh'].setEnabled(False)
    rh_dict['rh_table'].setEnabled(False)
    rh_df = rh_table_to_df(rh_dict)
    tot_seq_time = rh_df['time'].sum()
    tot_time_disp = str(np.round(tot_seq_time, decimals=1))
    # set up timers and counters
    elapsed_seq_time = 0
    seq_start_time = time.time()

    tot_seq_min = rh_df['time'].sum()
    seq_start_date = datetime.datetime.now()
    seq_end_date = seq_start_date + datetime.timedelta(
                                               minutes=tot_seq_min)
    rh_dict['seq_end_time_display'].setText(
           seq_end_date.strftime('%m-%d %H:%M:%S'))

    step_num = 0
    # loop over each step in sequence
    for step in range(len(rh_df)):

        if rh_dict['rh_seq_running']:
            step_start_time = time.time()
            elapsed_step_time = 0
            step_dur = rh_df['time'].iloc[step]*60
        else:
            break
        # repeat until step duration has elapsed
        while elapsed_step_time < step_dur:

            if rh_dict['rh_seq_running']:
                elapsed_step_time = time.time() - step_start_time
                elapsed_seq_time = time.time() - seq_start_time

                # update fields on GUI
                if step_num % 5 == 0:
                    rh_dict['save_data_now'].setChecked(True)
                    rh_dict['rh_seq_step'].setText(
                            str(int(step+1))+'/'+str(len(rh_df)))

                    rh_dict['set_rh'].setValue(float(rh_df['rh'].iloc[step]))

                    elasped_time_disp = str(
                            np.round(elapsed_seq_time/60, decimals=2))

                    rh_dict['elapsed_rh_seq_time'].setText(
                            elasped_time_disp + '/' + tot_time_disp)

                time.sleep(.5)
                step_num += 1
            else:
                break

    rh_dict['rh_seq_step'].setText('0')
    rh_dict['set_rh'].setValue(2)
    rh_dict['elapsed_rh_seq_time'].setText('0')
    rh_dict['output_box'].append('RH sequence completed.')
    rh_dict['rh_seq_running'] = False
    rh_dict['run_rh_seq'].setEnabled(True)
    rh_dict['set_rh'].setEnabled(True)
    rh_dict['rh_table'].setEnabled(True)
    rh_dict['save_data_now'].setChecked(False)


'''
# for plotting pressure over time
if self.df_i % 3 == 0:
    plt.ion
    fig_press = plt.figure(2)
    fig_press.clf()
    dfp = self.df[self.df['date'] != '']

    plt.plot(dfp['time'].astype(float),
             dfp['pressure'].astype(float),
             c='k', lw=1)
    plt.xlabel('Elapsed time (min)')
    plt.ylabel('Pressure (Torr)')
    fig_press.canvas.set_window_title('Chamber pressure')
    plt.tight_layout()
    plt.draw()
'''


# TEST RH-200 CONTROL BY RUNNING THIS MODULE
if __name__ == '__main__':

    setpoint = 2

    rh_task_dict = initialize()

    for i in range(5):
        [rh_task_dict[key].start() for key in rh_task_dict]

        dp = rh_task_dict['dp'].read()
        actual_rh = dp_to_rh(dp)
        print(actual_rh)
        # write voltages to mass flow controllers
        wet_volts, dry_volts = rh_setpoint_to_volts(setpoint)
        rh_task_dict['ao_wet'].write(wet_volts)
        rh_task_dict['ao_dry'].write(dry_volts)

        rh_task_dict['do_wet'].write(True)
        rh_task_dict['do_dry'].write(True)
        rh_task_dict['do_gas'].write(True)

        time.sleep(1)
        [rh_task_dict[key].stop() for key in rh_task_dict]

    close(rh_task_dict)
