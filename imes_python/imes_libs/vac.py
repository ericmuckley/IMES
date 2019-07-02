# -*- coding: utf-8 -*-
"""
This module controls instruments which monitor and control
the pressure and gas/vapor flow into a vacuum chamber.

Pressure control requires the MKS 600 series (651) pressure controller,
which should be connected to the MKS butterfly valve and MKS 972 dual-mag
pressure transducers .

Created on Mon Apr 22 13:12:13 2019

@author: ericmuckley@gmail.com
"""

import time
import visa
import serial
import datetime
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
# instrument libraries
# from alicat import FlowController


# %% ------ Funtions to control Leybold Turbovac 90i turbo pump--------------

def turbo_checked(vac_dict):
    # run this function when turbo pump checkbox is checked/unchecked on GUI
    if vac_dict['mks_on'].isChecked():
        if vac_dict['turbo_on'].isChecked():
            vac_dict['turbo_dev'] = serial.Serial(
                    vac_dict['turbo_address'].text(), 19200, timeout=1.0)
            vac_dict['output_box'].append('Turbo pump connected')
        if not vac_dict['turbo_on'].isChecked():
            vac_dict['turbo_dev'].close()
            vac_dict['output_box'].append('Turbo pump disconnected')
    else:
        vac_dict['output_box'].append(
                'Pressure controller must be on to run turbo pump.')
        vac_dict['turbo_on'].setChecked(False)

def operate_turbo(vac_dict, run_pump=False):
    # turn trubo pump on/off and read pump rotor speed in Hz
    first_half = '02 16 00 10 18 00 00 00 00 00 00 04 '
    on_str = first_half + '01 00 00 00 00 00 00 00 00 00 00 19'
    off_str = first_half + '00 00 00 00 00 00 00 00 00 00 00 18'
    if run_pump:
        # turn pump on
        vac_dict['turbo_dev'].write(bytes.fromhex(on_str))

    else:
        # turn pump off
        vac_dict['turbo_dev'].write(bytes.fromhex(off_str))
    # read pump speed
    read_message = vac_dict['turbo_dev'].readline().hex()
    turbo_speed = ((eval("0x"+read_message) & 0xffff000000000000000000) >> 72)
    # print(read_message)
    # print(turbo_speed)
    vac_dict['turbo_speed'].setText(str(turbo_speed))


# %% ------------ These functions control MKS 651 pressure controller
# with butterfly valve and dual-mag pressure transducers


def mks_checked(vac_dict):
    # run this function when the MKS box is checked to connect or disconnect
    # the MKS-651 pressure controller.
    if vac_dict['mks_on'].isChecked():
        try:
            rm = visa.ResourceManager()
            # list all resources connected to PC
            # print(rm.list_resources())
            # create instance of MKS instrument
            mks = rm.open_resource(vac_dict['mks_address'].text())
            vac_dict['mks_dev'] = mks
            vac_dict['output_box'].append('MKS-651 connected.')
            vac_dict['mks_address'].setEnabled(False)
            # vac_dict['menu_vacuum'].setEnabled(True)
        except NameError:
            vac_dict['output_box'].append('MKS-651 could not connect.')
            vac_dict['mks_on'].setChecked(False)
            vac_dict['mks_address'].setEnabled(True)
            # vac_dict['menu_vacuum'].setEnabled(False)
    if not vac_dict['mks_on'].isChecked():
        vac_dict['mks_address'].setEnabled(True)
        try:
            vac_dict['mks_dev'].close()
            vac_dict['output_box'].append('MKS-651 disconnected.')
            # vac_dict['menu_vacuum'].setEnabled(False)
        except NameError:
            vac_dict['mks_on'].setChecked(False)
            # vac_dict['menu_vacuum'].setEnabled(False)


def set_valve_pos(dev, position):
    # set the butterfly valve position using MKS 651 pressure controller
    # select setpoint C
    dev.write('D3')
    # set setpoint C to valve mode
    dev.write('T30')
    # set setpoint C position of valve in terms of % open
    dev.write('S3'+str(position))


def set_pressure(dev, pressure):
    # set pressure using MKS 651 pressure controller
    # select setpoint D
    dev.write('D3')
    # set setpoint D to pressure mode
    dev.write('T31')
    # set setpoint D pressure in terms of % of total range
    dev.write('S3'+str(pressure/10))


def get_valve_pos(dev):
    # get valve position from MKS 600 pressure controller using device name
    valve_pos_str = dev.query('R6').rstrip()[1:]
    return np.round(float(valve_pos_str), decimals=1)


