# -*- coding: utf-8 -*-
"""
Created on Wed Jan 9 14:38:47 2019
@author: ericmuckley@gmail.com
"""

# custom modules
from imes_libs import spec  # Ocean Optics USB4000 optical spectrometer
from imes_libs import ops  # operations of the GUI
from imes_libs import keith  # Keithley 2400 source-measure unit
from imes_libs import rhmeter  # RH / temp meter
from imes_libs import sark  # SARK-110 antenna analyzer for QCM measurements
from imes_libs import rh200  # RH-200 relative humidity generator
from imes_libs import eis  # Solartron 1260 vector impedance analyzer
from imes_libs import vac  # insruments for controlling vacuum chamber
from imes_libs import realtimeplot  # module for realtime plots in pyqtgraph

# core GUI libraries
from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QMainWindow, QFileDialog
import ornl_cnms_logo

# to create new logo, create qrc file in Qt desinger, then use
# Anaconda prompt to run: Pyrcc5 qrc_filename.qrc -o output_file.py

from threading import Thread
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
ornl_cnms_logo


class App(QMainWindow):  # create the main window

    # path of the .ui Qt designer file to set up GUI
    ui_layout = 'C:\\Users\\a6q\\imes_python\\IMES_layout.ui'

    # load Qt designer XML .ui GUI file
    Ui_MainWindow, QtBaseClass = uic.loadUiType(ui_layout)

    def __init__(self):  # initialize application
        super(App, self).__init__()
        self.ui = App.Ui_MainWindow()
        self.ui.setupUi(self)

        self.move(150, 150)  # set initial position of the window

        # create timer which updates fields on GUI (set interval in ms)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.main_loop)
        self.timer.start(int(self.ui.set_main_loop_delay.value()))

        # assign functions to top menu items
        # example: self.ui.MENU_ITEM_NAME.triggered.connect(self.FUNCTION_NAME)
        # system menu items
        self.ui.file_quit.triggered.connect(self.quit_app)
        self.ui.list_devices.triggered.connect(self.list_devices)
        self.ui.create_report.triggered.connect(self.create_report)
        self.ui.export_settings.triggered.connect(self.export_settings)
        self.ui.import_settings.triggered.connect(self.import_settings)
        self.ui.file_set_save.triggered.connect(self.set_file_save_directory)
        self.ui.view_file_save_dir.triggered.connect(self.view_file_save_dir)
        self.ui.view_app_starttime.triggered.connect(self.view_app_starttime)
        # vacuum menu items
        self.ui.run_vac_seq.triggered.connect(self.run_vac_seq)
        self.ui.stop_vac_seq.triggered.connect(self.stop_vac_seq)
        self.ui.plot_vac_seq.triggered.connect(self.plot_vac_seq)
        self.ui.plot_pressure.triggered.connect(self.plot_pressure)
        self.ui.clear_vac_seq.triggered.connect(self.clear_vac_seq)
        self.ui.export_vac_seq.triggered.connect(self.export_vac_seq)
        self.ui.import_vac_seq.triggered.connect(self.import_vac_seq)
        # RH menu items
        self.ui.add_rh_step.triggered.connect(self.add_rh_step)
        self.ui.plot_rh_now.triggered.connect(self.plot_rh)
        self.ui.run_rh_seq.triggered.connect(self.run_rh_seq)
        self.ui.stop_rh_seq.triggered.connect(self.stop_rh_seq)
        self.ui.plot_rh_seq.triggered.connect(self.plot_rh_seq)
        self.ui.clear_rh_seq.triggered.connect(self.clear_rh_seq)
        self.ui.export_rh_seq.triggered.connect(self.export_rh_seq)
        self.ui.import_rh_seq.triggered.connect(self.import_rh_seq)
        # DC electrical menu items
        self.ui.plot_current.triggered.connect(self.plot_current)
        self.ui.measure_iv_now.triggered.connect(self.measure_iv)
        self.ui.measure_cv_now.triggered.connect(self.measure_cv)
        self.ui.view_iv_data.triggered.connect(self.view_iv_data)
        self.ui.view_cv_data.triggered.connect(self.view_cv_data)
        self.ui.view_bs_data.triggered.connect(self.view_bs_data)
        self.ui.clear_dc_data.triggered.connect(self.clear_dc_data)
        self.ui.iv_max_vs_time.triggered.connect(self.iv_max_vs_time)
        self.ui.cv_max_vs_time.triggered.connect(self.cv_max_vs_time)
        self.ui.preview_bias_seq.triggered.connect(self.plot_bias_seq)
        self.ui.cv_area_vs_time.triggered.connect(self.cv_area_vs_time)
        self.ui.preview_iv_biases.triggered.connect(self.print_iv_biases)
        self.ui.preview_cv_biases.triggered.connect(self.print_cv_biases)
        self.ui.measure_current_now.triggered.connect(self.measure_current)
        self.ui.measure_bias_seq_now.triggered.connect(self.measure_bias_seq)
        # AC electrical menu items
        self.ui.plot_z.triggered.connect(self.plot_z)
        self.ui.plot_phase.triggered.connect(self.plot_phase)
        self.ui.measure_eis.triggered.connect(self.measure_eis)
        self.ui.plot_nyquist.triggered.connect(self.plot_nyquist)
        self.ui.clear_ac_data.triggered.connect(self.clear_ac_data)
        self.ui.plot_low_freq_z.triggered.connect(self.plot_low_freq_z)
        self.ui.preview_eis_freqs.triggered.connect(self.preview_eis_freqs)
        # qcm menu items
        self.ui.plot_deltaf.triggered.connect(self.plot_deltaf)
        self.ui.plot_deltad.triggered.connect(self.plot_deltad)
        self.ui.measure_bands.triggered.connect(self.measure_bands)
        self.ui.clear_qcm_data.triggered.connect(self.clear_qcm_data)
        self.ui.find_resonances.triggered.connect(self.find_resonances)
        self.ui.plot_qcm_spectra.triggered.connect(self.plot_qcm_spectra)

        # optical spectrometer menu items
        self.ui.clear_optical_data.triggered.connect(self.clear_optical_data)
        self.ui.get_opt_spectrum.triggered.connect(self.get_optical_spectrum)
        self.ui.plot_opt_spectra.triggered.connect(self.plot_optical_spectra)

        # assign actions to GUI buttons
        # example: self.ui.BUTTON_NAME.clicked.connect(self.FUNCTION_NAME)

        # assign actions to checkboxes
        # example: self.ui.CHECKBOX.stateChanged.connect(self.FUNCTION_NAME)
        # self.ui.rhmeter_on.stateChanged.connect(self.rhmeter_checked)
        self.ui.eis_on.stateChanged.connect(self.eis_checked)
        self.ui.mks_on.stateChanged.connect(self.mks_checked)
        self.ui.sark_on.stateChanged.connect(self.sark_checked)
        self.ui.spec_on.stateChanged.connect(self.spec_checked)
        self.ui.mfc1_on.stateChanged.connect(self.mfc1_checked)
        self.ui.mfc2_on.stateChanged.connect(self.mfc2_checked)
        self.ui.turbo_on.stateChanged.connect(self.turbo_checked)
        self.ui.rh200_on.stateChanged.connect(self.rh200_checked)
        self.ui.keithley_on.stateChanged.connect(self.keithley_checked)

        # initialize some settings
        self.eis_busy = False
        self.sark_busy = False
        self.keith_busy = False
        self.spec_busy = False
        self.rhmeter_dev = None
        self.rh_task_dict = None
        self.rh_seq_running = False
        self.vac_seq_running = False
        self.ui.qcm_box.setEnabled(False)
        # self.ui.menu_vacuum.setEnabled(False)
        self.ui.electrical_box.setEnabled(False)
        self.ui.menu_electrical.setEnabled(False)
        self.ui.start_eis_freq.setCurrentIndex(0)
        self.ui.end_eis_freq.setCurrentIndex(6)

        # master dataframe to hold all pressure data
        self.df = pd.DataFrame(
                columns=['date', 'time', 'pressure', 'pressure_setpoint',
                         'mfc1', 'mfc2', 'rh', 'rh_setpoint',
                         'temp', 'bias', 'current', 'max_iv_current',
                         'max_cv_current', 'cv_area', 'low_freq_z',
                         'note', 'save'],
                data=np.full((100000, 17), '', dtype=str))

        # initialize file-saving variables
        self.df_i = 0
        self.save_file_dir = None
        self.start_time = time.time()
        self.start_date = time.strftime('%Y-%m-%d_%H-%M_')
        # this opens file diaglog for saving
        self.set_file_save_directory()
        # initialize dataframes for holding saved data
        self.iv_df = pd.DataFrame()
        self.cv_df = pd.DataFrame()
        self.bs_df = pd.DataFrame()
        self.eis_df = pd.DataFrame()
        self.optical_df = pd.DataFrame()
        self.qcm_data = {str(i): pd.DataFrame() for i in range(1, 19, 2)}
        self.qcm_data['params'] = pd.DataFrame(
                data=np.full((10000, 19), ''),
                columns=['time', 'f_1', 'f_3', 'f_5', 'f_7', 'f_9',
                         'f_11', 'f_13', 'f_15', 'f_17',
                         'd_1', 'd_3', 'd_5', 'd_7', 'd_9',
                         'd_11', 'd_13', 'd_15', 'd_17'])

        # dictionary to hold GUI operation-related items
        self.ops_dict = {
                'app': self.ui,
                'elapsed_time': 0,
                'timer': self.timer,
                'gas1': self.ui.gas1,
                'gas2': self.ui.gas2,
                'app_settings': None,
                'start_time': self.start_time,
                'start_date': self.start_date,
                'output_box': self.ui.output_box,
                'sample_name': self.ui.sample_name,
                'save_file_dir': self.save_file_dir,
                'save_data_now': self.ui.save_data_now,
                'rows_of_saved_data': self.ui.rows_of_saved_data,
                'set_main_loop_delay': self.ui.set_main_loop_delay,
                'main_loop_counter_display': self.ui.main_loop_counter_display}

        # dictionary to hold pressure-related items
        self.vac_dict = {
                'mks_dev': None,
                'mfc1_dev': None,
                'mfc2_dev': None,
                'mfc3_dev': None,
                'turbo_dev': None,
                'gas1': self.ui.gas1,
                'gas2': self.ui.gas2,
                'mks_on': self.ui.mks_on,
                'current_pressure': None,
                'mfc1_on': self.ui.mfc1_on,
                'mfc2_on': self.ui.mfc2_on,
                'mfc1_sp': self.ui.mfc1_sp,
                'mfc2_sp': self.ui.mfc2_sp,
                'mfc3_sp': self.ui.mfc3_sp,
                'turbo_on': self.ui.turbo_on,
                'run_turbo': self.ui.run_turbo,
                'vac_table': self.ui.vac_table,
                'output_box': self.ui.output_box,
                'valve_mode': self.ui.valve_mode,
                'turbo_speed': self.ui.turbo_speed,
                'menu_vacuum': self.ui.menu_vacuum,
                'mks_address': self.ui.mks_address,
                'run_vac_seq': self.ui.run_vac_seq,
                'mfc1_address': self.ui.mfc1_address,
                'mfc2_address': self.ui.mfc2_address,
                'vac_seq_step': self.ui.vac_seq_step,
                'set_pressure': self.ui.set_pressure,
                'mfc1_display': self.ui.mfc1_display,
                'mfc2_display': self.ui.mfc2_display,
                'mfc3_display': self.ui.mfc3_display,
                'stop_vac_seq': self.ui.stop_vac_seq,
                'set_valve_pos': self.ui.set_valve_pos,
                'save_data_now': self.ui.save_data_now,
                'pressure_mode': self.ui.pressure_mode,
                'turbo_auto_on': self.ui.turbo_auto_on,
                'turbo_address': self.ui.turbo_address,
                'vac_seq_running': self.vac_seq_running,
                'pressure_display': self.ui.pressure_display,
                'tot_vac_seq_time': self.ui.tot_vac_seq_time,
                'valve_pos_display': self.ui.valve_pos_display,
                'elapsed_vac_seq_time': self.ui.elapsed_vac_seq_time,
                'vac_seq_end_time_display': self.ui.vac_seq_end_time_display}

        # dictionary to hold RH-200 generator related items
        self.rh_dict = {
                'current_rh': None,
                'set_rh': self.ui.set_rh,
                'menu_rh': self.ui.menu_rh,
                'rh_table': self.ui.rh_table,
                'rh200_on': self.ui.rh200_on,
                'rh_to_add': self.ui.rh_to_add,
                'output_box': self.ui.output_box,
                'rh_display': self.ui.rh_display,
                'run_rh_seq': self.ui.run_rh_seq,
                'rh_task_dict': self.rh_task_dict,
                'rh_seq_step': self.ui.rh_seq_step,
                'rh_seq_running': self.rh_seq_running,
                'save_data_now': self.ui.save_data_now,
                'tot_rh_seq_time': self.ui.tot_rh_seq_time,
                'elapsed_rh_seq_time': self.ui.elapsed_rh_seq_time,
                'seq_end_time_display': self.ui.seq_end_time_display}

        # dictionary to hold Solartron 1260 impedancee analyzer related items
        self.eis_dict = {
                'eis_dev': None,
                'new_data': None,
                'eis_df': self.eis_df,
                'eis_on': self.ui.eis_on,
                'eis_busy': self.eis_busy,
                'ac_bias': self.ui.ac_bias,
                'eis_time': self.ui.eis_time,
                'start_date': self.start_date,
                'dc_offset': self.ui.dc_offset,
                'end_freq': self.ui.end_eis_freq,
                'output_box': self.ui.output_box,
                'eis_points': self.ui.eis_points,
                'eis_rh_seq': self.ui.eis_rh_seq,
                'actual_z': self.ui.actual_eis_z,
                'eis_vac_seq': self.ui.eis_vac_seq,
                'averaging': self.ui.eis_averaging,
                'save_file_dir': self.save_file_dir,
                'start_freq': self.ui.start_eis_freq,
                'actual_freq': self.ui.actual_eis_freq,
                'actual_phase': self.ui.actual_eis_phase,
                'pause_after_eis': self.ui.pause_after_eis,
                'solartron_address': self.ui.solartron_address}

        # dictionary to hold Ocean Optics USB4000 spectrometer related items
        self.spec_dict = {
                'spec_dev': None,
                'spec_busy': False,
                'spec_smoothing': None,
                'spec_on': self.ui.spec_on,
                'optical_df': self.optical_df,
                'start_date': self.start_date,
                'output_box': self.ui.output_box,
                'optical_box': self.ui.optical_box,
                'save_file_dir': self.save_file_dir,
                'spec_int_time': self.ui.spec_int_time,
                'max_intensity': self.ui.max_intensity,
                'set_spec_pause': self.ui.set_spec_pause,
                'measure_button': self.ui.get_opt_spectrum,
                'wavelength_at_max': self.ui.wavelength_at_max}

        # dictionary to hold Keithley 2400 related items
        self.keith_dict = {
                'new_data': None,
                'keith_dev': None,
                'iv_df': self.iv_df,
                'cv_df': self.cv_df,
                'bs_df': self.bs_df,
                'keith_seq_running': False,
                'set_bias': self.ui.set_bias,
                'max_bias': self.ui.max_bias,
                'keith_busy': self.keith_busy,
                'start_date': self.start_date,
                'iv_rh_seq': self.ui.iv_rh_seq,
                'cv_rh_seq': self.ui.cv_rh_seq,
                'bs_rh_seq': self.ui.bs_rh_seq,
                'iv_vac_seq': self.ui.iv_vac_seq,
                'cv_vac_seq': self.ui.cv_vac_seq,
                'bs_vac_seq': self.ui.bs_vac_seq,
                'output_box': self.ui.output_box,
                'actual_bias': self.ui.actual_bias,
                'keithley_on': self.ui.keithley_on,
                'save_file_dir': self.save_file_dir,
                'voltage_steps': self.ui.voltage_steps,
                'keith_address': self.ui.keith_address,
                'cv_sweep_rates': self.ui.cv_sweep_rates,
                'measure_iv_now': self.ui.measure_iv_now,
                'measure_cv_now': self.ui.measure_cv_now,
                'bias_seq_table': self.ui.bias_seq_table,
                'electrical_box': self.ui.electrical_box,
                'current_display': self.ui.current_display,
                'menu_electrical': self.ui.menu_electrical,
                'pause_after_cycle': self.ui.set_keith_pause,
                'measure_current_now': self.ui.measure_current_now,
                'measure_bias_seq_now': self.ui.measure_bias_seq_now}

        # dictionary to hold SARK-110 QCM related items
        self.sark_dict = {
                'new_data': None,
                'sark_dev': None,
                'nth_qcm_loop': 0,
                'qcm_rs': self.ui.qcm_rs,
                'qcm_xs': self.ui.qcm_xs,
                'set_f0': self.ui.set_f0,
                'qcm_data': self.qcm_data,
                'sark_on': self.ui.sark_on,
                'qcm_box': self.ui.qcm_box,
                'sark_busy': self.sark_busy,
                'start_date': self.start_date,
                'dynamic_bc': self.ui.dynamic_bc,
                'output_box': self.ui.output_box,
                'save_file_dir': self.save_file_dir,
                'sec_per_band': self.ui.sec_per_band,
                'measure_bands': self.ui.measure_bands,
                'find_resonances': self.ui.find_resonances,
                'set_band_points': self.ui.set_band_points,
                'actual_frequency': self.ui.actual_frequency,
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

        # set up real-time graphs
        self.press_graph = realtimeplot.MakeGraph(
                title='Pressure', xlabel='Time (min)', ylabel='Press. (Torr)')

        self.qcm_graph = realtimeplot.MakeGraph(
                title='QCM', xmax=1000, xlabel='Freq. (MHz)', ylabel='G (mS)')

        self.qcm_fit_graph = realtimeplot.MakeGraph(
                title='QCM fitting', xmax=1000,
                xlabel='Freq. (MHz)', ylabel='G (mS)')

        self.rh_graph = realtimeplot.MakeGraph(
                title='RH', xlabel='Time (min)', ylabel='RH (%)')

        self.eis_graph = realtimeplot.MakeGraph(
                title='EIS', xlabel='Frequency (Hz)', ylabel='Z (Ohm)')

        self.keith_graph_cv = realtimeplot.MakeGraph(
                title='Keithley', xlabel='Voltage (V)', ylabel='Current (A)')

# %% ----------- system control functions ------------------------------

    def main_loop(self):
        # Main loop to execute which keeps the app running.
        # wait until the file saving directory is set to do anything
        if self.save_file_dir is not None:

            # auto scroll to bottom of output box at each main loop iteration
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)

            # set and measure RH
            self.set_rh()
            if self.rh_dict['rh200_on'].isChecked():
                if self.rh_dict['current_rh'] is not None:
                    self.rh_graph.append_data([
                            self.ops_dict['elapsed_time'],
                            self.rh_dict['current_rh']])
                    self.rh_graph.show()

            # control and measure vacuum chamber pressure and plot pressure
            self.vac_main()
            if self.vac_dict['mks_on'].isChecked():
                if self.vac_dict['current_pressure'] is not None:
                    self.press_graph.append_data([
                            self.ops_dict['elapsed_time'],
                            self.vac_dict['current_pressure']])
                    self.press_graph.show()

            # measure and plot electrical current
            if self.ui.keithley_on.isChecked():
                if self.ui.measure_current_now.isChecked():
                    self.measure_current()
                if self.keith_dict['keith_busy']:
                    if self.keith_dict['new_data'] is not None:
                        self.keith_graph_cv.add_data(
                                self.keith_dict['new_data'])
                        self.keith_graph_cv.show()

            # show EIS plot
            if self.eis_dict['eis_on'].isChecked():
                if self.eis_dict['eis_busy']:
                    if self.eis_dict['new_data'] is not None:
                        self.eis_graph.add_data(self.eis_dict['new_data'])
                        self.eis_graph.show()

            # show QCM plot
            if self.sark_dict['sark_on'].isChecked():
                if self.sark_dict['sark_busy']:
                    if self.sark_dict['new_data'] is not None:
                        self.qcm_graph.xmax = len(self.sark_dict['new_data'])
                        self.qcm_graph.add_data(self.sark_dict['new_data'])
                        self.qcm_graph.show()

            # ################################################################
            # ------ control functionality when vacuum sequence is running ---
            # ################################################################
            if self.vac_dict['vac_seq_running']:

                # run Keithley functions for RH sequence
                self.keith_vac_seq()

                # run impedance spectroscopy
                self.eis_vac_seq()

                # measure QCM
                if self.ui.qcm_vac_seq.isChecked():
                    if not self.sark_dict['sark_busy']:
                        self.measure_bands()

                # measure optical
                if self.ui.optical_vac_seq.isChecked():
                    if not self.spec_dict['spec_busy']:
                        self.optical_vac_seq()

            # ################################################################
            # ------ control functionality when RH sequence is running -------
            # ################################################################
            if self.rh_dict['rh_seq_running']:

                # run Keithley functions for RH sequence
                self.keith_rh_seq()

                # run impedance spectroscopy
                self.eis_rh_seq()

                # measure QCM
                if self.ui.qcm_rh_seq.isChecked():
                    if not self.sark_dict['sark_busy']:
                        self.measure_bands()

                # measure optical
                if self.ui.optical_rh_seq.isChecked():
                    if not self.spec_dict['spec_busy']:
                        self.optical_rh_seq()

            # update fields, normal operations, and saving in main loop
            self.df, self.df_i = ops.main_loop_update(
                    self.ops_dict, self.df, self.df_i)

    def list_devices(self):
        # list all connected devices in the GUI output box
        ops.list_devices(self.ops_dict)

    def set_file_save_directory(self):
        # set the directory for saving data files
        self.save_file_dir = str(QFileDialog.getExistingDirectory(
                self, 'Create or select directory for data files.'))
        self.ui.output_box.append('Save file directory set to:')
        self.ui.output_box.append(self.save_file_dir)

    def create_report(self):
        # Create Origin report of saved experimental data. This method
        # opens Origin, runs an internal Origin python script, imports
        # the saved data files, plots them, and saves the Origin file.
        Thread(target=ops.create_report, args=(self.ops_dict,)).start()

    def view_file_save_dir(self):
        # Print the file saving directory to the output box on GUI.
        ops.view_file_save_dir(self.keith_dict)

    def view_app_starttime(self):
        # Print start time o application in output box.
        ops.view_app_starttime(self.ops_dict)

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
            rh200.close(self.rh_dict['rh_task_dict'])
        if self.ui.eis_on.isChecked():
            self.eis_dict['eis_dev'].close()
        if self.ui.mks_on.isChecked():
            self.vac_dict['mks_dev'].close()
        if self.ui.mfc1_on.isChecked():
            self.vac_dict['mfc1_dev'].close()
        if self.ui.mfc2_on.isChecked():
            self.vac_dict['mfc2_dev'].close()
        if self.ui.turbo_on.isChecked():
            self.vac_dict['turbo_dev'].close()

        if self.ui.create_report_on_quit.isChecked():
            try:
                self.create_report()
            except NameError:
                print('ERROR CREATING ORIGIN REPORT')

        plt.close('all')  # close all figures
        self.deleteLater()
        self.timer.stop()  # stop timer
        self.close()  # close app window
        sys.exit()  # kill python kernel

    def export_settings(self):
        # export all GUI settings to file
        ops.export_settings(self.ops_dict)

    def import_settings(self):
        # import all GUI settings from file
        import_settings_filepath = QFileDialog.getOpenFileName(
                self, 'Select experiment settings file', '.ini')[0]
        ops.import_settings(self.ops_dict, import_settings_filepath)

