# -*- coding: utf-8 -*-
"""
Call Origin to open and instantly run an internal python script

Created on Thu Mar  7 15:01:32 2019
@author: ericmuckley@gmail.com
"""

import subprocess
import os

# designate path to Origin executable file to run
path_to_origin = "C:\Program Files\OriginLab\Origin2019\Origin96_64.exe"
# designate name of internal Origin script to run when origin opens
# this should be located in Origin User Files folder
internal_origin_script = 'C:\\Users\\Ivan\\Documents\\OriginLab\\User Files\\internal_imes_script.py'
# path to data_folder
data_folder = 'C:\\Users\\Ivan\\exp_data\\sample_imes_python_data'
# experiment start time
exp_start_time = '2019-03-05_17-56'


def call_origin(path_to_origin, internal_origin_script,
                data_folder, exp_start_time):

    '''
    # arguments to pass to origin when it is called to run
    origin_args = [
            path_to_origin,
            '-rs run -pyf',
            internal_origin_script,
            exp_start_time,
            data_folder,
            ]
    # total command to give when opening origin
    total_origin_call = ' '.join(origin_args)
    '''
    # subprocess.call() will hang python until origin closes,
    # subprocess.Popen with start origin in a new thread
    # call origin to open, run, and run internal python script 
    #subprocess.call(total_origin_call)
    # call origin to open, run, and run internal python script 
    subprocess.Popen([path_to_origin, '-rs', 'run', '-pyf',
                      internal_origin_script,
                      exp_start_time,
                      data_folder])

try:
    os.makedirs('C:\\Users\\Ivan\\Desktop\\'+exp_start_time)
except FileExistsError:
    # directory already exists
    pass

call_origin(path_to_origin, internal_origin_script, data_folder, exp_start_time)

print('Exporting Done')





'''
# path to data_folder
data_folder = '\\path\\to\\data\\folder\\'
# experiment start time
exp_start_time = time.strftime('2019-03-07_15-28')

# arguments to pass to Origin when it is called to run
origin_args = [path_to_origin,
               '-rs run -pyf',
               internal_origin_py,
               data_folder,
               exp_start_time]
# total command to give when opening Origin
total_origin_call = ' '.join(origin_args)

# call origin to open, run, and run internal python script 
# subprocess.call(total_origin_call)
 
'''

'''

# in the internal Origin python file, access variables like:
import os
import sys
import glob


#print(len(sys.argv))
#print(sys.argv[1])

# get path of data folder
#data_folder = sys.argv[1]
data_folder = 'C:\\Users\\a6q\\imes_python\\measurement_data'



def get_file_dict(exp_start_time, data_folder):
    # get a dictionary of each data file and what type of data it holds based
    # on the experiment start time and folder of data files.
    # get list of all data files in data folder
    all_data_files = glob.glob(data_folder + '\\' + '\*')
    # list of data descriptors (strings) which should show up in file names
    data_file_descriptors = ['main', 'qcm_params', 'iv', 'cv', 
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


file_dict = get_file_dict(exp_start_time, data_folder)
'''