def get_pressure(dev):
    # get pressure reading from MKS 600 pressure controller using device name
    # read the pressure
    press_str = dev.query('R5').rstrip()[1:]
    return np.round(float(press_str)*10, decimals=5)

# %% ------ Funtions to control alicat mass flow controllers (MFCs) ---------


def mfc1_checked(vac_dict):
    # run when MFC box is checked/unchecked on GUI to initialize/close MFC
    if vac_dict['mfc1_on'].isChecked():
        try:
            # initialize MFC
            mfc1 = serial.Serial(vac_dict['mfc1_address'].text(),
                                 19200, timeout=1.0)
            vac_dict['mfc1_dev'] = mfc1
            vac_dict['output_box'].append('MFC-1 connected successfully.')
        except AttributeError:
            vac_dict['output_box'].append('MFC-1 could not connect.')
            vac_dict['mfc1_on'].setChecked(False)
    if not vac_dict['mfc1_on'].isChecked():
        try:
            vac_dict['mfc1_dev'].close()
            vac_dict['output_box'].append('MFC-1 disconnected.')
        except AttributeError:
            pass


def mfc2_checked(vac_dict):
    # run when MFC box is checked/unchecked on GUI to initialize/close MFC
    if vac_dict['mfc2_on'].isChecked():
        try:
            # initialize MFC
            mfc2 = serial.Serial(vac_dict['mfc2_address'].text(),
                                 19200, timeout=1.0)
            vac_dict['mfc2_dev'] = mfc2
            vac_dict['output_box'].append('MFC-2 connected successfully.')
        except AttributeError:
            vac_dict['output_box'].append('MFC-2 could not connect.')
            vac_dict['mfc2_on'].setChecked(False)
    if not vac_dict['mfc2_on'].isChecked():
        try:
            vac_dict['mfc2_dev'].close()
            vac_dict['output_box'].append('MFC-2 disconnected.')
        except AttributeError:
            pass


def get_flow_params(mfc, address='A'):
    # get mass flow controller parameters from MFC device and address name
    try:
        command = '{addr}\r'.format(addr=address)
        mfc.write(command.encode('ascii'))
        output = mfc.readline().decode('utf-8').split()
        if output == []:
            print('No output from MFC.')
            return 0, 0, 'None'
        else:
            flowrate = float(output[-3])
            setpoint = float(output[-2])
            gas = str(output[-1])
    except KeyError:
        flowrate, setpoint, gas = 0, 0, 'Air'
    return [flowrate, setpoint, gas]


def set_setpoint(mfc, setpoint, address='A'):
    # set the setpoint of MFC using the MFC device name and address
    command = '{addr}S{setpoint:.2f}\r'.format(addr=address, setpoint=setpoint)
    mfc.write(command.encode('ascii'))
    time.sleep(0.2)


def set_gas(mfc, gas, address='A'):
    # set the gas type of an MFC device and address
    gas = str(gas)
    gas_types = ['Air', 'Ar', 'CH4', 'CO', 'CO2', 'C2H6', 'H2', 'He', 'N2',
                 'N2O', 'Ne', 'O2', 'C3H8', 'n-C4H10', 'C2H2', 'C2H4',
                 'i-C2H10', 'Kr', 'Xe', 'SF6', 'C-25', 'C-10', 'C-8', 'C-2',
                 'C-75', 'A-75', 'A-25', 'A1025', 'Star29', 'P-5']
    if gas in gas_types:
        command = '{addr}$${gas}\r'.format(addr=address,
                                           gas=gas_types.index(gas))
        mfc.write(command.encode('ascii'))
    else:
        print('Invalid gas type. Try O2, N2, Air, CO2, etc.)')
    time.sleep(0.2)


# %% ------------- MAIN FUNCTION TO REPEAT EACH GUI ITERATION ---------------

