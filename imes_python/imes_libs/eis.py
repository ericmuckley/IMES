# -*- coding: utf-8 -*-
"""
This module controls the Solartron 1260 impedance analyzer using
GPIB interface.

Created on Fri Mar 15 13:28:19 2019
@author: ericmuckley@gmail.com
"""

import visa
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
fontsize = 12


def eis_checked(eis_dict):
    # run this function when solartron1260 checkbox is clicked

    # open connection to instrument
    if eis_dict['eis_on'].isChecked():
        try:
            rm = visa.ResourceManager()
            # print(rm.list_resources())
            # solartron = rm.open_resource('GPIB1::4::INSTR')
            eis_add = eis_dict['solartron_address'].text()
            eis_dev = rm.open_resource(eis_add)
            eis_dict['eis_dev'] = eis_dev
            eis_dev.timeout = 60000
            time.sleep(0.2)
            eis_dev.write('*RST')
            time.sleep(0.2)
            eis_dict['output_box'].append('Solartron 1260 connected.')
        except visa.VISAIOERROR:
            eis_dict['output_box'].append('Solartron 1260 could not connect.')
            eis_dict['eis_on'].setChecked(False)

    # close connection to instument
    if not eis_dict['eis_on'].isChecked():
        try:
            eis_dict['eis_dev'].close()
            eis_dict['output_box'].append('Solartron 1260 disconnected.')
        except visa.VISAIOERROR:
            eis_dict['output_box'].append('Solartron 1260 could not close.')
        eis_dict['eis_on'].setChecked(False)


def get_eis_freqs(eis_dict):
    # get impedance spectrum frequencies from selections on GUI
    # get start and end frequencies from GUI
    start_f = float(str(eis_dict['start_freq'].currentText()).replace(',', ''))
    end_f = float(str(eis_dict['end_freq'].currentText()).replace(',', ''))
    # convert frequencies into exponents with base 10
    start_f_exp = int(np.log10(start_f))
    end_f_exp = int(np.log10(end_f))
    # construct frequency array
    freq_array = np.logspace(start_f_exp, end_f_exp,
                             eis_dict['eis_points'].value())
    return freq_array


def preview_eis_freqs(eis_dict):
    # display impedance frequencies to user
    freq_array = get_eis_freqs(eis_dict)
    eis_dict['output_box'].append(
            'Impedance frequencies to measure in Hz:')
    eis_dict['output_box'].append(str(freq_array))
    ac_bias = float(eis_dict['ac_bias'].value())
    dc_offset = float(eis_dict['dc_offset'].value())
    ac_bias_repeat = np.repeat(ac_bias, len(freq_array))
    dc_bias_repeat = np.repeat(dc_offset, len(freq_array))
    plt.ion
    fig_eis_freqs = plt.figure(40)
    fig_eis_freqs.clf()
    plt.semilogx(freq_array, dc_bias_repeat,
                 c='g', marker='o', markersize=5, label='DC offset')
    plt.semilogx(freq_array, ac_bias_repeat,
                 c='r', marker='o', markersize=5, label='AC bias')
    plt.xlabel('Frequency (Hz)', fontsize=fontsize)
    plt.ylabel('Bias (V)', fontsize=fontsize)
    fig_eis_freqs.canvas.set_window_title('Frequencies for EIS measurements')
    plt.legend()
    plt.tight_layout()
    plt.draw()


