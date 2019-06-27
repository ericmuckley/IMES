# -*- coding: utf-8 -*-
"""
Created on Wed Jan 9 14:38:47 2019
@author: ericmuckley@gmail.com
"""

# custom modules
from imes_libs import keith
from imes_libs import rhmeter
from imes_libs import sark

# core libraries
from PyQt5 import QtCore, QtWidgets, uic  # , QtGui
from PyQt5.QtWidgets import QMainWindow, QFileDialog
# from datetime import datetime
import pandas as pd
import numpy as np
import sys
import time

# plotting libraries
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
fontsize = 12
plt.rcParams['xtick.labelsize'] = fontsize
plt.rcParams['ytick.labelsize'] = fontsize

# instrument libraries
# from alicat import FlowController

# path of the .ui Qt designer file to set up GUI
qt_ui_file = 'C:\\Users\\a6q\\imes_python\\IMES_layout_Jan22.ui'

# initialize file-saving variables
start_time = time.time()
start_date = time.strftime('%Y-%m-%d_%H-%M')
# set up master dataframe to hold all pressure data
df = pd.DataFrame(
            columns=['date', 'time', 'pressure',
                     'temp', 'bias', 'current',
                     'save'],
            data=np.full((100000, 7), '', dtype=str))
iv_df = pd.DataFrame()
cv_df = pd.DataFrame()
bs_df = pd.DataFrame()

'''
class Keith():

    def __init__(self, output_box):
        self.mainwindow = App
 
    def keith_print(output_box):
        print('hi0')
        output_box.append('printing hi...')
        print('hi')

    def print_iv_biases(self):
        # print biases for I-V measurements in the output box
        iv_biases, _ = keith.get_bias_voltages(self.ui.max_bias.value(),
                                               self.ui.voltage_steps.value())
        self.ui.output_box.append('IV biases = '+format(iv_biases))
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

    def print_cv_biases(self):
        # print biases for C-V measurements in the output box
        _, cv_biases = keith.get_bias_voltages(self.ui.max_bias.value(),
                                               self.ui.voltage_steps.value())
        self.ui.output_box.append('CV biases = '+format(cv_biases))
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

'''


