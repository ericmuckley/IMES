# -*- coding: utf-8 -*-
"""
Created on Wed Jan 9 14:38:47 2019
@author: ericmuckley@gmail.com
"""

# custom modules
from imes_libs import ops
from imes_libs import keith
from imes_libs import rhmeter
from imes_libs import sark
from imes_libs import rh200

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
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12

# instrument libraries
# from alicat import FlowController


# create the main window
class App(QMainWindow):

    # path of the .ui Qt designer file to set up GUI
    qt_ui_file = 'C:\\Users\\a6q\\imes_python\\IMES_layout_Jan30.ui'

    # load Qt designer XML .ui GUI file
    Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_ui_file)

    def __init__(self):  # initialize application
        super(App, self).__init__()
        self.ui = App.Ui_MainWindow()
        self.ui.setupUi(self)

        self.move(0, 0)  # set initial position of the window

        # create timer which updates fields on GUI (set interval in ms)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.main_loop)
        self.timer.start(self.ui.set_main_loop_delay.value())

        # assign functions to top menu items
        # example: self.ui.MENU_ITEM_NAME.triggered.connect(self.FUNCTION_NAME)
        self.ui.plot_rh.triggered.connect(self.plot_rh)
        self.ui.file_quit.triggered.connect(self.quit_app)
        self.ui.run_rh_seq.triggered.connect(self.run_rh_seq)
        self.ui.stop_rh_seq.triggered.connect(self.stop_rh_seq)
        self.ui.plot_rh_seq.triggered.connect(self.plot_rh_seq)
        self.ui.clear_rh_seq.triggered.connect(self.clear_rh_seq)
        self.ui.measure_iv_now.triggered.connect(self.measure_iv)
        self.ui.measure_cv_now.triggered.connect(self.measure_cv)
        self.ui.view_iv_data.triggered.connect(self.view_iv_data)
        self.ui.view_cv_data.triggered.connect(self.view_cv_data)
        self.ui.view_bs_data.triggered.connect(self.view_bs_data)
        self.ui.export_rh_seq.triggered.connect(self.export_rh_seq)
        self.ui.import_rh_seq.triggered.connect(self.import_rh_seq)
        self.ui.measure_bands.triggered.connect(self.measure_bands)
        self.ui.view_qcm_data.triggered.connect(self.view_qcm_data)
        self.ui.preview_bias_seq.triggered.connect(self.plot_bias_seq)
        self.ui.find_resonances.triggered.connect(self.find_resonances)
        self.ui.preview_iv_biases.triggered.connect(self.print_iv_biases)
        self.ui.preview_cv_biases.triggered.connect(self.print_cv_biases)
        self.ui.measure_current_now.triggered.connect(self.measure_current)
        self.ui.file_set_save.triggered.connect(self.set_file_save_directory)
        self.ui.view_file_save_dir.triggered.connect(self.view_file_save_dir)
        self.ui.measure_bias_seq_now.triggered.connect(self.measure_bias_seq)

        # assign actions to GUI buttons
        # example: self.ui.BUTTON_NAME.clicked.connect(self.FUNCTION_NAME)

        # assign actions to checkboxes
        # example: self.ui.CHECKBOX.stateChanged.connect(self.FUNCTION_NAME)
        # self.ui.rhmeter_on.stateChanged.connect(self.rhmeter_checked)
        self.ui.sark_on.stateChanged.connect(self.sark_checked)
        self.ui.rh200_on.stateChanged.connect(self.rh200_checked)
        self.ui.keithley_on.stateChanged.connect(self.keithley_checked)

        # initialize device names
        self.rhmeter_dev = None
        self.rh_task_dict = None

        # initialize some settings
        self.sark_busy = False
        self.keithley_busy = False
        self.rh_seq_running = False
        self.ui.rh_box.setEnabled(False)
        self.ui.qcm_box.setEnabled(False)
        self.ui.menu_rh.setEnabled(False)
        self.ui.menu_qcm.setEnabled(False)
        self.ui.electrical_box.setEnabled(False)
        self.ui.menu_electrical.setEnabled(False)
        self.ui.app_start_time_display.setText(time.ctime())

        # master dataframe to hold all pressure data
        self.df = pd.DataFrame(
                columns=['date', 'time', 'pressure', 'rh', 'rh_setpoint',
                         'temp', 'bias', 'current',
                         'save'],
                data=np.full((100000, 9), '', dtype=str))

        # initialize file-saving variables
        self.df_i = 0
        self.start_time = time.time()
        self.start_date = time.strftime('%Y-%m-%d_%H-%M')
        self.file_save_dir_is_set = False
        self.set_file_save_directory()
        self.iv_df = pd.DataFrame()
        self.cv_df = pd.DataFrame()
        self.bs_df = pd.DataFrame()
        self.qcm_data = {str(i): pd.DataFrame() for i in range(1, 19, 2)}
        self.qcm_data['params'] = pd.DataFrame(
                data=np.full((10000, 19), ''),
                columns=['time', 'f_1', 'f_3', 'f_5', 'f_7', 'f_9',
                         'f_11', 'f_13', 'f_15', 'f_17',
                         'd_1', 'd_3', 'd_5', 'd_7', 'd_9',
                         'd_11', 'd_13', 'd_15', 'd_17'])

        # dictionary to hold GUI operation-related items
        self.ops_dict = {
                'timer': self.timer,
                'start_time': self.start_time,
                'start_date': self.start_date,
                'save_file_dir': self.save_file_dir,
                'save_data_now': self.ui.save_data_now,
                'rows_of_saved_data': self.ui.rows_of_saved_data,
                'set_main_loop_delay': self.ui.set_main_loop_delay,
                'main_loop_counter_display': self.ui.main_loop_counter_display}

        # dictionary to hold pressure-related items
        self.press_dict = {
                'flow1': self.ui.flow1,
                'flow2': self.ui.flow2,
                'flow3': self.ui.flow3,
                'valve_mode': self.ui.valve_mode,
                'flow1_display': self.ui.flow1_display,
                'flow2_display': self.ui.flow2_display,
                'flow3_display': self.ui.flow3_display,
                'pressure_mode': self.ui.pressure_mode,
                'set_valve_position': self.ui.set_valve_position}

        # dictionary to hold sequence-related items
        self.seq_dict = {
                'set_rh': self.ui.set_rh,
                'rh_box': self.ui.rh_box,
                'menu_rh': self.ui.menu_rh,
                'rh_table': self.ui.rh_table,
                'rh200_on': self.ui.rh200_on,
                'output_box': self.ui.output_box,
                'rh_display': self.ui.rh_display,
                'run_rh_seq': self.ui.run_rh_seq,
                'rh_task_dict': self.rh_task_dict,
                'rh_seq_step': self.ui.rh_seq_step,
                'rh_seq_running': self.rh_seq_running,
                'save_data_now': self.ui.save_data_now,
                'tot_rh_seq_time': self.ui.tot_rh_seq_time,
                'elapsed_rh_seq_time': self.ui.elapsed_rh_seq_time}

        # dictionary to hold Keithley-related items
        self.keith_dict = {
                'keith_dev': None,
                'iv_df': self.iv_df,
                'cv_df': self.cv_df,
                'bs_df': self.bs_df,
                'set_bias': self.ui.set_bias,
                'max_bias': self.ui.max_bias,
                'start_date': self.start_date,
                'output_box': self.ui.output_box,
                'keithley_on': self.ui.keithley_on,
                'keithley_busy': self.keithley_busy,
                'save_file_dir': self.save_file_dir,
                'voltage_steps': self.ui.voltage_steps,
                'keith_address': self.ui.keith_address,
                'measure_iv_now': self.ui.measure_iv_now,
                'measure_cv_now': self.ui.measure_cv_now,
                'bias_seq_table': self.ui.bias_seq_table,
                'electrical_box': self.ui.electrical_box,
                'current_display': self.ui.current_display,
                'menu_electrical': self.ui.menu_electrical,
                'measure_current_now': self.ui.measure_current_now}

        # dictionary to hold QCM-related items
        self.sark_dict = {
                'sark_dev': None,
                'nth_qcm_loop': 0,
                'set_f0': self.ui.set_f0,
                'qcm_data': self.qcm_data,
                'sark_on': self.ui.sark_on,
                'qcm_box': self.ui.qcm_box,
                'sark_busy': self.sark_busy,
                'menu_qcm': self.ui.menu_qcm,
                'start_date': self.start_date,
                'dynamic_bc': self.ui.dynamic_bc,
                'output_box': self.ui.output_box,
                'save_file_dir': self.save_file_dir,
                'sec_per_band': self.ui.sec_per_band,
                'measure_bands': self.ui.measure_bands,
                'find_resonances': self.ui.find_resonances,
                'set_band_points': self.ui.set_band_points,
                'set_qcm_averaging': self.ui.set_qcm_averaging,
                'bc_fields': {
                        '1': self.ui.bc_n1, '3': self.ui.bc_n3,
                        '5': self.ui.bc_n5, '7': self.ui.bc_n7,
                        '9': self.ui.bc_n9, '11': self.ui.bc_n11,
                        '13': self.ui.bc_n13, '15': self.ui.bc_n15,
                        '17': self.ui.bc_n17},
                'bw_fields': {
                        '1': self.ui.bw_n1, '3': self.ui.bw_n3,
                        '5': self.ui.bw_n5, '7': self.ui.bw_n7,
                        '9': self.ui.bw_n9, '11': self.ui.bw_n11,
                        '13': self.ui.bw_n13, '15': self.ui.bw_n15,
                        '17': self.ui.bw_n17},
                'n_on_fields': {
                        '1': self.ui.n1_on, '3': self.ui.n3_on,
                        '5': self.ui.n5_on, '7': self.ui.n7_on,
                        '9': self.ui.n9_on, '11': self.ui.n11_on,
                        '13': self.ui.n13_on, '15': self.ui.n15_on,
                        '17': self.ui.n17_on},
                'f0_displays': {
                        '1': self.ui.realf0_n1, '3': self.ui.realf0_n3,
                        '5': self.ui.realf0_n5, '7': self.ui.realf0_n7,
                        '9': self.ui.realf0_n9, '11': self.ui.realf0_n11,
                        '13': self.ui.realf0_n13, '15': self.ui.realf0_n15,
                        '17': self.ui.realf0_n17}}