def measure_eis(eis_dict, df, df_i):
    # measure impedance spectrum
    eis_dict['eis_busy'] = True
    begin_eis_time = time.time()
    spec_time = time.strftime('%Y-%m-%d_%H-%M-%S_')

    # open connection to instrument
    # rm = visa.ResourceManager()
    # print(rm.list_resources())
    # solartron = rm.open_resource('GPIB1::4::INSTR')
    # solartron.timeout = 10000
    # time.sleep(0.2)
    # solartron.write('*RST')
    # time.sleep(0.2)

    solartron = eis_dict['eis_dev']
    eis_dict['output_box'].append('Measuring impedance spectrum...')

    # get frequencies at which to measure
    freq_array = get_eis_freqs(eis_dict)

    # set AC voltage amplitude
    ac_bias = float(eis_dict['ac_bias'].value())
    solartron.write('VA '+str(ac_bias))

    # set DC bias offset
    dc_offset = float(eis_dict['dc_offset'].value())
    solartron.write('VB '+str(dc_offset))

    results = np.zeros((len(freq_array), 5))
    # loop over each frequency in frequency range
    for i, f0 in enumerate(freq_array):

        # take slower measurements at low frequencies
        pause = 0.2
        if f0 < 100:
            pause = 2 * (1 / f0)
        # set frequency
        solartron.write('FR '+str(f0))
        time.sleep(pause)

        z = []
        phase_deg = []
        f0_exp = []
        for sweep in range(eis_dict['averaging'].value()):
            # measure impedance
            result0 = solartron.query('SI').split(',')
            f0_exp.append(float(result0[0]))
            z.append(float(result0[1]))
            phase_deg.append(float(result0[2]))
            time.sleep(pause/2)
        f0_exp = np.mean(f0_exp)
        z = np.mean(z)
        phase_deg = np.mean(phase_deg)
        # calculate real and imaginary impedance
        phase_rad = np.pi * phase_deg / 180
        rez = z * np.cos(phase_rad)
        imz = z * np.sin(phase_rad)

        results[i, :] = [f0_exp, z, phase_deg, rez, imz]
        print(results[:i, :2])
        eis_dict['new_data'] = results[:i, :2]

        # display results on GUI
        eis_dict['actual_freq'].setText(str(np.round(f0, decimals=2)))
        eis_dict['actual_z'].setText(str(np.round(z, decimals=2)))
        eis_dict['actual_phase'].setText(str(np.around(phase_deg, decimals=2)))

        tot_eis_time = (time.time() - begin_eis_time)/60
        eis_dict['eis_time'].setText(str(np.round(tot_eis_time, decimals=2)))
    # solartron.close()

    eis_dict['output_box'].append('Impedance measurement complete.')

    # display results on GUI
    eis_dict['actual_freq'].setText('--')
    eis_dict['actual_z'].setText('--')
    eis_dict['actual_phase'].setText('--')

    # save results to file
    # make empty columns to fill with data
    eis_dict['eis_df']['freq_'+spec_time] = np.repeat('', 500)
    eis_dict['eis_df']['z_'+spec_time] = np.repeat('', 500)
    eis_dict['eis_df']['phase_'+spec_time] = np.repeat('', 500)
    eis_dict['eis_df']['rez_'+spec_time] = np.repeat('', 500)
    eis_dict['eis_df']['imz_'+spec_time] = np.repeat('', 500)

    # now fill empty cells with new data
    eis_dict['eis_df'][
            'freq_'+spec_time].iloc[
                    :len(freq_array)] = results[:, 0].astype(str)

    eis_dict['eis_df'][
            'z_'+spec_time].iloc[
                    :len(freq_array)] = results[:, 1].astype(str)

    eis_dict['eis_df'][
            'phase_'+spec_time].iloc[
                    :len(freq_array)] = results[:, 2].astype(str)

    eis_dict['eis_df'][
            'rez_'+spec_time].iloc[
                    :len(freq_array)] = results[:, 3].astype(str)

    eis_dict['eis_df'][
            'imz_'+spec_time].iloc[
                    :len(freq_array)] = results[:, 4].astype(str)

    # save data to file
    eis_dict['eis_df'].to_csv(
            eis_dict['save_file_dir']+'/'+eis_dict[
                                        'start_date']+'_eis.csv', index=False)
    # save max current to main df
    low_freq_z = results[0, 1]
    df['low_freq_z'].iloc[df_i] = str(low_freq_z)
    eis_dict['eis_busy'] = False


def eis_rh_seq(eis_dict, df, df_i):
    # run impedance measurement continuously during RH sequence
    eis_dict['eis_busy'] = True
    if eis_dict['eis_rh_seq'].isChecked():
        measure_eis(eis_dict, df, df_i)
        time.sleep(2)
    time.sleep(float(eis_dict['pause_after_eis'].value())*60)
    eis_dict['eis_busy'] = False


def eis_vac_seq(eis_dict, df, df_i):
    # run impedance measurement continuously during RH sequence
    eis_dict['eis_busy'] = True
    if eis_dict['eis_vac_seq'].isChecked():
        measure_eis(eis_dict, df, df_i)
        time.sleep(2)
    time.sleep(float(eis_dict['pause_after_eis'].value())*60)
    eis_dict['eis_busy'] = False


def plot_phase(eis_dict):
    # plot phase over time
    file = eis_dict['save_file_dir']+'/'+eis_dict[
            'start_date']+'_eis.csv'
    data = pd.read_csv(file)
    plt.ion
    fig_eis_p = plt.figure(41)
    fig_eis_p.clf()
    # loop over each measurement
    for i in range(0, len(data.columns)-1, 5):
        colors = cm.jet(np.linspace(0, 1, len(data.columns)-4))
        plt.semilogx(data.iloc[:, i].astype(float),
                     data.iloc[:, i+2].astype(float),
                     c=colors[int(i/5)], label=str(int(i/5)))
    plt.xlabel('Frequency (Hz)', fontsize=fontsize)
    plt.ylabel('Phase (deg)', fontsize=fontsize)
    plt.legend()
    fig_eis_p.canvas.set_window_title(
            'Displaying '+str(int(len(data.columns)/5))+' phase plots')
    plt.tight_layout()
    plt.draw()


