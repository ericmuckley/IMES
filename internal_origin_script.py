# -*- coding: utf-8 -*-
"""
This is the internal Origin python script which runs inside Origin when
Origin is called externally from python.

Created on Thu Mar  7 15:01:32 2019
@author: ericmuckley@gmail.com
"""

import PyOrigin
import os
import sys
import csv
import glob
# add path to non-standard python libraries so they can be imported
# lib_path = 'C:\\ProgramData\\Anaconda3\\Lib\\site-packages'
# sys.path.append(lib_path)

# these imports will only work if pandas is installed in Origin first!
import numpy as np
import pandas as pd


def import_csv(filename):
    # imports a csv file and returns headers and data as floats
    data = []
    with open(filename) as f:
        reader = csv.reader(f)
        [data.append(row) for row in reader]
    # extact headers
    headers = data[0]
    # remove headers from data
    data = data[1:]
    # convert strings to floats
    for i in range(len(data)):
        for j in range(len(data[i])):
            if data[i][j] == '':
                data[i][j] = '0'
            data[i][j] = float(data[i][j])
    # remove completely empty rows from data
    data = [row for row in data if not all(i == 0 for i in row)]
    # transpose data
    data = list(map(list, zip(*data)))
    return headers, data


def get_file_dict(exp_start_time, data_folder):
    # get a dictionary of each data file and what type of data it holds based
    # on the experiment start time and folder of data files.
    # get list of all data files in data folder
    all_data_files = glob.glob(data_folder + '\*')
    # list of data descriptors (strings) which should show up in file names
    data_file_descriptors = ['main_df', 'qcm_params', 'iv', 'cv', 'eis',
                             'bs', 'optical']
    # create empty dictionary to hold selected data files
    file_dict = {}
    # loop through all data files in the data folder
    for f in all_data_files:
        # split full file path into file directory and name
        filedir, filename = os.path.split(f)
        # get date of file creation from beginning of filename
        filedate = filename.split('__')[0]
        # select files which creation date matches that of exp_start_time
        if filedate == exp_start_time:
            # assign each datafile to each file descriptor
            for descriptor in data_file_descriptors:
                if descriptor in filename:
                    file_dict[descriptor] = f
    return file_dict


def norm_qcm_params(data):
    # get arrays of normalized QCM parameters from delta F and delta D data.
    # input should be values of the raw data from qcm_params.csv:
    # i.e. pd.read_csv('qcm_params.csv).values
    # the normalized data is raw data minus original baseline divided by n.

    # separate deltaF from deltaD columns
    df_raw = data[:, 0:10]
    dd_raw = data[:, [0, 10, 11, 12, 13, 14, 15, 16, 17, 18]]

    # create copy arrays for normalized data
    df_norm = np.copy(df_raw)
    dd_norm = np.copy(dd_raw)

    # loop over each column of raw data
    for col in range(1, len(df_raw[0])):
        # get harmonic number
        n = (col - 1) * 2 + 1
        # find indicies which have data in them
        data_indices = np.invert(np.isnan(df_raw[:, col]))
        # check if there is any data in the column
        if len(data_indices) > 0:
            # index to normalize column on (the 1st measurement in the column)
            norm_index = np.argmax(data_indices)

            # get delta f/n and delta D/n
            df_norm[data_indices, col] = (
                    df_raw[data_indices, col] - df_raw[norm_index, col])/n/1e3
            dd_norm[data_indices, col] = (
                    dd_raw[data_indices, col] - dd_raw[norm_index, col]) / 1e-6
    return df_norm, dd_norm


def get_sheet(file, data):
    # get Origin worksheet and fill it with data
    # create workbook named 'file' using template named 'Origin'
    PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS, file, 'Origin', 1)
    sheet = PyOrigin.ActiveLayer()  # get sheet
    sheet.SetData(data.T, -1)  # put imported data into worksheet
    sheet.SetName(file)  # set sheet name
    return sheet


def get_plot(file, template='custom_line'):
    # create empty origin plot to fill with data using specified template
    pgName = PyOrigin.CreatePage(
            PyOrigin.PGTYPE_GRAPH,
            'plot_'+file, template, 1)
    gp = PyOrigin.Pages(str(pgName))
    gp.LT_execute('layer1.x.opposite = 1;layer1.y.opposite = 1;')
    gp.LT_execute('layer1 -g')
    gl = gp.Layers(0)
    # Create data range and plot it into the graph layer.
    rng = PyOrigin.NewDataRange()  # Create data range.
    return gl, rng