# %% ----functions for controlling vacuum chamber pressure using MFCs ---

    def mfc1_checked(self):
        # run this funtion when MFC-1 checkbox is checked
        vac.mfc1_checked(self.vac_dict)

    def mfc2_checked(self):
        # run this funtion when MFC-2 checkbox is checked
        vac.mfc2_checked(self.vac_dict)

# %% -------------functions for Leybold Turbovac 90i turbo pump ------------

    def turbo_checked(self):
        # run this when turbo pump checkbox is checked/unchecked
        vac.turbo_checked(self.vac_dict)

# %% ----functions for controlling vacuum chamber pressure using MKS 651 ---

    def mks_checked(self):
        # run this function when the MKS-651 pressure controller box is checked
        vac.mks_checked(self.vac_dict)

    def vac_main(self):
        # set pressure and flow rates in vacuum chamber
        Thread(target=vac.vac_main, args=(self.vac_dict,
                                          self.df, self.df_i)).start()

    def stop_vac_seq(self):
        # Stop vacuum sequence
        self.vac_dict['vac_seq_running'] = False

    def run_vac_seq(self):
        # Run the vacuum sequence
        Thread(target=vac.run_vac_seq, args=(self.vac_dict,)).start()
        if self.ui.export_settings_at_seq.isChecked():
            self.export_settings()

    def import_vac_seq(self):
        # Import a saved vacuum sequence from file
        seq_name = QFileDialog.getOpenFileName(
                self, 'Select vacuum sequence file', '.csv')[0]
        vac.import_vac_seq(self.vac_dict, seq_name)

    def export_vac_seq(self):
        # Export a vacuum sequence from the sequence table to a file
        seq_name = QFileDialog.getSaveFileName(
                self, 'Export vacuum sequence file', '.csv')[0]
        vac.export_vac_seq(self.vac_dict, seq_name)

    def clear_vac_seq(self):
        # Clear the vacuum sequence from the GUI table
        vac.clear_vac_seq(self.vac_dict)

    def plot_vac_seq(self):
        # Show plot of the vacuum sequence over time
        vac.plot_vac_seq(self.vac_dict)

    def plot_pressure(self):
        # plot the pressure of the chaber over time
        vac.plot_pressure(self.df, self.df_i)