# create the main window
class App(QMainWindow):

    # load Qt designer XML .ui GUI file
    Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_ui_file)

    def __init__(self):  # initialize application
        super(App, self).__init__()
        self.ui = App.Ui_MainWindow()
        self.ui.setupUi(self)

        # create timer which updates fields on GUI (set interval in ms)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.main_loop)
        self.timer.start(self.ui.set_main_loop_delay.value())

        # assign functions to top menu items
        # example: self.ui.MENU_ITEM_NAME.triggered.connect(self.FUNCTION_NAME)
        self.ui.file_quit.triggered.connect(self.quit_app)
        self.ui.file_set_save.triggered.connect(self.set_file_save_directory)
        self.ui.view_file_save_dir.triggered.connect(self.print_file_save_dir)
        self.ui.rh_seq_plot.triggered.connect(self.show_rh_sequence_plot)
        self.ui.seq_export.triggered.connect(self.export_sequence)
        self.ui.seq_import.triggered.connect(self.import_sequence)
        self.ui.seq_clear.triggered.connect(self.clear_sequence)
        self.ui.seq_run.triggered.connect(self.run_sequence)
        self.ui.seq_stop.triggered.connect(self.stop_sequence)
        self.ui.show_pressure_plot.triggered.connect(self.plot_pressure)
        self.ui.preview_bias_seq.triggered.connect(self.plot_bias_seq)
        self.ui.preview_iv_biases.triggered.connect(self.print_iv_biases2)
        self.ui.preview_cv_biases.triggered.connect(self.print_cv_biases2)
        
        
        
        self.ui.measure_iv_button.triggered.connect(self.measure_iv)
        self.ui.measure_cv_button.triggered.connect(self.measure_cv)
        self.ui.measure_current_now.triggered.connect(self.measure_current)
        self.ui.measure_bias_seq_now.triggered.connect(self.measure_bias_seq)
        self.ui.estimate_bands.triggered.connect(self.estimate_bands_using_n)
        self.ui.qcm_measure_now.triggered.connect(self.qcm_measure)

        # assign actions to GUI buttons
        # example: self.ui.BUTTON_NAME.clicked.connect(self.FUNCTION_NAME)
        self.ui.get_harmonics.clicked.connect(self.get_harmonics)
        self.ui.find_band_centers.clicked.connect(self.find_band_centers)
        self.ui.dummy_button.clicked.connect(self.call_k)

        # assign actions to checkboxes
        # example: self.ui.CHECKBOX.stateChanged.connect(self.FUNCTION_NAME)
        self.ui.keithley_on.stateChanged.connect(self.keithley_checked)
        self.ui.rhmeter_on.stateChanged.connect(self.rhmeter_checked)
        self.ui.sark_on.stateChanged.connect(self.sark_checked)

        # initialize some settings
        self.ui.app_start_time_display.setText(time.ctime())
        self.ui.seq_stop.setEnabled(False)
        self.ui.seq_run.setEnabled(True)
        self.stop_sequence = False
        self.keithley_busy = False
        self.ui.menuElectrical_measurements.setEnabled(False)
        self.ui.electrical_box.setEnabled(False)

        # self.keith_print()
        self.df_i = 0  # initialize main loop counter

        '''
        self.qcm_dict = {}
        bc_fields = [self.ui.bc_n1, self.ui.bc_n3, self.ui.bc_n5,
                     self.ui.bc_n7, self.ui.bc_n9, self.ui.bc_n11,
                     self.ui.bc_n13, self.ui.bc_n15, self.ui.bc_n17]
        bw_fields = [self.ui.bw_n1, self.ui.bw_n3, self.ui.bw_n5,
                     self.ui.bw_n7, self.ui.bw_n9, self.ui.bw_n11,
                     self.ui.bw_n13, self.ui.bw_n15, self.ui.bw_n17]
        '''

    def call_k(self):
        Keith.keith_print(self.ui.output_box)

    # ------------ system control functions ------------------------------
    def main_loop(self):
        # Main loop to execute which keeps the app running.
        global save_file_dir
        global start_date
        global start_time
        global df

        # set file save directory on the first loop only
        if self.df_i == 0:
            self.set_file_save_directory()

        # update indicator fields on GUI
        # update fields during each loop iteration
        self.ui.main_loop_counter_display.setText(str(self.df_i))
        # update total sequence time
        pressure_df = self.pressure_table_to_df()
        tot_seq_hrs = pressure_df['time'].astype(float).sum()/60
        self.ui.tot_seq_time_display.setText(
                str(np.round(tot_seq_hrs, decimals=2)))
        self.ui.main_loop_counter_display.setText(str(self.df_i))

        # if RH meter is connected, update RH and temperature fields
        if self.ui.rhmeter_on.isChecked():
            if self.df_i % 4 == 0:
                rh0, temp0 = rhmeter.read(rhmeter_dev)
                self.ui.actual_rh_display.setText(str(rh0))
                self.ui.actual_temp_display.setText(str(temp0))

        # display number of rows of saved data
        self.ui.rows_of_saved_data_display.setText(str(
                    len(df[df['save'] != ''])))

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
            df['pressure'].iloc[self.df_i] = str(pressure0)
            self.ui.pressure_display.setText(str(np.round(pressure0,
                                                          decimals=6)))
            # control pop-up pressure plot
            if not plt.fignum_exists(2):
                    self.ui.show_pressure_plot.setChecked(False)
            if self.ui.show_pressure_plot.isChecked():
                self.plot_pressure()

        # timer which updates fields on GUI (set interval in ms)
        self.main_loop_delay = self.ui.set_main_loop_delay.value()
        self.timer.start(self.main_loop_delay)

        # record date/time and elapsed time at each iteration
        df['date'].iloc[self.df_i] = time.ctime()
        df['time'].iloc[self.df_i] = str(np.round((
                                    time.time()-start_time)/60, decimals=3))

        # measure current
        if self.ui.measure_current_now.isChecked():
            # use this to handle threading during the loop
            # QtCore.QCoreApplication.processEvents()
            self.measure_current()

        # save data
        if self.ui.save_data_now.isChecked():
            df['save'].iloc[self.df_i] = 'on'  # mark current row as "saved"
            if self.df_i % 10 == 0:  # every 10 points, save data to file
                save_master_df = df[df['save'] == 'on']  # remove extra rows
                # use this to handle threading during the loop
                QtCore.QCoreApplication.processEvents()
                save_master_df.to_csv(
                        save_file_dir+'/'+start_date+'_master_df.csv',
                        index=False)

        # increment main loop counter
        self.df_i += 1

    '''
    def plot_results(self, x=[1,2,3], y=[2,6,9],
                     xtitle='X', ytitle='Y', plottitle='Title'):
        #plot results of a measurement
        plt.cla()
        plt.ion()
        plt.plot(x, y, c='k', lw=1, marker='o', markersize=5)
        plt.xlabel(xtitle, fontsize=fontsize)
        plt.ylabel(ytitle, fontsize=fontsize)
        plt.title(plottitle, fontsize=fontsize)
        plt.tight_layout()
        plt.draw()
    '''

    def set_file_save_directory(self):
        # set the directory for saving data files
        global save_file_dir
        save_file_dir = str(QFileDialog.getExistingDirectory(self,
                            'Create or select a directory to save files in.'))
        self.ui.output_box.append('Save file directory set to:')
        self.ui.output_box.append(save_file_dir)

    def print_file_save_dir(self, a):
        # print the file saving directory
        global save_file_dir
        try:  # if save file directory is already set
            self.ui.output_box.append('Current save file directory:')
            self.ui.output_box.append(save_file_dir)
        except NameError:  # if file directory is not set
            self.ui.output_box.append(
                    'No save file directory has been set.')
            self.ui.output_box.append(
                    'Please set in File --> Set file save directory.')

    def quit_app(self):
        # quit the application
        self.ui.measure_current_now.setChecked(False)  # stop measuring current
        # close instruments
        try:
            keith.close(keith_dev)
        except NameError:
            pass
        try:
            rhmeter.close(rhmeter_dev)
        except NameError:
            pass
        try:
            sark.sark_close(sark_dev)
        except NameError:
            pass

        plt.close('all')  # close all figures
        self.deleteLater()
        self.close()  # close app window
        self.timer.stop()  # stop timer

    def dummy_fun(self):
        print(self.df_i)