def plot_z(eis_dict):
    # plot impedance ovwer time
    file = eis_dict['save_file_dir']+'/'+eis_dict[
            'start_date']+'_eis.csv'
    data = pd.read_csv(file)
    plt.ion
    fig_eis_z = plt.figure(42)
    fig_eis_z.clf()
    # loop over each measurement
    for i in range(0, len(data.columns)-1, 5):
        colors = cm.jet(np.linspace(0, 1, len(data.columns)-4))
        plt.loglog(data.iloc[:, i].astype(float),
                   data.iloc[:, i+1].astype(float),
                   c=colors[int(i/5)], label=str(int(i/5)))
    plt.xlabel('Frequency (Hz)', fontsize=fontsize)
    plt.ylabel('Z (Ohm)', fontsize=fontsize)
    plt.legend()
    fig_eis_z.canvas.set_window_title(
            'Displaying '+str(int(len(data.columns)/5))+' impedance plots')
    plt.tight_layout()
    plt.draw()


def plot_nyquist(eis_dict):
    # plot Nyquist impedance over time
    file = eis_dict['save_file_dir']+'/'+eis_dict[
            'start_date']+'_eis.csv'
    data = pd.read_csv(file)
    plt.ion
    fig_eis_z = plt.figure(43)
    fig_eis_z.clf()
    # loop over each measurement
    for i in range(0, len(data.columns)-1, 5):
        colors = cm.jet(np.linspace(0, 1, len(data.columns)-4))
        plt.plot(data.iloc[:, i+3].astype(float),
                 data.iloc[:, i+4].astype(float),
                 c=colors[int(i/5)], label=str(int(i/5)))
    plt.xlabel('Re(Z) (Ohm)', fontsize=fontsize)
    plt.ylabel('Im(Z) (Ohm)', fontsize=fontsize)
    plt.legend()
    fig_eis_z.canvas.set_window_title(
            'Displaying '+str(int(len(data.columns)/5))+' Nyquist plots')
    plt.tight_layout()
    plt.draw()


def plot_low_freq_z(eis_dict, df, df_i):
    # plotlowest-frequency impedance over time
    plt.ion
    fig_current = plt.figure(45)
    fig_current.clf()
    df_small = df[df['low_freq_z'] != '']
    plt.plot(pd.to_numeric(df_small['time']),
             pd.to_numeric(df_small['low_freq_z']),
             c='r', lw=1)
    plt.xlabel('Elapsed time (min)', fontsize=fontsize)
    plt.ylabel('Low-frequency Impedance (Ohm)', fontsize=fontsize)
    fig_current.canvas.set_window_title('Low-frequency Impedance')
    plt.tight_layout()
    plt.draw()


# use this script to test/debug impedance analyzer
if __name__ == '__main__':

    # open connectino to instrument
    rm = visa.ResourceManager()
    # print(rm.list_resources())
    solartron = rm.open_resource('GPIB1::4::INSTR')
    time.sleep(0.2)
    solartron.write('*RST')
    time.sleep(0.2)

    # set AC voltage amplitude
    solartron.write('VA 1')
    time.sleep(0.2)
    # set DC bias offset (-40 V to +40 V)
    solartron.write('VB 0')
    time.sleep(0.2)

    # set frequency
    start_f = 10
    end_f = 1000000
    start_f_exp = int(np.log10(start_f))
    end_f_exp = int(np.log10(end_f))
    # construct frequency array
    freqs = np.logspace(start_f_exp, end_f_exp, 5)
    results = np.zeros((len(freqs), 3))
    for f_i, f in enumerate(freqs):
        time.sleep(0.2)
        solartron.write('FR '+str(f))
        time.sleep(0.2)
        # print(solartron.query('SI'))
        solartron.write('SI')
        time.sleep(0.2)

        read_string = solartron.read().split(',')
        results[f_i] = [float(r0) for r0 in read_string[:3]]

        print(read_string)

    solartron.close()
    print(results)
    plt.plot(results[:, 0], results[:, 1])
    plt.show()

'''
    # for manual sweeping of frequencies
    frequencies = np.logspace(0, 6, base=10, num=10)
    averaging = 1

    # empty dataframe for data
    z_list = []
    phase_list = []

    for f in frequencies:

        # take slower measurements at low frequencies
        pause = 0.6 if f < 10 else 0.3

        # set frequency
        solartron.write('FR '+str(f))
        time.sleep(0.2)
        print(solartron.read_stb())
        time.sleep(pause)
        print('frequency = '+str(f))
        z = []
        phase_deg = []
        for sweep in range(averaging):
            time.sleep(0.2)
            # measure impedance
            result0 = solartron.query('SI')
            print(result0)
            result0 = result0.split(',')
            z.append(float(result0[1]))
            phase_deg.append(float(result0[2]))
            time.sleep(pause)
        z = np.median(z)
        phase_deg = np.median(phase_deg)

        z_list.append(z)
        phase_list.append(phase_deg)

    plt.semilogx(frequencies, z_list)
    plt.title('Z')
    plt.show()

    plt.semilogx(frequencies, phase_list)
    plt.title('Phase')
    plt.show()
    solartron.close()    
'''