# %% functions for impedance spectroscopy measurements using Solartron 1260 --

    def eis_checked(self):
        # Run this function when Solartron 1260 checkbox status changes.
        eis.eis_checked(self.eis_dict)

    def preview_eis_freqs(self):
        # display the frequencies to be used for impedance measurement.
        eis.preview_eis_freqs(self.eis_dict)

    def plot_phase(self):
        # plot impedance phase over time
        eis.plot_phase(self.eis_dict)

    def plot_z(self):
        # plot impedance over time
        eis.plot_z(self.eis_dict)

    def plot_nyquist(self):
        # plot Nyquist impedance traces over time
        eis.plot_nyquist(self.eis_dict)

    def measure_eis(self):
        # measure impedance spectrum
        Thread(target=eis.measure_eis, args=(self.eis_dict,
                                             self.df,
                                             self.df_i)).start()

    def eis_rh_seq(self):
        # measure impedance spectrum repeatedly during RH sequence
        if self.ui.eis_rh_seq.isChecked():
            if not self.eis_dict['eis_busy']:
                Thread(target=eis.eis_rh_seq, args=(self.eis_dict,
                                                    self.df,
                                                    self.df_i)).start()

    def eis_vac_seq(self):
        # measure impedance spectrum repeatedly during vacuum sequence
        if self.ui.eis_vac_seq.isChecked():
            if not self.eis_dict['eis_busy']:
                Thread(target=eis.eis_rh_seq, args=(self.eis_dict,
                                                    self.df,
                                                    self.df_i)).start()

    def plot_low_freq_z(self):
        # plot lowest-frequency impedance over time
        eis.plot_low_freq_z(self.eis_dict, self.df, self.df_i)

    def clear_ac_data(self):
        # clear AC electrical data
        self.eis_dict['eis_df'] = pd.DataFrame()