# ----- functions for SARK-110 antenna analyzer for QCM measurements --------

    def sark_checked(self):
        '''This function triggers when SARK-110 checkbox status changes.'''
        global sark_dev
        # if SARK checkbox was just checked
        if self.ui.sark_on.isChecked():
            try:
                sark_dev = sark.sark_open()
                self.ui.menuQCM.setEnabled(True)
                self.ui.qcm_box.setEnabled(True)
                self.ui.output_box.append('SARK-110 connected.')
            except NameError:
                self.ui.output_box.append('SARK-110 could not connect.')
        # if SARK checkbox was just unchecked
        if not self.ui.sark_on.isChecked():
            try:
                sark.sark_close(sark_dev)
                self.ui.menuQCM.setEnabled(False)
                self.ui.qcm_box.setEnabled(False)
                self.ui.output_box.append('SARK-110 disconnected.')
            except NameError:
                pass

    def estimate_bands_using_n(self):
        '''Estimate the appropriate frequency to measure across based on the
        harmonic number, band points, and resonant frequency of the QCM.'''
        # estimate the frequency bands
        band_dict = sark.get_bands_using_n(
                        f0=int(self.ui.set_f0.value())*1e6,
                        n_list=[1, 3, 5, 7, 9, 11, 13, 15, 17],
                        band_points=int(self.ui.set_band_points.value()))
        # populate estimated F0 and bandwidth fields on GUI
        bc_fields = [self.ui.bc_n1, self.ui.bc_n3, self.ui.bc_n5,
                     self.ui.bc_n7, self.ui.bc_n9, self.ui.bc_n11,
                     self.ui.bc_n13, self.ui.bc_n15, self.ui.bc_n17]
        bw_fields = [self.ui.bw_n1, self.ui.bw_n3, self.ui.bw_n5,
                     self.ui.bw_n7, self.ui.bw_n9, self.ui.bw_n11,
                     self.ui.bw_n13, self.ui.bw_n15, self.ui.bw_n17]
        for band_i, band_key in enumerate(band_dict):
            bc_fields[band_i].setText(str(band_dict[band_key]['bc']))
            bw_fields[band_i].setText(str(band_dict[band_key]['bw']))
        self.ui.output_box.append('Predicted frequency bands estimated.')

    def get_harmonics(self):
        '''Get a list of the harmomics which are selected in the
        GUI checkboxes.'''
        # get selected QCM harmonics from GUI checkboxes
        n_fields = [self.ui.n1_on, self.ui.n3_on, self.ui.n5_on,
                    self.ui.n7_on, self.ui.n9_on, self.ui.n11_on,
                    self.ui.n13_on, self.ui.n15_on, self.ui.n17_on]
        n_options = [1, 3, 5, 7, 9, 11, 13, 15, 17]
        n_selected = []
        for n_i, n0 in enumerate(n_fields):
            if n0.isChecked():
                n_selected.append(n_options[n_i])
        return n_selected

    def get_bands_from_fields(self):
        '''Get measurement bands from band centers and band widths shown in
        fields on GUI.'''
        # get list of which harmonics are checked
        n_options = [1, 3, 5, 7, 9, 11, 13, 15, 17]
        n_selected = self.get_harmonics()
        bc_fields = [self.ui.bc_n1, self.ui.bc_n3, self.ui.bc_n5,
                     self.ui.bc_n7, self.ui.bc_n9, self.ui.bc_n11,
                     self.ui.bc_n13, self.ui.bc_n15, self.ui.bc_n17]
        bw_fields = [self.ui.bw_n1, self.ui.bw_n3, self.ui.bw_n5,
                     self.ui.bw_n7, self.ui.bw_n9, self.ui.bw_n11,
                     self.ui.bw_n13, self.ui.bw_n15, self.ui.bw_n17]

        # populate dictionary of band centers and widths from fields on GUI
        band_dict = {}
        # loop through each harmonic
        for n_i, n0 in enumerate(n_options):
            # if the harmonic will be measured
            if n0 in n_selected:
                # create dictionaries to hold band center, width,
                # and frequencies
                band_dict[str(n0)] = {}
                # determine band center and band width based on GUI fields
                band_center = int(bc_fields[n_i].text())
                band_width = int(bw_fields[n_i].text())
                # construct frequency band
                band = np.linspace(
                        band_center - band_width/2,
                        band_center + band_width/2,
                        num=int(self.ui.set_band_points.value())).astype(int)
                # band center
                band_dict[str(n0)]['bc'] = band_center
                # band width
                band_dict[str(n0)]['bw'] = band_width
                # actual band, in Hz
                band_dict[str(n0)]['band'] = band
        return band_dict

    def find_band_centers(self):
        '''Find resonant frequency of each QCM harmonic.'''
        harmonics = self.get_harmonics()
        sark_dev = sark.sark_open()
        f0_displays = {'1': self.ui.realf0_n1, '3': self.ui.realf0_n3,
                       '5': self.ui.realf0_n5, '7': self.ui.realf0_n7,
                       '9': self.ui.realf0_n9, '11': self.ui.realf0_n11,
                       '13': self.ui.realf0_n13, '15': self.ui.realf0_n15,
                       '17': self.ui.realf0_n17}
        bc_fields = {'1': self.ui.bc_n1, '3': self.ui.bc_n3,
                     '5': self.ui.bc_n5, '7': self.ui.bc_n7,
                     '9': self.ui.bc_n9, '11': self.ui.bc_n11,
                     '13': self.ui.bc_n13, '15': self.ui.bc_n15,
                     '17': self.ui.bc_n17}

        # dictionary for real bandcenters found by scanning frequency bands
        real_bcs = {}

        # loop over each harmonic
        for n0 in harmonics:
            self.ui.output_box.append(
                    'Finding center of harmonic n = '+str(n0)+'...')
            # try band_center based on harmonic number
            bandcenter = int(self.ui.set_f0.value())*1e6*n0 - (5e4*n0)
            # try bandwidth based on harmonic number
            bandwidth = 200000*n0
            band = sark.get_band(bandcenter, bandwidth)
            spec0 = np.zeros((len(band), 2))
            spec0[:, 0] = band
            band_step = band[2] - band[1]  # get frequency interval in band

            # loop over each point in frequency band
            for f0_i in range(0, len(band), 4):
                # use this to handle threading during the loop
                QtCore.QCoreApplication.processEvents()
                # measure conductance at each frequency
                g_vec = sark.get_fast_g(
                        sark_dev, band[f0_i],
                        band_step,
                        avg=int(self.ui.set_qcm_averaging.value()))
                spec0[f0_i:f0_i+4, 1] = g_vec  # save conductance values

                if f0_i % 100 == 0 or f0_i == len(band):
                    # use this to handle threading during the loop
                    QtCore.QCoreApplication.processEvents()
                    # find resonant frequency in band
                    f0, _ = sark.get_f_d(spec0[:, 0], spec0[:, 1])
                    real_bcs[str(n0)] = f0

                    # plot band and resonant frequency
                    # use this to handle threading during the loop
                    QtCore.QCoreApplication.processEvents()
                    plt.ion
                    fig_qcm = plt.figure(100)
                    fig_qcm.clf()
                    plt.plot(spec0[:, 0]/1e6, spec0[:, 1],
                             c='k', lw=2, alpha=0.4)
                    plt.axvline(x=f0/1e6, lw=1, c='r')
                    plt.xlabel('Frequency (Hz)', fontsize=fontsize)
                    plt.ylabel('Conductance (S)', fontsize=fontsize)
                    plt.title('n = '+str(n0), fontsize=fontsize)
                    fig_qcm.canvas.set_window_title('QCM conductance spectrum')
                    plt.tight_layout()
                    plt.draw()

                    bc_fields[str(n0)].setText(str(f0))
                    f0_displays[str(n0)].setText(str(f0))

    def qcm_measure(self):
        '''Measure conductance spectra at specified harmonics and
        frequency bands.'''
        harmonics = self.get_harmonics()
        band_dict = self.get_bands_from_fields()
        sark_dev = sark.sark_open()

        f0_displays = {'1': self.ui.realf0_n1, '3': self.ui.realf0_n3,
                       '5': self.ui.realf0_n5, '7': self.ui.realf0_n7,
                       '9': self.ui.realf0_n9, '11': self.ui.realf0_n11,
                       '13': self.ui.realf0_n13, '15': self.ui.realf0_n15,
                       '17': self.ui.realf0_n17}

        # loop over each harmonic
        for n0 in harmonics:
            self.ui.output_box.append('Measuring harmonic n= '+str(n0))
            # band to measure across
            band = band_dict[str(n0)]['band']
            # create empty array to fill with data
            spec0 = np.zeros((len(band), 2))
            spec0[:, 0] = band
            band_step = band[2] - band[1]  # get frequency interval in band

            # loop over each point in frequency band
            for f0_i in range(0, len(band), 4):
                # use this to handle threading during the loop
                QtCore.QCoreApplication.processEvents()
                # measure conductance at each frequency
                g_vec = sark.get_fast_g(
                        sark_dev,
                        band[f0_i],
                        band_step,
                        avg=int(self.ui.set_qcm_averaging.value()))
                spec0[f0_i:f0_i+4, 1] = g_vec  # save conductance values

                # plot spectra during acquisition
                # use this to handle threading during the loop
                QtCore.QCoreApplication.processEvents()
                if f0_i % int(len(band)/5) == 0 or f0_i == len(band):
                    plt.ion
                    fig_qcm = plt.figure(100 + n0)
                    fig_qcm.clf()
                    plt.plot(spec0[:, 0]/1e6, spec0[:, 1], c='k', lw=1)
                    plt.xlabel('Frequency (Hz)', fontsize=fontsize)
                    plt.ylabel('Conductance (S)', fontsize=fontsize)
                    plt.title('n = '+str(n0), fontsize=fontsize)
                    fig_qcm.canvas.set_window_title('QCM conductance spectrum')
                    plt.tight_layout()
                    plt.draw()

            # get resonant frequency of the spectrum
            f0, _ = sark.get_f_d(spec0[:, 0], spec0[:, 1])
            f0_displays[str(n0)].setText(str(f0))

    # --------- functions for RH / temperature meter -------------------

    def rhmeter_checked(self):
        '''This function is triggered whenever the RH/temp. meter checkbox status
        changes.
        '''
        global rhmeter_dev
        # if RH meter checkbox was just checked
        if self.ui.rhmeter_on.isChecked():
            try:
                rhmeter_dev = rhmeter.initialize(
                        self.ui.rhmeter_address.text())
                self.ui.output_box.append('RH meter connected.')
                self.ui.rhmeter_address.setEnabled(False)
            except NameError:
                self.ui.output_box.append('RH meter could not connect.')
        # if RH meter checkbox was just unchecked
        if not self.ui.rhmeter_on.isChecked():
            try:
                rhmeter.close(rhmeter_dev)
            except NameError:
                pass
            self.ui.output_box.append('RH meter disconnected.')
            self.ui.rhmeter_address.setEnabled(True)

    # --------- functions for electrical characterization -------------------

    def keithley_checked(self):
        '''This function triggers when Keithey checkbox status changes.'''
        global keith_dev
        # if keithley checkbox was just checked
        if self.ui.keithley_on.isChecked():
            try:
                keith_dev = keith.initialize(self.ui.keithley_address.text())
                self.ui.electrical_box.setEnabled(True)
                self.ui.menuElectrical_measurements.setEnabled(True)
                self.ui.keithley_address.setEnabled(False)
                self.ui.output_box.append('Keithley connected.')
            except NameError:
                self.ui.output_box.append('Keithley could not connect.')
        # if keithley checkbox was just unchecked
        if not self.ui.keithley_on.isChecked():
            try:
                keith.close(keith_dev)
            except NameError:
                pass
            self.ui.electrical_box.setEnabled(False)
            self.ui.menuElectrical_measurements.setEnabled(False)
            self.ui.keithley_address.setEnabled(True)
            self.ui.output_box.append('Keithley disconnected.')

    def measure_current(self):
        '''Measure current continuously using Keithley multimeter.'''
        global df_i
        global df
        global keithley_busy
        # if current measurement was initiated
        if self.ui.measure_current_now.isChecked():
            self.ui.measure_iv_button.setEnabled(False)
            self.ui.measure_cv_button.setEnabled(False)
            self.keithley_busy = True
            keith.apply_bias(keith_dev, self.ui.set_constant_bias.value())
            current0 = keith.get_current(keith_dev)
            self.ui.current_display.setText(
                    str(np.round(current0, decimals=11)))
            df['bias'].iloc[self.df_i] = self.ui.set_constant_bias.value()
            df['current'].iloc[self.df_i] = current0
            if self.df_i % 3 == 0:
                # use this to handle threading during the loop
                QtCore.QCoreApplication.processEvents()
                # plot current over time
                plt.ion
                fig_current = plt.figure(5)
                fig_current.clf()
                df_current = df[df['current'] != '']
                plt.plot(df_current['time'].astype(float),
                         df_current['current'].astype(float),
                         c='r', lw=1)
                plt.xlabel('Elapsed time (min)', fontsize=fontsize)
                plt.ylabel('Current (A)', fontsize=fontsize)
                fig_current.canvas.set_window_title('Sample current')
                plt.tight_layout()
                plt.draw()

        # if current measurement was stopped
        if not self.ui.measure_current_now.isChecked():
            keith.remove_bias(keith_dev)
            self.ui.measure_iv_button.setEnabled(True)
            self.ui.measure_cv_button.setEnabled(True)
            self.ui.output_box.append(
                    'Current measurement at constant bias ended.')
            self.keithley_busy = False

    def print_iv_biases2(self):
        # print biases for I-V measurements in the output box
        iv_biases, _ = keith.get_bias_voltages(self.ui.max_bias.value(),
                                               self.ui.voltage_steps.value())
        self.ui.output_box.append('IV biases = '+format(iv_biases))
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

    def print_cv_biases2(self):
        # print biases for C-V measurements in the output box
        _, cv_biases = keith.get_bias_voltages(self.ui.max_bias.value(),
                                               self.ui.voltage_steps.value())
        self.ui.output_box.append('CV biases = '+format(cv_biases))
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



    def print_iv_biases(self):
        # print biases for I-V measurements in the output box
        keith.print_iv_biases(self.ui.max_bias.value(),
                              self.ui.voltage_steps.value(),
                              self.ui.output_box)

    def print_cv_biases(self):
        # print biases for C-V measurements in the output box
        keith.print_cv_biases(self.ui.max_bias.value(),
                              self.ui.voltage_steps.value(),
                              self.ui.output_box)
        '''
        iv_biases, _ = keith.get_bias_voltages(self.ui.max_bias.value(),
                                               self.ui.voltage_steps.value())
        self.ui.output_box.append('IV biases = '+format(iv_biases))
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
        '''

    def print_cv_biases(self):
        # print biases for C-V measurements in the output box
        _, cv_biases = keith.get_bias_voltages(self.ui.max_bias.value(),
                                               self.ui.voltage_steps.value())
        self.ui.output_box.append('CV biases = '+format(cv_biases))
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

    def measure_iv(self):
        '''Measure I-V curve using Keithley multimeter.'''
        global iv_df
        global keithley_busy
        iv_biases, _ = keith.get_bias_voltages(self.ui.max_bias.value(),
                                               self.ui.voltage_steps.value())
        current_list = np.empty_like(iv_biases)
        self.ui.output_box.append('Measuring I-V...')
        iv_time = time.ctime()
        keithley_busy = True
        # loop through each applied voltage level
        for v_i, v0 in enumerate(iv_biases):
            # use this to handle threading during the loop
            QtCore.QCoreApplication.processEvents()
            # apply voltage
            keith.apply_bias(keith_dev, v0)
            # read current
            current_list[v_i] = keith.get_current(keith_dev)
            self.ui.current_display.setText(
                    str(np.round(current_list[v_i], decimals=11)))
            # plot results over time
            plt.ion
            fig_press = plt.figure(7)
            fig_press.clf()
            plt.plot(iv_biases[:v_i], current_list[:v_i], c='k', lw=1)
            plt.xlabel('Bias V)', fontsize=fontsize)
            plt.ylabel('Current (A)', fontsize=fontsize)
            fig_press.canvas.set_window_title('I-V measurement')
            plt.tight_layout()
            plt.draw()
        self.ui.output_box.append('I-V measurement complete.')
        keith.remove_bias(keith_dev)
        keithley_busy = False
        # append new data to I-V dataframe. first create empty cells to fill.
        # this is done so I-V curves with different lengths can be appended
        iv_df['bias_'+iv_time] = np.repeat('', 99)
        iv_df['current_'+iv_time] = np.repeat('', 99)
        # now fill empty cells with new data
        iv_df['bias_'+iv_time].iloc[:len(iv_biases)] = iv_biases.astype(str)
        iv_df['current_'+iv_time].iloc[
                :len(iv_biases)] = current_list.astype(str)
        # save I-V data to file
        iv_df.to_csv(save_file_dir+'/'+start_date+'_iv.csv', index=False)

    def measure_cv(self):
        '''Measure C-V curve using Keithley multimeter.'''
        global cv_df
        global keithley_busy
        _, cv_biases = keith.get_bias_voltages(
                self.ui.max_bias.value(), self.ui.voltage_steps.value())
        current_list = np.empty_like(cv_biases)
        self.ui.output_box.append('Measuring C-V...')
        cv_time = time.ctime()
        keithley_busy = True
        # loop through each applied voltage level
        for v_i, v0 in enumerate(cv_biases):
            # use this to handle threading during the loop
            QtCore.QCoreApplication.processEvents()
            # apply voltage
            keith.apply_bias(keith_dev, v0)
            # read current
            current_list[v_i] = keith.get_current(keith_dev)
            self.ui.current_display.setText(
                    str(np.round(current_list[v_i], decimals=11)))
            # plot results over time
            plt.ion
            fig_press = plt.figure(8)
            fig_press.clf()
            plt.plot(cv_biases[:v_i], current_list[:v_i], c='k', lw=1)
            plt.xlabel('Bias V)', fontsize=fontsize)
            plt.ylabel('Current (A)', fontsize=fontsize)
            fig_press.canvas.set_window_title('C-V measurement')
            plt.tight_layout()
            plt.draw()
        self.ui.output_box.append('C-V measurement complete.')
        keith.remove_bias(keith_dev)
        keithley_busy = False
        # append new data to C-V dataframe. first create empty cells to fill.
        # this is done so C-V curves with different lengths can be appended
        cv_df['bias_'+cv_time] = np.repeat('', 1000)
        cv_df['current_'+cv_time] = np.repeat('', 1000)
        # now fill empty cells with new data
        cv_df['bias_'+cv_time].iloc[:len(cv_biases)] = cv_biases.astype(str)
        cv_df['current_'+cv_time].iloc[
                :len(cv_biases)] = current_list.astype(str)
        # save C-V data to file
        cv_df.to_csv(save_file_dir+'/'+start_date+'_cv.csv', index=False)

    def bias_table_to_df(self):
        # convert bias sequence table on GUI to pandas dataframe
        # create empty dataframe
        bias_df = pd.DataFrame(columns=['points', 'bias'],
                               index=range(self.ui.bias_seq_table.rowCount()))
        # populate dataframe
        for rowi in range(self.ui.bias_seq_table.rowCount()):
            for colj in range(self.ui.bias_seq_table.columnCount()):
                new_entry = self.ui.bias_seq_table.item(rowi, colj).text()
                bias_df.iloc[rowi, colj] = new_entry
        # delete empty rows
        bias_df = bias_df[bias_df['points'] != '0'].astype(float)
        return bias_df

    def plot_bias_seq(self):
        # plot the bias sequence
        try:  # retrieve the sequence from the GUI bias table
            bs_array = self.bias_table_to_df().values
            # create empty list to populate from bias sequence table
            bs_biases = [np.repeat(
                    bs_array[ii, 1],
                    bs_array[ii, 0]) for ii in range(len(bs_array))]
            bs_biases = np.reshape(bs_biases, (-1,))
            fig_seq = plt.figure(9)
            plt.cla()
            plt.ion()
            plt.plot(np.arange(len(bs_biases))+1, bs_biases,
                     c='r', drawstyle='steps', alpha=1)
            plt.xlabel('Points', fontsize=fontsize)
            plt.ylabel('Bias (V)', fontsize=fontsize)
            plt.tight_layout()
            fig_seq.canvas.set_window_title('Bias sequence')
            fig_seq.show()
        except NameError:
            self.ui.output_box.append(
                'Bias sequence not valid.')

    def measure_bias_seq(self):
        # Measure current over time using Keithley multimeter.
        # Voltage bias is applied over time according to bias table on GUI.
        global bias_seq_df
        global keithley_busy
        # retrieve the sequence from the GUI bias table
        bs_array = self.bias_table_to_df().values
        # create empty list to populate from bias sequence table
        bs_biases = [np.repeat(
                bs_array[ii, 1],
                bs_array[ii, 0]) for ii in range(len(bs_array))]
        bs_biases = np.reshape(bs_biases, (-1,))
        self.ui.output_box.append('Measuring bias sequence...')
        # create empty array to hold measured data
        bs_results = np.empty((0, 3))
        keithley_busy = True
        bs_time = time.ctime()
        bs_start_time = time.time()
        for bs_i, bs_v0 in enumerate(bs_biases):
            # use this to handle threading during the loop
            QtCore.QCoreApplication.processEvents()
            # apply bias and measure current
            keith.apply_bias(keith_dev, bs_v0)
            current0 = keith.get_current(keith_dev)
            self.ui.current_display.setText(
                    str(np.round(current0, decimals=11)))
            # add results to saved bias array
            bs_results = np.vstack((bs_results,
                                    [(time.time() - bs_start_time)/60,
                                     bs_v0, current0]))
            # plot the bias over time
            plt.ion
            fig_press = plt.figure(6)
            fig_press.clf()
            plt.plot(bs_results[:, 0], bs_results[:, 2], c='k', lw=1)
            plt.xlabel('Elapsed time (min)', fontsize=fontsize)
            plt.ylabel('Current (A)', fontsize=fontsize)
            fig_press.canvas.set_window_title('Current during bias sequence')
            plt.tight_layout()
            plt.draw()

        keith.remove_bias(keith_dev)
        self.ui.output_box.append('Bias sequence complete.')
        keithley_busy = False
        # append new data to bias seq dataframe. #first create empty cells to
        # fill so bias sequences with different lengths can be appended
        bs_df['time_'+bs_time] = np.repeat('', 10000)
        bs_df['bias_'+bs_time] = np.repeat('', 10000)
        bs_df['current_'+bs_time] = np.repeat('', 10000)
        # now fill empty cells with new data
        bs_df['time_'+bs_time].iloc[
                :(len(bs_results))] = bs_results[:, 0].astype(str)
        bs_df['bias_'+bs_time].iloc[
                :(len(bs_results))] = bs_results[:, 1].astype(str)
        bs_df['current_'+bs_time].iloc[
                :(len(bs_results))] = bs_results[:, 2].astype(str)
        # save bias seq data to file
        bs_df.to_csv(save_file_dir+'/'+start_date+'_bs.csv', index=False)

    '''
    #timed bias sequence functions

    def plot_timed_bias_seq(self):
        #plot the timed bias sequence
        try: #retrieve the sequence from the GUI bias table
            bias_seq = self.bias_table_to_df().values
            seq_time = bias_seq[:,0]
            plot_seq_time = np.insert(np.cumsum(seq_time), 0, 0)
            seq_bias = bias_seq[:,1]
            plot_seq_bias = np.insert(seq_bias, 0, seq_bias[0])
            fig_seq = plt.figure(9)
            plt.cla()
            plt.ion()
            plt.plot(plot_seq_time,
                     plot_seq_bias,
                     c='r', drawstyle='steps', alpha=1)
            plt.xlabel('Time (minutes)', fontsize=fontsize)
            plt.ylabel('Bias (V)', fontsize=fontsize)
            plt.tight_layout()
            fig_seq.canvas.set_window_title('Bias sequence')
            fig_seq.show()
        except: self.ui.output_box.append('Bias sequence not valid.')


    def timed_bias_table_to_df(self):
        #convert bias sequence table on GUI to pandas dataframe
        #create empty dataframe
        bias_df = pd.DataFrame(columns=['time', 'bias'],
                                index=range(self.ui.bias_seq_table.rowCount()))
        #populate dataframe
        for rowi in range(self.ui.bias_seq_table.rowCount()):
            for colj in range(self.ui.bias_seq_table.columnCount()):
                new_entry = self.ui.bias_seq_table.item(rowi, colj).text()
                bias_df.iloc[rowi, colj] = new_entry
        #delete empty rows
        bias_df = bias_df[bias_df['time'] != '0'].astype(float)
        return bias_df

    def measure_bias_seq_timed(self):
        #Measure current over time using Keithley multimeter.
        #Voltage bias is applied over time according to bias table on GUI.

        global bias_seq_df
        global keithley_busy
        #retrieve the sequence from the GUI bias table
        bias_seq = self.timed_bias_table_to_df().values
        #step durations in minutes
        bs_step_lengths = bias_seq[:, 0]*60
        step_biases = bias_seq[:,1]
        self.ui.output_box.append('Measuring bias sequence...')
        #create empty array to hold measured data
        bs_results = np.empty((0,3))
        bs_start_time = time.time()
        bs_time = time.ctime()
        keithley_busy = True
        for i in range(len(bias_seq)):
            bs_step_start_time = time.time()
            while time.time() - bs_step_start_time < bs_step_lengths[i]:
                #use this to handle threading during the loop
                QtCore.QCoreApplication.processEvents()
                #apply bias and measure current
                keith.apply_bias(keith_dev, step_biases[i])
                current0 = keith.get_current(keith_dev)
                self.ui.current_display.setText(
                                        str(np.round(current0, decimals=11)))
                # add results to saved bias array
                bs_results = np.vstack((bs_results,
                                        [(time.time() - bs_start_time)/60,
                                         step_biases[i], current0]))
                #plot the bias over time
                plt.ion
                fig_press = plt.figure(6)
                fig_press.clf()
                plt.plot(bs_results[:,0], bs_results[:,2], c='k', lw=1)
                plt.xlabel('Elapsed time (min)', fontsize=fontsize)
                plt.ylabel('Current (A)', fontsize=fontsize)
                fig_press.canvas.set_window_title(
                        'Current during bias sequence')
                plt.tight_layout()
                plt.draw()

        keith.remove_bias(keith_dev)
        self.ui.output_box.append('Bias sequence complete.')
        keithley_busy = False
        #append new data to bias seq dataframe. #first create empty cells to
        #tfill so bias sequences with different lengths can be appended
        bs_df['time_'+bs_time] = np.repeat('', 10000)
        bs_df['bias_'+bs_time] = np.repeat('', 10000)
        bs_df['current_'+bs_time] = np.repeat('', 10000)
        #now fill empty cells with new data
        bs_df['time_'+bs_time].iloc[
                :(len(bs_results))] = bs_results[:,0].astype(str)
        bs_df['bias_'+bs_time].iloc[
                :(len(bs_results))] = bs_results[:,1].astype(str)
        bs_df['current_'+bs_time].iloc[
                :(len(bs_results))] = bs_results[:,2].astype(str)
        #save bias seq data to file
        bs_df.to_csv(save_file_dir+'/'+start_date+'_bs.csv', index=False)
    '''
    # ------- functions for pressure control ------------------------------

    def pressure_table_to_df(self):
        # convert pressure sequence table to pandas dataframe
        global pressure_df
        # create empty dataframe
        pressure_df = pd.DataFrame(columns=['time', 'rh'],
                                   index=range(
                                           self.ui.pressure_table.rowCount()))
        # populate dataframe
        for rowi in range(self.ui.pressure_table.rowCount()):
            for colj in range(self.ui.pressure_table.columnCount()):
                new_entry = self.ui.pressure_table.item(rowi, colj).text()
                pressure_df.iloc[rowi, colj] = new_entry
        # delete empty rows
        pressure_df = pressure_df[pressure_df['time'] != '']
        return pressure_df

    def plot_pressure(self):
        # plot the pressure over time
        global df
        if self.df_i % 3 == 0:
            plt.ion
            fig_press = plt.figure(2)
            fig_press.clf()
            dfp = df[df['date'] != '']

            plt.plot(dfp['time'].astype(float),
                     dfp['pressure'].astype(float),
                     c='k', lw=1)
            plt.xlabel('Elapsed time (min)', fontsize=fontsize)
            plt.ylabel('Pressure (Torr)', fontsize=fontsize)
            fig_press.canvas.set_window_title('Chamber pressure')
            plt.tight_layout()
            plt.draw()

