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

import os
import time
import visa
import subprocess
import numpy as np
import inspect
import pywinusb.hid as hid
from PyQt5.QtWidgets import QLabel, QComboBox, QLineEdit, QSlider
from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton
from PyQt5.QtCore import QSettings


def main_loop_update(ops_dict, df, df_i):
    # Update fields on GUI, perform main operations, and save data
    # in main GUI loop.

    # timer which updates fields on GUI (set interval in ms)
    ops_dict['main_loop_delay'] = int(ops_dict['set_main_loop_delay'].value())
    ops_dict['timer'].start(ops_dict['main_loop_delay'])

    # update main loop counter display on GUI
    ops_dict['main_loop_counter_display'].setText(str(df_i))

    # record date/time and elapsed time at each iteration
    df['date'].iloc[df_i] = str(time.strftime('%Y-%m-%d_%H-%M-%S_'))[:-1]

    elapsed_time = np.round((
            time.time()-ops_dict['start_time'])/60, decimals=3)
    ops_dict['elapsed_time'] = elapsed_time
    df['time'].iloc[df_i] = str(elapsed_time)
    df['note'].iloc[df_i] = ops_dict['sample_name'].text()
    # save data
    if ops_dict['save_data_now'].isChecked():
        # mark current row as "saved"
        df['save'].iloc[df_i] = 'on'
        # every n points, save data to file
        if df_i % 10 == 0:
            # remove extra rows
            save_master_df = df[df['save'] == 'on']
            # remove "save" column
            save_master_df = save_master_df[save_master_df.columns[:-1]]

            # rename MFC column headers to include gas names
            gas1 = str(ops_dict['gas1'].currentText())
            gas2 = str(ops_dict['gas2'].currentText())
            save_master_df = save_master_df.rename(
                    columns={'mfc1': 'mfc1_'+gas1,
                             'mfc2': 'mfc2_'+gas2})

            # save dataframe to file
            save_master_df.to_csv(
                    ops_dict['save_file_dir']+'/'+ops_dict[
                            'start_date']+'_main_df.csv', index=False)
    # update GUI indicator of number of save data rows
    ops_dict['rows_of_saved_data'].setText(str(len(df[df['save'] != ''])))
    # increment main loop counter
    df_i = df_i + 1
    return df, df_i


def list_devices(ops_dict):
    # list all connected devices in the GUi output box
    rm = visa.ResourceManager()
    visa_devs = rm.list_resources()
    # get SARK devices
    target_vendor_id = 0x0483
    target_product_id = 0x5750
    filter = hid.HidDeviceFilter(vendor_id=target_vendor_id,
                                 product_id=target_product_id)
    sark_devs = filter.get_devices()
    ops_dict['output_box'].append('VISA DEVS: '+str(visa_devs))
    ops_dict['output_box'].append('SARK DEVS: '+str(sark_devs))


def view_file_save_dir(ops_dict):
    # Show the name of the file-saving directory in the output box on the GUI.
    try:  # if save file directory is already set
        ops_dict['output_box'].append('Current save file directory:')
        ops_dict['output_box'].append(ops_dict['save_file_dir'])
    except NameError:  # if file directory is not set
        ops_dict['output_box'].append(
                'No save file directory has been set.')
        ops_dict['output_box'].append(
                'Please set in File --> Change file save directory.')


def view_app_starttime(ops_dict):
    # print start time of the application in the output box.
    ops_dict['output_box'].append(
            'Application start time: '+str(ops_dict['start_date']))