def vac_main(vac_dict, df, df_i):
    # control pressure and flow rates in vacuum chamber. this fucntion
    # should run every loop iteration of the GUI in order to update
    # GUI displays andm aintain appropriate pressure settings.

    # measure the current pressure and flow rates
    if vac_dict['mks_on'].isChecked():
        # get pressure setpoint
        pressure_sp = vac_dict['set_pressure'].value()
        # get valve setpoint
        valve_sp = vac_dict['set_valve_pos'].value()
        # measure pressure and valve position
        pressure = get_pressure(vac_dict['mks_dev'])
        valve_pos = get_valve_pos(vac_dict['mks_dev'])
        vac_dict['current_pressure'] = pressure

        # set the pressure or valve position
        if vac_dict['pressure_mode'].isChecked():
            set_pressure(vac_dict['mks_dev'], pressure_sp)

        if vac_dict['valve_mode'].isChecked():
            set_valve_pos(vac_dict['mks_dev'], valve_sp)

        # update GUI with current values
        vac_dict['pressure_display'].setText(str(pressure))  # float(pressure))
        vac_dict['valve_pos_display'].setText(str(float(valve_pos)))

        df['pressure'].iloc[df_i] = str(pressure)
        df['pressure_setpoint'].iloc[df_i] = str(pressure_sp)

    # control turbo pump
    if vac_dict['turbo_on'].isChecked():
        if pressure < 0.5:
            if vac_dict['run_turbo'].isChecked():
                operate_turbo(vac_dict, run_pump=True)
            elif vac_dict['turbo_auto_on'].isChecked():
                operate_turbo(vac_dict, run_pump=True)
            else:
                operate_turbo(vac_dict, run_pump=False)
        else:
            operate_turbo(vac_dict, run_pump=False)

    # control MFCs
    if vac_dict['mfc1_on'].isChecked():
        # get MFC setpoint
        mfc1_sp = vac_dict['mfc1_sp'].value()
        # set the desired flow rate
        set_setpoint(vac_dict['mfc1_dev'],
                     float(mfc1_sp))
        # change gas
        # set_gas(mfc1, vac_dict['gas1'].currentText())
        # get MFC parameters
        flowrate1, setpoint1, gas1 = get_flow_params(vac_dict['mfc1_dev'])
        # update GUI
        vac_dict['mfc1_display'].setText(
                str(np.round(float(flowrate1), decimals=2)))
        # append values to main pressure file
        df['mfc1'].iloc[df_i] = str(flowrate1)

    if vac_dict['mfc2_on'].isChecked():
        # get MFC setpoint
        mfc2_sp = vac_dict['mfc2_sp'].value()
        # set the desired flow rate
        set_setpoint(vac_dict['mfc2_dev'],
                     float(mfc2_sp))
        # change gas
        # set_gas(mfc1, vac_dict['gas1'].currentText())
        # get MFC parameters
        flowrate2, setpoint2, gas2 = get_flow_params(vac_dict['mfc2_dev'])
        # update GUI
        vac_dict['mfc2_display'].setText(
                str(np.round(float(flowrate2), decimals=2)))
        # append values to main pressure file
        df['mfc2'].iloc[df_i] = str(flowrate2)

        '''
        print('flowrate = '+str(flowrate))
        print('setpoint = '+str(setpoint))
        print('gas = '+str(gas))
        '''

    # update vacuum sequence duration on GUI
    vac_df = vac_table_to_df(vac_dict)
    seq_time = vac_df['time'].sum()
    vac_dict['tot_vac_seq_time'].setText(
            str(np.round(int(seq_time)/60, decimals=2)))

    # display estimated sequence end time on the GUI
    if not vac_dict['vac_seq_running']:
        tot_seq_min = vac_df['time'].sum()
        seq_start_date = datetime.datetime.now()
        seq_end_date = seq_start_date + datetime.timedelta(minutes=tot_seq_min)
        vac_dict['vac_seq_end_time_display'].setText(
               seq_end_date.strftime('%m-%d %H:%M:%S'))


# %% ---------- THESE FUNCTIONS CONTROL GUI AND PRESSURE SEQUENCE -----------


def vac_table_to_df(vac_dict):
    # Convert vacuum sequence table on GUI to a Pandas dataframe
    # create empty dataframe
    vac_df = pd.DataFrame(
            columns=['time', 'pressure', 'mfc1', 'mfc2'],
            index=range(vac_dict['vac_table'].rowCount()))

    # loop over table entries
    for rowi in range(vac_dict['vac_table'].rowCount()):
        for colj in range(vac_dict['vac_table'].columnCount()):
            # populate dataframe with table entries
            new_entry = vac_dict['vac_table'].item(rowi, colj).text()
            vac_df.iloc[rowi, colj] = new_entry
    # delete empty rows
    vac_df = vac_df[vac_df['time'] != '0']
    return vac_df.astype(float)


def import_vac_seq(vac_dict, seq_name):
    # import RH sequence from file
    imported_seq = pd.read_csv(seq_name)
    # populate table on GUI
    for rowi in range(len(imported_seq)):
        for colj in range(len(imported_seq.columns)):
            vac_dict['vac_table'].setItem(
                    rowi, colj,
                    QtWidgets.QTableWidgetItem(
                            str(imported_seq.iloc[rowi, colj])))
    vac_dict['output_box'].append('Vacuum sequence file imported.')


