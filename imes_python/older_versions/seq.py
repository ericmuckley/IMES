# -*- coding: utf-8 -*-
"""
This module allows communication between Python PyQt GUI and control
of environmental conditions, as well as sequences of conditions.

Packages required:
time
matplotlib
numpy
pandas
PyQt5

Created on Thur Jan 31 17:20:40 2019
@author: ericmuckley@gmail.com
"""

from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
fontsize = 12


def rh_table_to_df(seq_dict):
    # Convert RH sequence table on GUI to a Pandas dataframe
    # create empty dataframe
    rh_df = pd.DataFrame(
            columns=['time', 'rh'],
            index=range(seq_dict['rh_table'].rowCount()))

    # loop over table entries
    for rowi in range(seq_dict['rh_table'].rowCount()):
        for colj in range(seq_dict['rh_table'].columnCount()):
            # populate dataframe with table entries
            new_entry = seq_dict['rh_table'].item(rowi, colj).text()
            rh_df.iloc[rowi, colj] = new_entry
    # delete empty rows
    rh_df = rh_df[rh_df['time'] != '0']
    return rh_df


def plot_rh_seq(seq_dict):
    # plot the RH sequence
    rh_df = rh_table_to_df(seq_dict)
    try:
        rh_df = rh_table_to_df(seq_dict)
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
        seq_dict['output_box'].append('RH sequence not valid.')


def import_rh_seq(seq_dict, seq_name):
    # import RH sequence from file
    imported_seq = pd.read_csv(seq_name)
    # populate table on GUI
    for rowi in range(len(imported_seq)):
        for colj in range(len(imported_seq.columns)):
            seq_dict['rh_table'].setItem(
                    rowi, colj,
                    QtWidgets.QTableWidgetItem(
                            str(imported_seq.iloc[rowi, colj])))
    seq_dict['output_box'].append('RH sequence file imported.')


def export_rh_seq(seq_dict, seq_name):
    # export RH sequence to file
    rh_df = rh_table_to_df(seq_dict)
    rh_df.to_csv(str(seq_name), index=False)
    seq_dict['output_box'].append('RH sequence file exported.')


def clear_rh_seq(seq_dict):
        # clear pressure sequence by populating the sequence table with 0's
        for rowi in range(seq_dict['rh_table'].rowCount()):
            for colj in range(seq_dict['rh_table'].columnCount()):
                seq_dict['rh_table'].setItem(
                        rowi, colj,
                        QtWidgets.QTableWidgetItem('0'))
        seq_dict['output_box'].append('RH sequence cleared.')


def plot_rh(df, df_i):
    # Plot the RH over time
    rh_df = df[df['rh'] != '']
    rh = rh_df['rh'].astype(float)
    rh_time = rh_df['time'].astype(float)
    fig_seq = plt.figure(20)
    plt.cla()
    plt.ion()
    plt.plot(rh_time/60, rh, c='b')
    plt.xlabel('Time (hours)', fontsize=12)
    plt.ylabel('RH (%)', fontsize=12)
    plt.tight_layout()
    fig_seq.canvas.set_window_title('RH over time')
    fig_seq.show()


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