# %% --- functions for QCM measurements using SARK-110 antenna analyzer ------

    def sark_checked(self):
        # This function triggers when SARK-110 checkbox status changes.
        sark.checked(self.sark_dict)

    def find_resonances(self):
        # Find resonance peak at each QCM harmonic by sweeping across bands
        # sark.find_resonances(self.sark_dict)
        Thread(target=sark.find_resonances, args=(self.sark_dict,)).start()

    def measure_bands(self):
        # Measure across frequency bands as set by fields on GUI.
        # sark.measure_bands(self.sark_dict)
        Thread(target=sark.measure_bands, args=(self.sark_dict,)).start()

    def plot_deltaf(self):
        # plot all frequency shift data acquired by the SARK-110.
        sark.plot_deltaf(self.sark_dict)

    def plot_deltad(self):
        # plot all dissipation data acquired by the SARK-110.
        sark.plot_deltad(self.sark_dict)

    def plot_qcm_spectra(self):
        # plot QCM spectra based on which harmonic is selected on GUI
        sark.plot_qcm_spectra(self.sark_dict)

    def clear_qcm_data(self):
        # clear all QCM data
        self.sark_dict['nth_qcm_loop'] = 0
        self.sark_dict['qcm_data'] = {
                str(i): pd.DataFrame() for i in range(1, 19, 2)}
        self.sark_dict['qcm_data']['params'] = pd.DataFrame(
                data=np.full((10000, 19), ''),
                columns=['time', 'f_1', 'f_3', 'f_5', 'f_7', 'f_9',
                         'f_11', 'f_13', 'f_15', 'f_17',
                         'd_1', 'd_3', 'd_5', 'd_7', 'd_9',
                         'd_11', 'd_13', 'd_15', 'd_17'])

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

    def print_cv_biases(self):
        # print and display biases used for C-V measurements
        keith.print_cv_biases(self.keith_dict)

    def measure_iv(self):
        # Measure I-V curve using Keithley multimeter.
        # keith.measure_iv(self.keith_dict)
        Thread(target=keith.measure_iv, args=(self.keith_dict,
                                              self.df,
                                              self.df_i,)).start()

    def measure_cv(self):
        # Measure C-V curve using Keithley multimeter.
        # keith.measure_cv(self.keith_dict)
        Thread(target=keith.measure_multi_cv, args=(self.keith_dict,
                                                    self.df,
                                                    self.df_i,)).start()

    def plot_bias_seq(self):
        # plot the bias sequence
        keith.plot_bias_seq(self.keith_dict)

    def measure_bias_seq(self):
        # measure current during a sequence of changing biases
        # keith.measure_bias_seq(self.keith_dict)
        Thread(target=keith.measure_bias_seq, args=(self.keith_dict,
                                                    self.df,
                                                    self.df_i,)).start()

    def keith_rh_seq(self):
        # run keithley functions during RH sequence
        if self.ui.keithley_on.isChecked():
            if not self.keith_dict['keith_busy']:
                Thread(target=keith.keith_rh_seq,
                       args=(self.keith_dict, self.df, self.df_i,)).start()

    def keith_vac_seq(self):
        # run keithley functions during vacuum sequence
        if self.ui.keithley_on.isChecked():
            if not self.keith_dict['keith_busy']:
                Thread(target=keith.keith_vac_seq,
                       args=(self.keith_dict, self.df, self.df_i,)).start()

    def view_iv_data(self):
        # view all I-V data in one plot
        keith.view_iv_data(self.keith_dict)

    def view_cv_data(self):
        # view all C-V data in one plot
        keith.view_cv_data(self.keith_dict)

    def plot_current(self):
        # plot Keithley current over time
        keith.plot_current(self.df)

    def view_bs_data(self):
        # view all bias-sequence data in one plot
        keith.view_bs_data(self.keith_dict)

    def iv_max_vs_time(self):
        # plot I-V maximum current over time
        keith.iv_max_vs_time(self.keith_dict, self.df, self.df_i)

    def cv_max_vs_time(self):
        # plot I-V maximum current over time
        keith.cv_max_vs_time(self.keith_dict, self.df, self.df_i)

    def cv_area_vs_time(self):
        # plot I-V maximum current over time
        keith.cv_area_vs_time(self.keith_dict, self.df, self.df_i)

    def clear_dc_data(self):
        # clear DC electrical data
        self.keith_dict['iv_df'] = pd.DataFrame()
        self.keith_dict['cv_df'] = pd.DataFrame()
        self.keith_dict['bs_df'] = pd.DataFrame()