def export_vac_seq(vac_dict, seq_name):
    # export RH sequence to file
    vac_df = vac_table_to_df(vac_dict)
    vac_df.to_csv(str(seq_name), index=False)
    vac_dict['output_box'].append('Vacuum sequence file exported.')


def clear_vac_seq(vac_dict):
    # clear pressure sequence by populating the sequence table with 0's
    for rowi in range(vac_dict['vac_table'].rowCount()):
        for colj in range(vac_dict['vac_table'].columnCount()):
            vac_dict['vac_table'].setItem(
                    rowi, colj,
                    QtWidgets.QTableWidgetItem('0'))
    vac_dict['output_box'].append('Vacuum sequence cleared.')


def plot_vac_seq(vac_dict):
    # plot the RH sequence

    try:
        vac_df = vac_table_to_df(vac_dict)
        seq_time = np.array(vac_df['time'].astype(float))
        plot_seq_time = np.insert(np.cumsum(seq_time), 0, 0)/60
        press_arr = np.array(vac_df['pressure'].astype(float))
        mfc1_arr = np.array(vac_df['mfc1'].astype(float))
        mfc2_arr = np.array(vac_df['mfc2'].astype(float))
        plot_press = np.insert(press_arr, 0, press_arr[0])
        plot_mfc1 = np.insert(mfc1_arr, 0, mfc1_arr[0])
        plot_mfc2 = np.insert(mfc2_arr, 0, mfc2_arr[0])
        fig_seq = plt.figure(1)
        plt.cla()
        plt.ion()
        plt.fill_between(plot_seq_time, plot_press,
                         step='pre', alpha=0.6)

        plt.plot(plot_seq_time, plot_press,
                 label='Pressure (Torr)', c='b', drawstyle='steps')

        plt.plot(plot_seq_time, plot_mfc1, c='k',
                 label='MFC-1 flow (sccm)', drawstyle='steps')

        plt.plot(plot_seq_time, plot_mfc2, c='r',
                 label='MFC-2 flow (sccm)', drawstyle='steps')

        plt.legend(fontsize=10)
        plt.xlabel('Time (hours)', fontsize=12)
        plt.ylabel('Pressure (Torr)', fontsize=12)
        plt.tight_layout()
        fig_seq.canvas.set_window_title('Vacuum sequence')
        fig_seq.show()
    except NameError:
        vac_dict['output_box'].append('Vacuum sequence not valid.')


def plot_pressure(df, df_i):
    # Plot the RH over time
    vac_df = df[df['pressure'] != '']
    setpoint = vac_df['pressure_setpoint'].astype(float)
    pressure = vac_df['pressure'].astype(float)
    pressure_time = vac_df['time'].astype(float)
    fig_seq = plt.figure(20)
    plt.cla()
    plt.ion()
    plt.plot(pressure_time/60, pressure, c='b', label='measured')
    plt.plot(pressure_time/60, setpoint, c='r', label='setpoint')
    plt.xlabel('Time (hours)', fontsize=12)
    plt.ylabel('Pressure (Torr)', fontsize=12)
    plt.legend(fontsize=12)
    plt.tight_layout()
    fig_seq.canvas.set_window_title('Pressure over time')
    fig_seq.show()


