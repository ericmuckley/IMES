# -*- coding: utf-8 -*-
"""
This module communicates with the Harward PHD200 infuse syringe pump
The functions which control the pump are from GitHub library pumpy

The module also provides methods related to creating concentration sequences
for automated long-term control of experimnet

Packages required:
time
numpy
PyQt5
nidaqmx
pumpy

Created on Thurstday Jul 11 17:13:59 2019

@author: marekvidis@gmail.com
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
from imes_libs import pumpy as pumpy # module for syringe pump communication
fontsize = 12

# suppress NI DAQ warning:
# Finite acquisition or generation has been stopped before the requested
# number of samples were acquired or generated.
# error_buffer.value.decode("utf-8"), error_code)
# DaqWarning: Warning 200010 occurred.
warnings.filterwarnings('ignore', category=nidaqmx.DaqWarning)

def close(syr_dict):
    # stop pump if infusing and close serial port
    if syr_dict['syr_pump'] is not None: syr_dict['syr_pump'].stop()
    if syr_dict['syr_chain'] is not None: syr_dict['syr_chain'].close()
    print("syringe pump closed")

def checked(syr_dict):
    # Triggers when syringe box is checked or unchecked on the GUI.
    if syr_dict['syr_on'].isChecked():  # if box was checked
        try:
            chain = pumpy.Chain(str(syr_dict['syr_address'].text()))
            syr_dict['syr_chain'] = chain
            syr_dict['syr_pump'] = pumpy.PHD2000(chain, address=1)
            syr_dict['output_box'].append(
                    'syringe pump connected')
            syr_dict['run_syr_seq'].setEnabled(True)
            syr_dict['infuse_on'].setEnabled(True)
            
        except NameError:
            syr_dict['output_box'].append(
                    'Syringe pump connection failed, please restart')

    if not syr_dict['syr_on'].isChecked():  # if box was unchecked
        if syr_dict['syr_pump'] is not None: syr_dict['syr_pump'].stop()
        if syr_dict['syr_chain'] is not None: syr_dict['syr_chain'].close()
        syr_dict['syr_seq_running'] = False
        syr_dict['infuse_on'].setEnabled(False)
        syr_dict['syr_flow_display'].setText('--')
        syr_dict['output_box'].append('syringe pump disconnected')


def set_flow(syr_dict, df, df_i):
    # append values to main GUI dataframe
    df['anl_conc'].iloc[df_i] = str(syr_dict['syr_conc_set'].value())
    df['syr_flow'].iloc[df_i] = syr_dict['syr_flow_display'].text()
    df['rh_setpoint'].iloc[df_i] = str(syr_dict['wet_rat_set'].value())
    
    if syr_dict['syr_seq_running']:
        syr_dict['mfc1_sp'].setValue(float(syr_dict['mfc1_flow_display'].text()))
        syr_dict['mfc2_sp'].setValue(float(syr_dict['mfc2_flow_display'].text()))
    # update syringe sequence on GUI
    update_ui(syr_dict)

def plot_syr(df, df_i):
    # Plot the syringe sequence over time
    syr_df = df[df['syr'] != '']
    setpoint = syr_df['syr_setpoint'].astype(float)
    syr = syr_df['syr'].astype(float)
    syr_time = syr_df['time'].astype(float)
    fig_seq = plt.figure(20)
    plt.cla()
    plt.ion()
    plt.plot(syr_time/60, syr, c='b', label='measured')
    plt.plot(syr_time/60, setpoint, c='r', label='setpoint')
    plt.xlabel('Time (hours)', fontsize=12)
    plt.ylabel('Concentration (ppm)', fontsize=12)
    plt.legend(fontsize=12)
    plt.tight_layout()
    fig_seq.canvas.set_window_title('Concentration over time')
    fig_seq.show()


# -----These functions are related to the syringe sequence --------------------


def syr_table_to_df(syr_dict):
    # Convert syringe sequence table on GUI to a Pandas dataframe
    # create empty dataframe
    syr_df = pd.DataFrame(
            columns=['time', 'syr', 'rat'],
            index=range(syr_dict['syr_table'].rowCount()))

    # loop over table entries
    for rowi in range(syr_dict['syr_table'].rowCount()):
        for colj in range(syr_dict['syr_table'].columnCount()):
            # populate dataframe with table entries
            new_entry = syr_dict['syr_table'].item(rowi, colj).text()
            syr_df.iloc[rowi, colj] = new_entry
    # delete empty rows
    syr_df = syr_df[syr_df['time'] != '0']
    return syr_df.astype(float)


def plot_syr_seq(syr_dict):
    # plot the syr sequence
    try:
        syr_df = syr_table_to_df(syr_dict)
        seq_time = np.array(syr_df['time'].astype(float))
        plot_seq_time = np.insert(np.cumsum(seq_time), 0, 0)/60
        seq_syr = np.array(syr_df['syr'].astype(float))
        plot_seq_syr = np.insert(seq_syr, 0, seq_syr[0])
        fig_seq = plt.figure(1)
        plt.cla()
        plt.ion()
        plt.fill_between(plot_seq_time,
                         plot_seq_syr,
                         step='pre', alpha=0.6)
        plt.plot(plot_seq_time,
                 plot_seq_syr,
                 c='r', drawstyle='steps', alpha=0)
        plt.xlabel('Time (hours)', fontsize=12)
        plt.ylabel('Concentration (ppm)', fontsize=12)
        plt.tight_layout()
        fig_seq.canvas.set_window_title('Syringe sequence')
        fig_seq.show()
    except NameError:
        syr_dict['output_box'].append('Syringe sequence not valid.')


def import_syr_seq(syr_dict, seq_name):
    # import syr sequence from file
    imported_seq = pd.read_csv(seq_name)
    # populate table on GUI
    for rowi in range(len(imported_seq)):
        for colj in range(len(imported_seq.columns)):
            syr_dict['syr_table'].setItem(
                    rowi, colj,
                    QtWidgets.QTableWidgetItem(
                            str(imported_seq.iloc[rowi, colj])))
    syr_dict['output_box'].append('syr sequence file imported.')


def export_syr_seq(syr_dict, seq_name):
    # export syr sequence to file
    syr_df = syr_table_to_df(syr_dict)
    syr_df.to_csv(str(seq_name), index=False)
    syr_dict['output_box'].append('Syringe sequence file exported.')


def clear_syr_seq(syr_dict):
    # clear pressure sequence by populating the sequence table with 0's
    for rowi in range(syr_dict['syr_table'].rowCount()):
        for colj in range(syr_dict['syr_table'].columnCount()):
            syr_dict['syr_table'].setItem(
                    rowi, colj,
                    QtWidgets.QTableWidgetItem('0'))
    syr_dict['output_box'].append('Syringe sequence cleared.')


def run_syr_seq(syr_dict, vac_dict = None):
    # run syr sequence
    syr_dict['output_box'].append('Syringe sequence initiated.')
    syr_dict['syr_seq_running'] = True
    syr_dict['run_syr_seq'].setEnabled(False)
    syr_dict['save_data_now'].setChecked(True)
    syr_dict['syr_conc_set'].setEnabled(False)
    syr_dict['wet_rat_set'].setEnabled(False)
    syr_dict['infuse_on'].setEnabled(False)
    syr_dict['syr_table'].setEnabled(False)
    syr_df = syr_table_to_df(syr_dict)
    tot_seq_time = syr_df['time'].sum()
    tot_time_disp = str(np.round(tot_seq_time, decimals=1))
    # set up timers and counters
    elapsed_seq_time = 0
    seq_start_time = time.time()

    tot_seq_min = syr_df['time'].sum()
    seq_start_date = datetime.datetime.now()
    seq_end_date = seq_start_date + datetime.timedelta(
                                               minutes=tot_seq_min)
    syr_dict['seq_end_time_display'].setText(
           seq_end_date.strftime('%m-%d %H:%M:%S'))

    step_num = 0
    
    # loop over each step in sequence
    for step in range(len(syr_df)):

        if syr_dict['syr_seq_running']:
            syr_dict['syr_conc_set'].setValue(float(syr_df['syr'].iloc[step]))
            syr_dict['wet_rat_set'].setValue(float(syr_df['rat'].iloc[step]))
            calc(syr_dict)
            print('\n step %d, concetration %s' %(step, syr_df['syr'].iloc[step]))
            syr_dict['mfc1_sp'].setValue(float(syr_dict['mfc1_flow_display'].text()))
            syr_dict['mfc2_sp'].setValue(float(syr_dict['mfc2_flow_display'].text()))
            if float(syr_dict['syr_conc_set'].value()) > 0:
                tx_flow(syr_dict)
                if not syr_dict['infusing']: infuse(syr_dict)
            if float(syr_dict['syr_conc_set'].value()) > 0 and not syr_dict['infusing']:
                infuse(syr_dict)
            if float(syr_dict['syr_conc_set'].value()) == 0 and syr_dict['infusing']:
                stop_infusing(syr_dict)
            step_start_time = time.time()
            elapsed_step_time = 0
            step_dur = syr_df['time'].iloc[step]*60
        else:
            break
        # repeat until step duration has elapsed
        while elapsed_step_time < step_dur:

            if syr_dict['syr_seq_running']:
                elapsed_step_time = time.time() - step_start_time
                elapsed_seq_time = time.time() - seq_start_time

                # update fields on GUI
                if step_num % 5 == 0:
                    syr_dict['save_data_now'].setChecked(True)
                    syr_dict['syr_seq_step'].setText(
                            str(int(step+1))+'/'+str(len(syr_df)))

                    syr_dict['syr_conc_set'].setValue(float(syr_df['syr'].iloc[step]))

                    elasped_time_disp = str(
                            np.round(elapsed_seq_time/60, decimals=2))

                    syr_dict['elapsed_syr_seq_time'].setText(
                            elasped_time_disp + '/' + tot_time_disp)

                time.sleep(.5)
                step_num += 1
            else:
                break

    if syr_dict['infusing']: stop_infusing(syr_dict)        
    syr_dict['syr_seq_step'].setText('0')
    syr_dict['syr_conc_set'].setValue(2)
    syr_dict['elapsed_syr_seq_time'].setText('0')
    syr_dict['output_box'].append('Syringe sequence completed.')
    syr_dict['syr_seq_running'] = False
    syr_dict['run_syr_seq'].setEnabled(True)
    syr_dict['syr_conc_set'].setEnabled(True)
    syr_dict['wet_rat_set'].setEnabled(True)
    syr_dict['infuse_on'].setEnabled(True)
    syr_dict['syr_table'].setEnabled(True)
    syr_dict['save_data_now'].setChecked(False)

def calc(syr_dict):
    Qt = float(syr_dict['tot_flow_set'].value()) # total gas mixture flow
    R =  float(syr_dict['wet_rat_set'].value()) # wet branch carrier gas flow
    c = float(syr_dict['syr_conc_set'].value()) # desired analyte concentration
    cg = float(syr_dict['anl_conc_set'].value()) # analyte concentration in syringe
    if not syr_dict['syr_fix_car_flow'].isChecked():
        Qa = 1.0*Qt*c/cg    # analyte flow # pressure and themperature correstion to calculate from ml pre minute to sccm yet to be done
        Qd = (Qt-Qa)*(1-R)  # dry carrier gas flow
        Qw = (Qt-Qa)*R      # wet carrier gas flow
    
    if syr_dict['syr_fix_car_flow'].isChecked():
        Qd = Qt        # dry air is set
        if R < 1: Qw = Qd*R/(1-R)      # wet carrier gas flow
        else: Qw = 0
        if Qw > 50: Qw = 50
        Qt = Qd + Qw
        Qa = 1.0*Qt*c/cg    # analyte flow
    
    syr_dict['syr_flow_display'].setText(str(Qa))  # analyte flow
    syr_dict['mfc1_flow_display'].setText(str(Qd)) # dry carrier gas flow
    syr_dict['mfc2_flow_display'].setText(str(Qw)) # wet carrier gas flow

def update_ui(syr_dict):
    # update syringe sequence duration on GUI
    syr_df = syr_table_to_df(syr_dict)
    seq_time = syr_df['time'].sum()
    syr_dict['tot_syr_seq_time'].setText(
            str(np.round(int(seq_time)/60, decimals=2)))
        
    # display estimated sequence end time
    if not syr_dict['syr_seq_running']:
        tot_seq_min = syr_df['time'].sum()
        seq_start_date = datetime.datetime.now()
        seq_end_date = seq_start_date + datetime.timedelta(minutes=tot_seq_min)
        syr_dict['seq_end_time_display'].setText(
                seq_end_date.strftime('%m-%d %H:%M:%S'))
        volume = 0
        for line in range(len(syr_df)):
            t = float(syr_df['time'].iloc[line]) # time in minutes
            c = float(syr_df['syr'].iloc[line]) # desired conc in ppm
            Qt = float(syr_dict['tot_flow_set'].value()) # total gas mixture flow
            #R =  float(syr_dict['wet_rat_set'].value()) # wet branch carrier gas flow
            cg = float(syr_dict['anl_conc_set'].value()) # analyte concentration in syringe
        
            Qa = 1.0*Qt*c/cg    # analyte flow # pressure and themperature correstion to calculate from ml pre minute to sccm yet to be done
            #Qd = (Qt-Qa)*(1-R)  # dry carrier gas flow
            #Qw = (Qt-Qa)*R      # wet carrier gas flow
            volume += Qa * t
        syr_dict['tot_syr_vol'].setText(str(volume))

def infuse(syr_dict):

    if syr_dict['syr_pump'] is not None:        
        syr_dict['syr_pump'].infuse()
        syr_dict['infusing'] = True
    else: print('pump not connected')
    
def stop_infusing(syr_dict):
    if syr_dict['syr_pump'] is not None:
        syr_dict['syr_pump'].stop()
        syr_dict['infusing'] = False
    else: print('pump not connected')
    
def tx_flow(syr_dict):
    calc(syr_dict)
    Qa = float(syr_dict['syr_flow_display'].text()) # analyte flow
    if syr_dict['syr_pump'] is not None:
        syr_dict['syr_pump'].setflowrate(Qa*1000)
    else: print('pump not connected')
    
# TEST PHD2000 infuse syringe pump BY RUNNING THIS MODULE
if __name__ == '__main__':

    print("Syringe test module run")