# %% ---------- functions for RH control and sequence ------------------

    def set_rh(self):
        # measure and set RH using RH generator
        if self.ui.rh200_on.isChecked():
            Thread(target=rh200.set_rh, args=(self.rh_dict,
                                              self.df,
                                              self.df_i,)).start()

    def rh200_checked(self):
        # Triggers when RH-200 humidity generator checkbox status changes.
        rh200.checked(self.rh_dict)

    def import_rh_seq(self):
        # Import a saved RH sequence from file
        seq_name = QFileDialog.getOpenFileName(
                self, 'Select RH sequence file', '.csv')[0]
        rh200.import_rh_seq(self.rh_dict, seq_name)

    def export_rh_seq(self):
        # Export an RH sequence from the sequence table to a file
        seq_name = QFileDialog.getSaveFileName(
                self, 'Export RH sequence file', '.csv')[0]
        rh200.export_rh_seq(self.rh_dict, seq_name)

    def clear_rh_seq(self):
        # Clear the RH sequence from the GUI table
        rh200.clear_rh_seq(self.rh_dict)

    def plot_rh_seq(self):
        # Show plot of the RH over time
        rh200.plot_rh_seq(self.rh_dict)

    def plot_rh(self):
        rh200.plot_rh(self.df, self.df_i)

    def stop_rh_seq(self):
        # Stop RH sequence
        self.rh_dict['rh_seq_running'] = False

    def run_rh_seq(self):
        # Run the RH sequence
        Thread(target=rh200.run_rh_seq, args=(self.rh_dict,)).start()
        if self.ui.export_settings_at_seq.isChecked():
            self.export_settings()

    def add_rh_step(self):
        # add a RH step to the end of the RH sequence
        rh200.add_rh_step(self.rh_dict)

# %% --- functions for Ocean Optics USB4000 optical spectrometer -----------
    def spec_checked(self):
        # spectrometer check box is checked / unchecked
        spec.spec_checked(self.spec_dict)

    def get_optical_spectrum(self):
        # acquire optical spectrum
        Thread(target=spec.get_spec, args=(self.spec_dict,)).start()

    def optical_rh_seq(self):
        # acquire multiple optical spectra during sequence
        Thread(target=spec.optical_rh_seq, args=(self.spec_dict,)).start()

    def plot_optical_spectra(self):
        # plot optical optical spectra
        spec.plot_optical_spectra(self.spec_dict)

    def clear_optical_data(self):
        # clear optical data
        self.spec_dict['optical_df'] = pd.DataFrame()


# %% -------------------------- run application ----------------------------


if __name__ == '__main__':
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()

    window = App()
    window.show()
    sys.exit(app.exec_())