def export_settings(ops_dict):
    # export app settings from file

    ops_dict['output_box'].append('Exporting experiment settings...')

    # create filepath for saved settings
    settings_filepath = os.path.join(
                    ops_dict['save_file_dir'],
                    ops_dict['start_date']+'_experiment_settings.ini')
    # save the name of the settigns filepath
    ops_dict['app_settings_filename'] = settings_filepath
    # create settings .ini file
    settings = QSettings(settings_filepath, QSettings.IniFormat)

    # scroll through each GUI widget and write its data to settings file
    for name, obj in inspect.getmembers(ops_dict['app']):
        if isinstance(obj, QComboBox):
            name = obj.objectName()
            text = obj.itemText(obj.currentIndex())
            settings.setValue(name, text)
        if isinstance(obj, QLineEdit):
            name = obj.objectName()
            value = obj.text()
            settings.setValue(name, value)
        if isinstance(obj, QCheckBox):
            name = obj.objectName()
            state = obj.checkState()
            settings.setValue(name, state)
        if isinstance(obj, QRadioButton):
            name = obj.objectName()
            value = obj.isChecked()
            settings.setValue(name, value)
        if isinstance(obj, QSpinBox):
            name = obj.objectName()
            value = obj.value()
            settings.setValue(name, value)
        if isinstance(obj, QDoubleSpinBox):
            name = obj.objectName()
            value = obj.value()
            settings.setValue(name, value)
        if isinstance(obj, QSlider):
            name = obj.objectName()
            value = obj.value()
            settings.setValue(name, value)

    ops_dict['app_settings'] = settings
    ops_dict['output_box'].append('Experiment settings exported.')


def str_to_bool(inp_str):
    # converts string to boolean value
    out = False
    if inp_str == 1:
        out = True
    elif inp_str == 0:
        out = False
    elif inp_str == '1':
        out = True
    elif inp_str == '2':
        out = True
    elif inp_str == 2:
        out = True
    elif inp_str == '0':
        out = False
    elif inp_str == 'True':
        out = True
    elif inp_str == 'False':
        out = False
    elif inp_str is None:
        pass
    else:
        pass
    return out


def import_settings(ops_dict, filepath):
    # import app settings from file and restore them in widgets
    ops_dict['output_box'].append('Importing experiment settings...')
    settings = QSettings(filepath, QSettings.IniFormat)

    # loop over each widget on GUI and resotre its values from settings file
    for name, obj in inspect.getmembers(ops_dict['app']):
        if isinstance(obj, QComboBox):
            index = obj.currentIndex()
            # text   = obj.itemText(index)
            name = obj.objectName()
            value = (settings.value(name))
            # if value == '':
            #    continue
            index = obj.findText(value)
            if index == -1:  # add to list if not found
                obj.insertItems(0, [value])
                index = obj.findText(value)
                obj.setCurrentIndex(index)
            else:
                obj.setCurrentIndex(index)
        elif isinstance(obj, QLineEdit):
            name = obj.objectName()
            value = settings.value(name)  # .decode('utf-8'))
            if value is not None:
                obj.setText(str(value))
        elif isinstance(obj, QCheckBox):
            name = obj.objectName()
            value = settings.value(name)
            if value is not None:
                obj.setChecked(str_to_bool(value))
        elif isinstance(obj, QRadioButton):
            name = obj.objectName()
            value = settings.value(name)
            if value is not None:
                obj.setChecked(str_to_bool(value))
        elif isinstance(obj, QSpinBox):
            name = obj.objectName()
            value = settings.value(name)
            if value is not None:
                obj.setValue(int(value))
        elif isinstance(obj, QDoubleSpinBox):
            name = obj.objectName()
            value = settings.value(name)
            if value is not None:
                obj.setValue(float(value))
        elif isinstance(obj, QLabel):
            pass
        else:
            pass
    ops_dict['output_box'].append(
            'Experiment settings imported from '+filepath)

#  ##########################################################################
# the following method is used to communicate with Origin:
# the method calls Origin to open and run an internal
# python script inside Origin
# ###########################################################################