# %% ----------- system control functions ------------------------------

    def main_loop(self):
        # Main loop to execute which keeps the app running.
        # wait until the file saving directory is set
        if self.file_save_dir_is_set:

            # functions to run when RH sequence is not running
            if not self.rh_seq_running:
                # measure RH
                if self.ui.rh200_on.isChecked():
                    rh200.set_rh(self.seq_dict, self.df, self.df_i)
                # measure current
                if self.ui.keithley_on.isChecked():
                    if self.ui.measure_current_now.isChecked():
                        self.measure_current()

            # control which functions run during RH sequence
            if self.seq_dict['rh_seq_running']:

                if self.ui.iv_rh_seq.isChecked():
                    print(1)
                    if not self.keith_dict['keithley_busy']:
                        print(2)
                        self.measure_iv(self.keith_dict)
                if self.ui.cv_rh_seq.isChecked():
                    if not self.keith_dict['keithley_busy']:
                        self.measure_cv(self.keith_dict)
                if self.ui.bs_rh_seq.isChecked():
                    if not self.keith_dict['keithley_busy']:
                        self.measure_bias_seq(self.keith_dict)
                if self.ui.qcm_rh_seq.isChecked():
                    if not self.sark_dict['sark_busy']:
                        self.measure_bands()
                if self.ui.optical_rh_seq.isChecked():
                    pass

            # update fields, normal operations, and saving in main loop
            self.df, self.df_i = ops.main_loop_update(
                    self.ops_dict, self.df, self.df_i)

    def set_file_save_directory(self):
        # set the directory for saving data files
        self.save_file_dir = str(QFileDialog.getExistingDirectory(
                self, 'Create or select directory for data files.'))
        self.ui.output_box.append('Save file directory set to:')
        self.ui.output_box.append(self.save_file_dir)
        self.file_save_dir_is_set = True

    def view_file_save_dir(self):
        # Print the file saving directory to the output box on GUI.
        ops.view_file_save_dir(self.keith_dict)

    def quit_app(self):
        # quit the application
        self.ui.measure_current_now.setChecked(False)
        # close instruments
        if self.ui.keithley_on.isChecked():
            keith.close(self.keith_dict['keith_dev'])
        if self.ui.sark_on.isChecked():
            sark.sark_close(self.sark_dict['sark_dev'])
        if self.ui.rhmeter_on.isChecked():
            rhmeter.close(self.rhmeter_dev)
        if self.ui.rh200_on.isChecked():
            rh200.close(self.seq_dict['rh_task_dict'])
        plt.close('all')  # close all figures
        self.deleteLater()
        self.close()  # close app window
        self.timer.stop()  # stop timer

