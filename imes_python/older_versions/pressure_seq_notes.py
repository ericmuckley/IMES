# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 13:24:56 2019

@author: a6q
"""


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