# ----------------- functions for pressure sequence control ----------------

    def show_rh_sequence_plot(self):
        # plot the pressure sequence
        try:
            pressure_df = self.pressure_table_to_df()
            seq_time = np.array(pressure_df['time'].astype(float))
            plot_seq_time = np.insert(np.cumsum(seq_time), 0, 0)/60
            seq_rh = np.array(pressure_df['rh'].astype(float))
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
            plt.xlabel('Time (hours)', fontsize=fontsize)
            plt.ylabel('RH (%)', fontsize=fontsize)
            plt.tight_layout()
            fig_seq.canvas.set_window_title('Pressure sequence')
            fig_seq.show()
        except NameError:
            self.ui.output_box.append('Pressure sequence not valid.')

    def clear_sequence(self):
        # clear pressure sequence
        # populate dataframe with 0's
        for rowi in range(self.ui.pressure_table.rowCount()):
            for colj in range(self.ui.pressure_table.columnCount()):
                self.ui.pressure_table.setItem(rowi, colj,
                                               QtWidgets.QTableWidgetItem('0'))
        self.ui.output_box.append('Pressure sequence cleared.')

    def export_sequence(self):
        # save pressure sequence
        export_seq_name = QFileDialog.getSaveFileName(
                self, 'Create pressure sequence file to save',
                '.csv')[0]
        pressure_df.to_csv(str(export_seq_name), index=False)
        self.ui.output_box.append('Pressure sequence file exported.')

    def import_sequence(self):
        # import pressure sequence file
        import_seq_name = QFileDialog.getOpenFileName(
                self, 'Select pressure sequence file')[0]
        imported_seq = pd.read_csv(import_seq_name)
        # populate table on GUI
        for rowi in range(len(imported_seq)):
            for colj in range(len(imported_seq.columns)):
                self.ui.pressure_table.setItem(rowi, colj,
                                               QtWidgets.QTableWidgetItem(
                                                       str(imported_seq.iloc[
                                                               rowi, colj])))
        self.ui.output_box.append('Pressure sequence file imported.')

    def stop_sequence(self):
        # send sequence early using when "STOP" sequence menu item is clicked
        self.stop_sequence = True

    def run_sequence(self):
        # run pressure sequence
        # disable other sequence options
        self.ui.output_box.append('Pressure sequence initiated.')
        self.ui.seq_clear.setEnabled(False)
        self.ui.seq_import.setEnabled(False)
        self.ui.seq_run.setEnabled(False)
        self.ui.seq_stop.setEnabled(True)
        self.ui.valve_mode.setEnabled(False)
        self.ui.pressure_mode.setEnabled(False)
        self.ui.set_pressure.setEnabled(False)
        self.ui.set_valve_position.setEnabled(False)
        self.ui.flow1.setEnabled(False)
        self.ui.flow2.setEnabled(False)
        self.ui.flow3.setEnabled(False)
        self.ui.save_data_now.setChecked(True)

        # set up timers and counters
        pressure_df = self.pressure_table_to_df().astype(float)
        elapsed_seq_time = 0
        seq_start_time = time.time()
        # loop over each step in sequence
        for step in range(len(pressure_df)):
            if not self.stop_sequence:
                step_start_time = time.time()
                elapsed_step_time = 0
                step_dur = pressure_df['time'].iloc[step]*60
            else:
                break
            # repeat until step duration has elapsed
            while elapsed_step_time < step_dur:
                # use this to handle threading during the loop
                QtCore.QCoreApplication.processEvents()
                if not self.stop_sequence:
                    # update step counters and timers on GU
                    elapsed_step_time = time.time() - step_start_time
                    self.ui.current_step_display.setText(str(int(step+1)))
                    self.ui.set_rh.setValue(pressure_df['rh'].iloc[step])
                    self.ui.elapsed_step_time_display.setText(
                            str(np.round(elapsed_step_time/60, decimals=3)))
                    elapsed_seq_time = time.time() - seq_start_time
                    self.ui.elapsed_seq_time_display.setText(
                            str(np.round(elapsed_seq_time/3600, decimals=3)))

                    # EXECUTE MEASUREMENTS INSIDE SEQUENCE HERE

                    if self.ui.iv_during_seq.isChecked(
                            ) and not keithley_busy:
                        # use this to handle threading during the loop
                        QtCore.QCoreApplication.processEvents()
                        self.measure_iv()
                    if self.ui.cv_during_seq.isChecked(
                            ) and not keithley_busy:
                        QtCore.QCoreApplication.processEvents()
                        self.measure_cv()
                    if self.ui.bs_during_seq.isChecked(
                            ) and not keithley_busy:
                        QtCore.QCoreApplication.processEvents()
                        self.measure_bias_seq()

                else:
                    break
        self.stop_sequence = False
        self.ui.save_data_now.setChecked(False)
        # reset sequence counters
        self.ui.current_step_display.setText('0')
        self.ui.elapsed_step_time_display.setText('0')
        self.ui.elapsed_seq_time_display.setText('0')
        self.ui.output_box.append('Pressure sequence completed.')
        # re-enable other sequence options
        self.ui.seq_clear.setEnabled(True)
        self.ui.seq_import.setEnabled(True)
        self.ui.seq_run.setEnabled(True)
        self.ui.seq_stop.setEnabled(False)
        self.ui.valve_mode.setEnabled(True)
        self.ui.pressure_mode.setEnabled(True)
        self.ui.set_pressure.setEnabled(True)
        self.ui.set_valve_position.setEnabled(True)
        self.ui.flow1.setEnabled(True)
        self.ui.flow2.setEnabled(True)
        self.ui.flow3.setEnabled(True)


# --------------------------- run application ----------------------------
if __name__ == '__main__':
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    window = App()
    window.show()
    sys.exit(app.exec_())