# %% --- functions for QCM measurements using SARK-110 antenna analyzer ------

    def sark_checked(self):
        # This function triggers when SARK-110 checkbox status changes.
        sark.checked(self.sark_dict)

    def find_resonances(self):
        # Find resonance peak at each QCM harmonic by sweeping across bands
        sark.find_resonances(self.sark_dict)

    def measure_bands(self):
        # Measure across frequency bands as set by fields on GUI.
        sark.measure_bands(self.sark_dict)

    def view_qcm_data(self):
        # Views all data acquired by the SARK-110.
        sark.view_qcm_data(self.sark_dict)


# %%  ---- functions for electrical characterization using Keithley 2420 -----

    def keithley_checked(self):
        # This function triggers when Keithey checkbox status changes
        keith.checked(self.keith_dict)

    def measure_current(self):
        # Measure current continuously using Keithley multimeter.
        keith.get_current_continuously(self.keith_dict, self.df, self.df_i)

    def print_iv_biases(self):
        # print and display biases used for I-V measurements
        keith.print_iv_biases(self.keith_dict)

    def measure_iv(self):
        # Measure I-V curve using Keithley multimeter.
        keith.measure_iv(self.keith_dict)

    def print_cv_biases(self):
        # print and display biases used for C-V measurements
        keith.print_cv_biases(self.keith_dict)

    def measure_cv(self):
        # Measure C-V curve using Keithley multimeter.
        keith.measure_cv(self.keith_dict)

    def plot_bias_seq(self):
        # plot the bias sequence
        keith.plot_bias_seq(self.keith_dict)

    def measure_bias_seq(self):
        # measure current during a sequence of changing biases
        keith.measure_bias_seq(self.keith_dict)

    def view_iv_data(self):
        # view all I-V data in one plot
        keith.view_iv_data(self.keith_dict)

    def view_cv_data(self):
        # view all C-V data in one plot
        keith.view_cv_data(self.keith_dict)

    def view_bs_data(self):
        # view all bias-sequence data in one plot
        keith.view_bs_data(self.keith_dict)

