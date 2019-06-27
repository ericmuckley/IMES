# -*- coding: utf-8 -*-
"""
This module controls high-level operations of the main GUI,
including file saving operatins, quitting the application, and updating
fields on the GUI over time.

Packages required:
time

Created on Mon Feb  4 10:37:07 2019
@author: ericmuckley@gmail.com
"""

import time
import numpy as np


def main_loop_update(ops_dict, df, df_i):
    # Update fields on GUI, perform main operations, and save data
    # in main GUI loop.

    # timer which updates fields on GUI (set interval in ms)
    ops_dict['main_loop_delay'] = ops_dict['set_main_loop_delay'].value()
    ops_dict['timer'].start(ops_dict['main_loop_delay'])

    # update main loop counter display on GUI
    ops_dict['main_loop_counter_display'].setText(str(df_i))

    # record date/time and elapsed time at each iteration
    df['date'].iloc[df_i] = time.ctime()
    elapsed_time = str(np.round((
            time.time()-ops_dict['start_time'])/60, decimals=3))
    df['time'].iloc[df_i] = elapsed_time
    # save data
    if ops_dict['save_data_now'].isChecked():
        # mark current row as "saved"
        df['save'].iloc[df_i] = 'on'
        # every 10 points, save data to file
        if df_i % 10 == 0:
            # remove extra rows
            save_master_df = df[df['save'] == 'on']
            # remove "save" column
            save_master_df = save_master_df[save_master_df.columns[:-1]]

            save_master_df.to_csv(
                    ops_dict['save_file_dir']+'/'+ops_dict[
                            'start_date']+'_main_df.csv', index=False)

    ops_dict['rows_of_saved_data'].setText(str(len(df[df['save'] != ''])))
    # increment main loop counter
    df_i = df_i + 1
    return df, df_i


def view_file_save_dir(keith_dict):
    # Show the name of the file-saving directory in the output box on the GUI.
    try:  # if save file directory is already set
        keith_dict['output_box'].append('Current save file directory:')
        keith_dict['output_box'].append(keith_dict['save_file_dir'])
    except NameError:  # if file directory is not set
        keith_dict['output_box'].append(
                'No save file directory has been set.')
        keith_dict['output_box'].append(
                'Please set in File --> Change file save directory.')


def dummy_function(self):
    # call this function from GUI to test/debug different functionality
    print(self.df_i)
    print(len(self.df))


'''
# these may have to go in main loop
if self.ui.rhmeter_on.isChecked():
    if self.df_i % 4 == 0:
        rh0, temp0 = rhmeter.read(self.rhmeter_dev)
        self.ui.actual_rh_display.setText(str(rh0))
        self.ui.actual_temp_display.setText(str(temp0))


# display number of rows of saved data
self.ui.rows_of_saved_data_display.setText(str(
            len(self.df[self.df['save'] != ''])))

# switching between pressure and valve mode
if self.ui.pressure_mode.isChecked():
    self.ui.set_pressure.setEnabled(True)
    self.ui.set_valve_position.setEnabled(False)
if self.ui.valve_mode.isChecked():
    self.ui.set_valve_position.setEnabled(True)
    self.ui.set_pressure.setEnabled(False)

# control pressure

if self.ui.pressure_control_on.isChecked():
    pressure0 = np.random.random()+760
    self.df['pressure'].iloc[self.df_i] = str(pressure0)
    self.ui.pressure_display.setText(str(np.round(pressure0,
                                                  decimals=6)))
    # control pop-up pressure plot
    if not plt.fignum_exists(2):
            self.ui.show_pressure_plot.setChecked(False)
    if self.ui.show_pressure_plot.isChecked():
        self.plot_pressure()

'''