def create_report(ops_dict):
    # create report of data in Origin. This method calls Origin to
    # open and automatically runs an internal python script inside Origin,
    # which imnports data from the current experiment, plots it, and
    # saves the Origin file.

    # the "path_to_origin" and "internal_origin_script" may yhave to be
    # changed to reflect changes in file location and Origin installation.

    # designate path to Origin executable file to run
    path_to_origin = 'C:\\Program Files\\OriginLab\\Origin 2019\\Origin96_64.exe'
    # designate name of internal Origin script to run when origin opens
    # this should be located in Origin User Files folder
    # internal_origin_script = 'C:\\Users\\a6q\\imes_python\\imes_libs\\internal_origin_script.py' 
    internal_origin_script = 'C:\\Users\\a6q\\Origin_user_files\\internal_origin_script.py'
    # designate data folder to look in, and most recent experiment date
    # data_folder = 'C:\\Users\\a6q\\imes_python\\measurement_data'
    data_folder = os.path.normpath(ops_dict['save_file_dir'])
    exp_start_time = ops_dict['start_date']
    # get rid of this line to make the date the most recent!!
    # exp_start_time = '2019-03-19_12-23_'

    ops_dict['output_box'].append('Opening '+str(path_to_origin)+'\n'
                                  'to run '+str(internal_origin_script)+' \n'
                                  'for data in '+str(data_folder)+' \n'
                                  'collected at '+str(exp_start_time)[:-1])

    try:
        sp = subprocess.Popen([path_to_origin, '-rs', 'run', '-pyf',
                               internal_origin_script,
                               exp_start_time,
                               data_folder])
        sp.wait()

    except:
        ops_dict['output_box'].append('Could not call Origin.')


if __name__ == '__main__':

    # test Origin communication
    # designate path to Origin executable file to run
    path_to_origin = 'C:\\Program Files\\OriginLab\\Origin 2019\\Origin96_64.exe'
    # designate name of internal Origin script to run when origin opens
    # this should be located in Origin User Files folder
    #internal_origin_script = 'C:\\Users\\Ivan\\Documents\\OriginLab\\User Files\\internal_origin_script.py'
    internal_origin_script = 'C:\\Users\\a6q\\Origin_user_files\\internal_origin_script.py'

    data_folder = os.path.normpath(
            'C:\\Users\\a6q\\imes_python\\measurement_data')
    # exp_start_time = '2019-03-19_12-23_'
    exp_start_time = '2019-03-22_18-55_'

    # call origin to open and run internal python script
    sp = subprocess.Popen([path_to_origin, '-rs', 'run', '-pyf',
                           internal_origin_script,
                           exp_start_time,
                           data_folder])
    sp.wait()


'''
    # test email sending
    # email from ORNL-networked machine is blocked by ORNL firewall
    from_address = 'imes.data@gmail.com'
    password_of_sender = 'imes.data2019'
    to_address = 'muckleyes@ornl.gov'
    subject_text = 'Message from i-moose system'
    attachment_file = 'C:\\Users\\a6q\\Pictures\\ornl_cnms_logo.png'
    # use '\n' character to begin new line in email body text
    body_text = ('Dear researcher, \n'
                 'This is a test message from the i-moose system at CNMS.\n'
                 '\n'
                 'There should be a test file attached to this email.\n'
                 'In the future, this attachment will be an Origin report of\n'
                 'recent experimental results.\n'
                 '\n'
                 'Stay tuned for more updates coming soon.\n'
                 '\n'
                 'Regards,\n'
                 'i-moose')

    send_email(to_address,
               attachment_file,
               subject_text,
               body_text)

'''


'''
#  ##########################################################################
# the following method is used to send email from a Gmail account with
# subject, body, and file attachment
# ###########################################################################

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# USE THIS ACCOUNT TO SEND EMAILS:
# email: imes.data@gmail.com
# password: imes.data2019

def send_email(to_address,
               attachment_file,
               subject_text,
               body_text,
               from_address='imes.data@gmail.com',
               password_of_sender='imes.data2019'):
    # send an email wtith attachment using a gmail account as the sender
    # instance of MIMEMultipart
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject_text
    # attach the body with the msg instance
    msg.attach(MIMEText(body_text, 'plain'))
    # open the file to be sent
    attachment = open(attachment_file, "rb")
    # instance of MIMEBase and named as p
    p = MIMEBase('application', 'octet-stream')
    # To change the payload into encoded form
    p.set_payload((attachment).read())
    # encode into base64
    encoders.encode_base64(p)
    p.add_header('Content-Disposition',
                 'attachment; filename= %s' % attachment_file)
    # attach the instance 'p' to instance 'msg'
    msg.attach(p)
    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
    # start TLS for security
    s.starttls()
    # Authentication
    s.login(from_address, password_of_sender)
    # Converts the Multipart msg into a string
    text = msg.as_string()
    # sending the mail
    s.sendmail(from_address, to_address, text)
    # terminating the session
    s.quit()
'''

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