def run_vac_seq(vac_dict):
    # run RH sequence
    vac_dict['output_box'].append('Vacuum sequence initiated.')
    vac_dict['vac_seq_running'] = True
    vac_dict['run_vac_seq'].setEnabled(False)
    vac_dict['save_data_now'].setChecked(True)
    vac_dict['set_pressure'].setEnabled(False)
    vac_dict['set_valve_pos'].setEnabled(False)
    vac_dict['pressure_mode'].setEnabled(False)
    vac_dict['valve_mode'].setEnabled(False)
    vac_dict['mfc1_sp'].setEnabled(False)
    vac_dict['mfc2_sp'].setEnabled(False)
    vac_dict['vac_table'].setEnabled(False)
    vac_dict['pressure_mode'].setChecked(True)
    vac_dict['valve_mode'].setChecked(False)
    vac_df = vac_table_to_df(vac_dict)
    tot_seq_time = vac_df['time'].sum()
    tot_time_disp = str(np.round(tot_seq_time, decimals=1))
    # set up timers and counters
    elapsed_seq_time = 0
    seq_start_time = time.time()

    tot_seq_min = vac_df['time'].sum()
    seq_start_date = datetime.datetime.now()
    seq_end_date = seq_start_date + datetime.timedelta(
                                               minutes=tot_seq_min)
    vac_dict['vac_seq_end_time_display'].setText(
           seq_end_date.strftime('%m-%d %H:%M:%S'))

    step_num = 0
    # loop over each step in sequence
    for step in range(len(vac_df)):

        if vac_dict['vac_seq_running']:
            step_start_time = time.time()
            elapsed_step_time = 0
            step_dur = vac_df['time'].iloc[step]*60
        else:
            break
        # repeat until step duration has elapsed
        while elapsed_step_time < step_dur:

            if vac_dict['vac_seq_running']:
                elapsed_step_time = time.time() - step_start_time
                elapsed_seq_time = time.time() - seq_start_time

                # update fields on GUI
                if step_num % 5 == 0:
                    vac_dict['save_data_now'].setChecked(True)
                    vac_dict['vac_seq_step'].setText(
                            str(int(step+1))+'/'+str(len(vac_df)))

                    vac_dict['set_pressure'].setValue(
                            float(vac_df['pressure'].iloc[step]))

                    vac_dict['mfc1_sp'].setValue(
                            float(vac_df['mfc1'].iloc[step]))

                    vac_dict['mfc2_sp'].setValue(
                            float(vac_df['mfc2'].iloc[step]))

                    elasped_time_disp = str(
                            np.round(elapsed_seq_time/60, decimals=2))

                    vac_dict['elapsed_vac_seq_time'].setText(
                            elasped_time_disp + '/' + tot_time_disp)

                time.sleep(.5)
                step_num += 1
            else:
                break

    # reset pressure back to zero
    vac_dict['mfc1_sp'].setValue(float(0))
    vac_dict['mfc2_sp'].setValue(float(0))
    vac_dict['set_pressure'].setValue(0.0)
    vac_dict['set_valve_pos'].setValue(100.0)

    # reset other sequence options
    vac_dict['vac_seq_step'].setText('0')
    vac_dict['elapsed_vac_seq_time'].setText('0')
    vac_dict['output_box'].append('Vacuum sequence completed.')
    vac_dict['vac_seq_running'] = False
    vac_dict['run_vac_seq'].setEnabled(True)
    vac_dict['set_pressure'].setEnabled(True)
    vac_dict['vac_table'].setEnabled(True)
    vac_dict['save_data_now'].setChecked(False)
    vac_dict['set_valve_pos'].setEnabled(True)
    vac_dict['pressure_mode'].setEnabled(True)
    vac_dict['valve_mode'].setEnabled(True)
    vac_dict['mfc1_sp'].setEnabled(True)
    vac_dict['mfc2_sp'].setEnabled(True)


# %% ------------------- Test pressure transducer -------------------------


if __name__ == '__main__':

    mks_on = True
    if mks_on:
        rm = visa.ResourceManager()
        # list all resources connected to PC
        # print(rm.list_resources('?*'))  # all devices including GPIB
        # print(rm.list_resources())

        # create instance of MKS instrument
        mks = rm.open_resource('COM12')

        # set the valve to 0-5 volt mode
        # mks.write('B0')

        valve_mode = False
        pressure_mode = False

        if pressure_mode is True:
            set_pressure(mks, 00)

        if valve_mode is True:
            set_valve_pos(mks, 00)

        print('pressure:')
        print(get_pressure(mks))
        print('valve position:')
        print(get_valve_pos(mks))

        mks.close()

    mfcs_on = False
    if mfcs_on:
        # initialize MFC for gas
        mfcg = serial.Serial('COM17', 19200, timeout=1.0)
        # initialize MFC for vapor
        mfcv = serial.Serial('COM16', 19200, timeout=1.0)

        set_gas(mfcg, 'N2')
        set_setpoint(mfcg, 0)
        flowrate, setpoint, gas = get_flow_params(mfcg)
        print('flowrate = '+str(flowrate))
        print('setpoint = '+str(setpoint))
        print('gas = '+str(gas))

        set_gas(mfcv, 'Air')
        set_setpoint(mfcv, 0)
        flowrate, setpoint, gas = get_flow_params(mfcv)
        print('flowrate = '+str(flowrate))
        print('setpoint = '+str(setpoint))
        print('gas = '+str(gas))

        mfcg.close()
        mfcv.close()

    else:
        pass