# get path of data folder
exp_start_time = sys.argv[1]
exp_start_time = exp_start_time[:-1]  # remove trailing underscore
data_folder = sys.argv[2]
# get list of relevant data files
file_dict = get_file_dict(exp_start_time, data_folder)


# save origin file and quit
save_origin_filename = os.path.join(
        data_folder,
        exp_start_time+'_origin_report.opj')


# loop over every relevant data file and open new worksheet for each one
for file in file_dict:

    # if there is data, import data files
    if file_dict:
        data = pd.read_csv(file_dict[file]).values
        headers = list(pd.read_csv(file_dict[file]))

        if file == 'main_df':

            # re-read data as dataframe, not values
            data = pd.read_csv(file_dict[file])
            # cut off last values
            data = data.iloc[:-10]
            # create elapsed time column
            elapsed_time = (np.array(data['time']) - data['time'].iloc[0])/60
            # insert elapsed time column into dataframe
            data.insert(loc=2, column='Time', value=elapsed_time)
            # create worksheet and plot
            sheet = get_sheet(file, data.values)

            # loop over columns and label them
            for col in range(len(data)):

                if list(data)[col] == 'date':
                    sheet.Columns(col).SetLongName('Date/time')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_X)

                if list(data)[col] == 'time':
                    sheet.Columns(col).SetLongName('Time')
                    sheet.Columns(col).SetUnits('min')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_X)

                if list(data)[col] == 'Time':
                    sheet.Columns(col).SetLongName('Time')
                    sheet.Columns(col).SetUnits('hours')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_X)

                if list(data)[col] == 'pressure':
                    sheet.Columns(col).SetLongName('pressure_measured')
                    sheet.Columns(col).SetUnits('Torr')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'pressure_setpoint':
                    sheet.Columns(col).SetLongName('Pressure')
                    sheet.Columns(col).SetUnits('Torr')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'mfc1':
                    sheet.Columns(col).SetLongName('Flow-1')
                    sheet.Columns(col).SetUnits('SCCM')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'mfc2':
                    sheet.Columns(col).SetLongName('Flow-2')
                    sheet.Columns(col).SetUnits('SCCM')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'rh':
                    sheet.Columns(col).SetLongName('rh_measured')
                    sheet.Columns(col).SetUnits('%')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'rh_setpoint':
                    sheet.Columns(col).SetLongName('RH')
                    sheet.Columns(col).SetUnits('%')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'temp':
                    sheet.Columns(col).SetLongName('Temperature')
                    sheet.Columns(col).SetUnits('C')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'bias':
                    sheet.Columns(col).SetLongName('Bias')
                    sheet.Columns(col).SetUnits('V')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'current':
                    sheet.Columns(col).SetLongName('Current')
                    sheet.Columns(col).SetUnits('A')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'max_iv_current':
                    sheet.Columns(col).SetLongName('Max. I-V current')
                    sheet.Columns(col).SetUnits('A')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'max_cv_current':
                    sheet.Columns(col).SetLongName('Max. C-V current')
                    sheet.Columns(col).SetUnits('A')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'cv_area':
                    sheet.Columns(col).SetLongName('C-V area')
                    sheet.Columns(col).SetUnits('V x A')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'low_freq_z':
                    sheet.Columns(col).SetLongName('Low freq. Z')
                    sheet.Columns(col).SetUnits('Ohm')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)

                if list(data)[col] == 'note':
                    sheet.Columns(col).SetLongName('Note')
                    sheet.Columns(col).SetType(PyOrigin.COLTYPE_DESIGN_Y)
            try:
                # plot RH during experiment
                gl, rng = get_plot(file+'_rh')
                rng.Add('X', sheet, 0, data.columns.get_loc('Time'),
                        -1, data.columns.get_loc('Time'))
                rng.Add('Y', sheet, 0, data.columns.get_loc('RH'),
                        -1, data.columns.get_loc('RH'))
                dp = gl.AddPlot(rng, 200)

                # plot pressure during experiment
                gl, rng = get_plot(file+'_rh')
                rng.Add('X', sheet, 0, data.columns.get_loc('Time'),
                        -1, data.columns.get_loc('Time'))
                rng.Add('Y', sheet, 0, data.columns.get_loc('Pressure'),
                        -1, data.columns.get_loc('Pressure'))
                dp = gl.AddPlot(rng, 200)
            except:
                pass

        if file == 'iv':
            # change units
            for i in range(0, len(data[0]), 2):
                data[:, i+1] = data[:, i+1] * 1e9
            # create worksheet and plot
            sheet = get_sheet(file, data)
            gl, rng = get_plot(file)
            for i in range(0, len(data[0]), 2):
                sheet.Columns(i).SetLongName('Bias')
                sheet.Columns(i).SetUnits('V')
                sheet.Columns(i).SetComments(str(1+int(i/2)))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
                sheet.Columns(i+1).SetLongName('Current')
                sheet.Columns(i+1).SetUnits('nA')
                sheet.Columns(i+1).SetComments(str(1+int(i/2)))
                sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's i col as X
                rng.Add('X', sheet, 0, i, -1, i)
                # graph worksheet's i+1 col as Y
                rng.Add('Y', sheet, 0, i+1, -1, i+1)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

        elif file == 'cv':
            # change units and cut off redundant cycles
            # cycle_length = int((len(data) - 1)/4)
            # data = data[cycle_length-1:-cycle_length]
            # for i in range(0, len(data[0]), 2):
            #    data[:, i+1] = data[:, i+1] * 1e9
            # create worksheet and plot
            sheet = get_sheet(file, data)
            gl, rng = get_plot(file)

            for i in range(0, len(data[0]), 2):

                if 'bias' in headers[i]:
                    pass
                sheet.Columns(i).SetLongName('Bias')
                sheet.Columns(i).SetUnits('V')
                sheet.Columns(i).SetComments(str(1+int(i/2)))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
                sheet.Columns(i+1).SetLongName('Current')
                sheet.Columns(i+1).SetUnits('A')
                sheet.Columns(i+1).SetComments(str(1+int(i/2)))
                sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's i col as X
                rng.Add('X', sheet, 0, i, -1, i)
                # graph worksheet's i+1 col as Y
                rng.Add('Y', sheet, 0, i+1, -1, i+1)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

        elif file == 'bs':
            # change units
            for i in range(0, len(data[0]), 3):
                data[:, i+2] = data[:, i+2] * 1e9
            # create worksheet and plot
            sheet = get_sheet(file, data)
            gl, rng = get_plot(file)
            for i in range(0, len(data[0]), 3):
                sheet.Columns(i).SetLongName('Time')
                sheet.Columns(i).SetUnits('min')
                sheet.Columns(i).SetComments(str(1+int(i/3)))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
                sheet.Columns(i+1).SetLongName('Bias')
                sheet.Columns(i+1).SetUnits('V')
                sheet.Columns(i+1).SetComments(str(1+int(i/3)))
                sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                sheet.Columns(i+2).SetUnits('nA')
                sheet.Columns(i+2).SetLongName('Current')
                sheet.Columns(i+2).SetComments(str(1+int(i/3)))
                sheet.Columns(i+2).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's i col as X
                rng.Add('X', sheet, 0, i, -10, i)
                # graph worksheet's i+2 col as Y
                rng.Add('Y', sheet, 0, i+2, -10, i+2)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

        elif file == 'optical':
            # create worksheet and plot
            sheet = get_sheet(file, data)
            gl, rng = get_plot(file)
            for i in range(0, len(data[0]), 2):
                sheet.Columns(i).SetLongName('Wavelength')
                sheet.Columns(i).SetUnits('nm')
                sheet.Columns(i).SetComments(str(1+int(i/2)))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
                sheet.Columns(i+1).SetLongName('Intensity')
                sheet.Columns(i+1).SetUnits('counts')
                sheet.Columns(i+1).SetComments(str(1+int(i/2)))
                sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's i col as X
                rng.Add('X', sheet, 0, i, -1, i)
                # graph worksheet's i+2 col as Y
                rng.Add('Y', sheet, 0, i+1, -1, i+1)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

        elif file == 'eis':

            # only select data columns corresponding to Bode Z data
            data_bd_z = np.empty((len(data), 0))
            for i in range(0, len(data[0]), 5):
                data_bd_z = np.column_stack((data_bd_z, data[:, i]))
                data_bd_z = np.column_stack((data_bd_z, data[:, i+1]/1e6))

            # create worksheet and plot
            sheet = get_sheet(file+'_bode_z', data_bd_z)
            # create impedance plot
            gl, rng = get_plot(file+'_z')
            for i in range(0, len(data_bd_z[0]), 2):
                sheet.Columns(i).SetLongName('Frequency')
                sheet.Columns(i).SetUnits('Hz')
                sheet.Columns(i).SetComments(str(1+int(i/2)))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
                sheet.Columns(i+1).SetLongName('Z')
                sheet.Columns(i+1).SetUnits('MOhm')
                sheet.Columns(i+1).SetComments(str(1+int(i/2)))
                sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's i col as X
                rng.Add('X', sheet, 0, i, -1, i)
                # graph worksheet's i+1 col as Y
                rng.Add('Y', sheet, 0, i+1, -1, i+1)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

            # Z data with only one frequency column for heatmap plotting
            # use the last set of measured frequencies as "X" column
            data_bd_z2 = data[:, -5]
            for i in range(0, len(data[0]), 5):
                data_bd_z2 = np.column_stack((data_bd_z2, data[:, i+1]/1e6))

            # create worksheet and plot
            sheet = get_sheet('bode_z_clean', data_bd_z2)
            # create plot
            # gl, rng = get_plot('z_clean')
            sheet.Columns(0).SetLongName('Frequency')
            sheet.Columns(0).SetUnits('Hz')
            sheet.Columns(0).SetComments('0')
            sheet.Columns(0).SetType(PyOrigin.COLTYPE_DESIGN_X)
            # rng.Add('X', sheet, 0, 0, -1, 0)
            for i in range(1, len(data_bd_z2[0])):
                sheet.Columns(i).SetLongName('Z')
                sheet.Columns(i).SetUnits('MOhm')
                sheet.Columns(i).SetComments(str(i-1))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's Y columns
                # rng.Add('Y', sheet, 0, i, -1, i)
            # dp = gl.AddPlot(rng, 200)
            # PyOrigin.LT_execute('layer -g')

            # only select data columns corresponding to Bode phase data
            data_bd_phi = np.empty((len(data), 0))
            for i in range(0, len(data[0]), 5):
                data_bd_phi = np.column_stack((data_bd_phi, data[:, i]))
                data_bd_phi = np.column_stack((data_bd_phi, data[:, i+2]))

            # create worksheet and plot
            sheet = get_sheet(file+'_bode_phase', data_bd_phi)
            # create phase plot
            gl, rng = get_plot(file+'_phase')
            for i in range(0, len(data_bd_phi[0]), 2):
                sheet.Columns(i).SetLongName('Frequency')
                sheet.Columns(i).SetUnits('Hz')
                sheet.Columns(i).SetComments(str(1+int(i/2)))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
                sheet.Columns(i+1).SetLongName('Phase')
                sheet.Columns(i+1).SetUnits('deg')
                sheet.Columns(i+1).SetComments(str(1+int(i/2)))
                sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's i col as X
                rng.Add('X', sheet, 0, i, -1, i)
                # graph worksheet's i+1 col as Y
                rng.Add('Y', sheet, 0, i+1, -1, i+1)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

            # phase data with only one frequency column for heatmap plotting
            # use the last set of measured frequencies as "X" column
            data_bd_phi2 = data[:, -5]
            for i in range(0, len(data[0]), 5):
                data_bd_phi2 = np.column_stack((data_bd_phi2, data[:, i+2]))

            # create worksheet and plot
            sheet = get_sheet('bode_phase_clean', data_bd_phi2)
            # create phase plot
            # gl, rng = get_plot('phase_clean')
            sheet.Columns(0).SetLongName('Frequency')
            sheet.Columns(0).SetUnits('Hz')
            sheet.Columns(0).SetComments('0')
            sheet.Columns(0).SetType(PyOrigin.COLTYPE_DESIGN_X)
            # rng.Add('X', sheet, 0, 0, -1, 0)
            for i in range(1, len(data_bd_phi2[0])):
                sheet.Columns(i).SetLongName('Phase')
                sheet.Columns(i).SetUnits('deg')
                sheet.Columns(i).SetComments(str(i-1))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's Y columns
                # rng.Add('Y', sheet, 0, i, -1, i)
            # dp = gl.AddPlot(rng, 200)
            # PyOrigin.LT_execute('layer -g')

            # only select data columns corresponding to Nyquist data
            data_ny = np.empty((len(data), 0))
            for i in range(0, len(data[0]), 5):
                data_ny = np.column_stack((data_ny, data[:, i+3]/1e6))
                data_ny = np.column_stack((data_ny, data[:, i+4]/1e6))
            # create worksheet and plot
            sheet = get_sheet(file+'_nyquist', data_ny)
            # create impedance plot
            gl, rng = get_plot(file+'_nyquist')
            for i in range(0, len(data_ny[0]), 2):
                sheet.Columns(i).SetLongName('Re(Z)')
                sheet.Columns(i).SetUnits('MOhm')
                sheet.Columns(i).SetComments(str(1+int(i/2)))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
                sheet.Columns(i+1).SetLongName('Im(Z)')
                sheet.Columns(i+1).SetUnits('MOhm')
                sheet.Columns(i+1).SetComments(str(1+int(i/2)))
                sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's i col as X
                rng.Add('X', sheet, 0, i, -1, i)
                # graph worksheet's i+2 col as Y
                rng.Add('Y', sheet, 0, i+1, -1, i+1)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

            '''
            #only select data columns corresponding to Bode data
            data_bd = np.empty((len(data), 0))
            for i in range(0, len(data[0]), 5):
                data_bd = np.column_stack((data_bd, data[:, i]))
                data_bd = np.column_stack((data_bd, data[:, i+1]/1e6))
                data_bd = np.column_stack((data_bd, data[:, i+2]))
            #create worksheet and plot
            sheet = get_sheet(file+'_bode', data_bd)
            # create impedance plot
            gl, rng = get_plot(file+'_z')
            for i in range(0, len(data_bd[0]), 3):
                sheet.Columns(i).SetLongName('Frequency')
                sheet.Columns(i).SetUnits('Hz')
                sheet.Columns(i).SetComments(str(1+int(i/3)))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
                sheet.Columns(i+1).SetLongName('Z')
                sheet.Columns(i+1).SetUnits('MOhm')
                sheet.Columns(i+1).SetComments(str(1+int(i/3)))
                sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                sheet.Columns(i+2).SetLongName('Phase')
                sheet.Columns(i+2).SetUnits('deg')
                sheet.Columns(i+2).SetComments(str(1+int(i/3)))
                sheet.Columns(i+2).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                # graph worksheet's i col as X
                rng.Add('X', sheet, 0, i, -1, i)
                # graph worksheet's i+2 col as Y
                rng.Add('Y', sheet, 0, i+1, -1, i+1)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

            # create phase plot
            gl, rng = get_plot(file+'_phase')
            for i in range(0, len(data_bd[0]), 5):
                # graph worksheet's i col as X
                rng.Add('X', sheet, 0, i, -1, i)
                # graph worksheet's i+2 col as Y
                rng.Add('Y', sheet, 0, i+2, -1, i+2)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')
            '''

        elif file == 'qcm_params':
            # separate delta f and delta D data and normalize by n
            df_norm, dd_norm = norm_qcm_params(data)

            # delta F
            # create worksheet and plot
            sheet = get_sheet(file+'_df', df_norm)
            gl, rng = get_plot(file+'_df')

            sheet.Columns(0).SetLongName('Time')
            sheet.Columns(0).SetType(PyOrigin.COLTYPE_DESIGN_X)
            # graph worksheet's i col as X
            rng.Add('X', sheet, 0, 0, -1, 0)
            for i in range(1, len(df_norm[0])):
                sheet.Columns(i).SetLongName('Delta F / n')
                sheet.Columns(i).SetUnits('kHz/cm^2')
                sheet.Columns(i).SetComments(str((i-1)*2+1))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                rng.Add('Y', sheet, 0, i, -1, i)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

            # delta D
            # create worksheet and plot
            sheet = get_sheet(file+'_dd', dd_norm)
            gl, rng = get_plot(file+'_dd')

            sheet.Columns(0).SetLongName('Time')
            sheet.Columns(0).SetType(PyOrigin.COLTYPE_DESIGN_X)
            # graph worksheet's i col as X
            rng.Add('X', sheet, 0, 0, -1, 0)
            for i in range(1, len(dd_norm[0])):
                sheet.Columns(i).SetLongName('Delta D')
                sheet.Columns(i).SetUnits('x 10^-6')
                sheet.Columns(i).SetComments(str((i-1)*2+1))
                sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_Y)
                rng.Add('Y', sheet, 0, i, -1, i)
            dp = gl.AddPlot(rng, 200)
            PyOrigin.LT_execute('layer -g')

        else:
            pass

        # save origin file
        PyOrigin.Save(save_origin_filename)

    else:
        pass

# quit origin
# quit()