# %% ---------- functions for RH control and sequence ------------------

    def rh200_checked(self):
        # Triggers when RH-200 humidity generator checkbox status changes.
        rh200.checked(self.seq_dict)

    def import_rh_seq(self):
        # Import a saved RH sequence from file
        seq_name = QFileDialog.getOpenFileName(
                self, 'Select RH sequence file', '.csv')[0]
        rh200.import_rh_seq(self.seq_dict, seq_name)

    def export_rh_seq(self):
        # Export an RH sequence from the sequence table to a file
        seq_name = QFileDialog.getSaveFileName(
                self, 'Export RH sequence file', '.csv')[0]
        rh200.export_rh_seq(self.seq_dict, seq_name)

    def clear_rh_seq(self):
        # Clear the RH seuquence from the GUI table
        rh200.clear_rh_seq(self.seq_dict)

    def plot_rh_seq(self):
        # Show plot of the RH over time
        rh200.plot_rh_seq(self.seq_dict)

    def plot_rh(self):
        rh200.plot_rh(self.df, self.df_i)

    def stop_rh_seq(self):
        # Stop RH sequence
        self.seq_dict['rh_seq_running'] = False

    def run_rh_seq(self):
        # Run the RH sequence
        rh200.run_rh_seq(self.seq_dict)

# %% ---------------- functions for pressure sequence control ----------------

    '''
    def plot_pressure(self):
        pass

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
                            ) and not self.keithley_busy:
                        # use this to handle threading during the loop
                        QtCore.QCoreApplication.processEvents()
                        self.measure_iv()
                    if self.ui.cv_during_seq.isChecked(
                            ) and not self.keithley_busy:
                        QtCore.QCoreApplication.processEvents()
                        self.measure_cv()
                    if self.ui.bs_during_seq.isChecked(
                            ) and not self.keithley_busy:
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
        '''
# %% --------- functions for RH / temperature meter -------------------

    '''
    def rhmeter_checked(self):
        # This function is triggered whenever the RH/temp. meter checkbox
        # status changes.

        # if RH meter checkbox was just checked
        if self.ui.rhmeter_on.isChecked():
            try:
                self.rhmeter_dev = rhmeter.initialize(
                        self.ui.rhmeter_address.text())
                self.ui.output_box.append('RH meter connected.')
                self.ui.rhmeter_address.setEnabled(False)
            except NameError:
                self.ui.output_box.append('RH meter could not connect.')
        # if RH meter checkbox was just unchecked
        if not self.ui.rhmeter_on.isChecked():
            try:
                rhmeter.close(self.rhmeter_dev)
            except NameError:
                pass
            self.ui.output_box.append('RH meter disconnected.')
            self.ui.rhmeter_address.setEnabled(True)
       '''


# %% -------------------------- run application ----------------------------
if __name__ == '__main__':
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    window = App()
    window.show()
    sys.exit(app.exec_())
