# -*- coding: utf-8 -*-
"""
This is the internal Origin python script which runs inside Origin when
Origin is called externally from python.

Created on Thu Mar  7 15:01:32 2019
@author: ericmuckley@gmail.com
"""

# This PyOrigin example will import an ASCII file into an Origin worksheet and
# create a scatter plot from the data.


import PyOrigin
import os
import sys
import csv
import glob
# add path to non-standard python libraries so they can be imported
# lib_path = 'C:\\Users\\a6q\\AppData\\Local\\Continuum\\Anaconda3\\Lib\\site-packages'
# sys.path.append(lib_path)


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


'''
# sample data
data = [[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
        [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
        [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
        [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
        [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
        [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
        [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]]
'''



# get path of data folder
exp_start_time = sys.argv[1]
data_folder = sys.argv[2]
# get list of relevant data files
file_dict = get_file_dict(exp_start_time, data_folder)

col_num_dict = {}

#loop over every relevant data file and open new worksheet for each one
for file in file_dict:

    # get data from file
    filename = file_dict[file]
    headers, data = import_csv(filename)
    # get number of columns in data
    col_num_dict[file] = len(data)    

    # create workbook named 'file' using template named 'Origin'
    PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS, 'data-'+file, 'Origin', 1)
    # get active sheet
    #sheet = PyOrigin.GetPage('data_'+file) #PyOrigin.Pages(str(file)) 
    # Get sheet
    sheet = PyOrigin.ActiveLayer() 
    # put imported data into worksheet
    sheet.SetData(data, -1) 
    # set sheet name
    sheet.SetName(file)
    
    # script will fail if column designation is set for column that
    # doesn't exist. Number of columns is controlled by size of data.

    if file == 'iv':
        
        # create graph page named 'plot_file' using template'
        pgName = PyOrigin.CreatePage(PyOrigin.PGTYPE_GRAPH,
                                     'plot'+file+exp_start_time, 'iv', 1)
        gp = PyOrigin.Pages(str(pgName))
        gp.LT_execute("layer1.x.opposite = 1;layer1.y.opposite = 1;")
        gl = gp.Layers(0)
        # Create data range and plot it into the graph layer.
        rng = PyOrigin.NewDataRange()  # Create data range.
        
        #= file
        #    #sheet = PyOrigin.WorksheetPages(file).Layers(0)
        #PyOrigin.LT_execute('page -t iv')
        
        for i in range(0, col_num_dict[file], 2):
            sheet.Columns(i).SetLongName('Bias')
            sheet.Columns(i+1).SetLongName('Current')
            sheet.Columns(i).SetUnits('V')
            sheet.Columns(i+1).SetUnits('nA')
            sheet.Columns(i).SetComments(str(1+int(i/2)))
            sheet.Columns(i+1).SetComments(str(1+int(i/2)))
            sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
            sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)

            rng.Add('X', sheet, 0, i, -1, i) # Add worksheet's 2nd col as X.
            rng.Add('Y', sheet, 0, i+1, -1, i+1) # Add worksheet's 3rd col as Y.
            
        dp = gl.AddPlot(rng, 202)
        
        rng = PyOrigin.NewDataRange()# Plot data range.
        rng.Add('X', sheet, 0, 0, -1, 0)
        rng.Add('Y', sheet, 0, 1, -1, 1)
        
        dpc = gl.AddPlot(rng, 230)
        PyOrigin.LT_execute('layer -g')
        
       
    if file == 'cv':
        pgName = PyOrigin.CreatePage(PyOrigin.PGTYPE_GRAPH,
                                     'plot'+file+exp_start_time, 'cv', 1)
        gp = PyOrigin.Pages(str(pgName))
        gp.LT_execute("layer1.x.opposite = 1;layer1.y.opposite = 1;")
        gl = gp.Layers(0)
        # Create data range and plot it into the graph layer.
        rng = PyOrigin.NewDataRange() 
        for i in range(0, col_num_dict[file], 2):
            sheet.Columns(i).SetLongName('Bias')
            sheet.Columns(i+1).SetLongName('Current')
            sheet.Columns(i).SetUnits('V')
            sheet.Columns(i+1).SetUnits('nA')
            sheet.Columns(i).SetComments(str(1+int(i/2)))
            sheet.Columns(i+1).SetComments(str(1+int(i/2)))
            sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
            sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
            
            rng.Add('X', sheet, 0, i, -1, i) # Add worksheet's 2nd col as X.
            rng.Add('Y', sheet, 0, i+1, -1, i+1) # Add worksheet's 3rd col as Y.
            
        dp = gl.AddPlot(rng, 200)     
        PyOrigin.LT_execute('layer -g')
    if file == 'bs':
        pgName = PyOrigin.CreatePage(PyOrigin.PGTYPE_GRAPH,
                                     'plot'+file+exp_start_time, 'bs', 1)
        gp = PyOrigin.Pages(str(pgName))
        gp.LT_execute("layer1.x.opposite = 1;layer1.y.opposite = 1;")
        gl = gp.Layers(0)
        
        rng = PyOrigin.NewDataRange() 
        for i in range(0, col_num_dict[file], 3):
            sheet.Columns(i).SetLongName('Time')
            sheet.Columns(i+1).SetLongName('Bias')
            sheet.Columns(i+2).SetLongName('Current')
            sheet.Columns(i).SetUnits('min')
            sheet.Columns(i+1).SetUnits('V')
            sheet.Columns(i+2).SetUnits('nA')
            sheet.Columns(i).SetComments(str(1+int(i/3)))
            sheet.Columns(i+1).SetComments(str(1+int(i/3)))
            sheet.Columns(i+2).SetComments(str(1+int(i/3)))
            sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
            sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
            sheet.Columns(i+2).SetType(PyOrigin.COLTYPE_DESIGN_Y)
            
            rng.Add('X', sheet, 0, i, -1, i) # Add worksheet's 2nd col as X.
            rng.Add('Y', sheet, 0, i+2, -1, i+2)
           # Add worksheet's 3rd col as Y.
            
        dp = gl.AddPlot(rng, 201)  
        PyOrigin.LT_execute('layer -g')
    if file == 'optical':
        pgName = PyOrigin.CreatePage(PyOrigin.PGTYPE_GRAPH,
                                     'plot'+file+exp_start_time, 'optical', 1)
        gp = PyOrigin.Pages(str(pgName))
        gp.LT_execute("layer1.x.opposite = 1;layer1.y.opposite = 1;")
        gl = gp.Layers(0)
        # Create data range and plot it into the graph layer.
        rng = PyOrigin.NewDataRange() 
        for i in range(0, col_num_dict[file], 2):
            sheet.Columns(i).SetLongName('Wavelength')
            sheet.Columns(i+1).SetLongName('Intensity')
            sheet.Columns(i).SetUnits('nm')
            sheet.Columns(i+1).SetUnits('counts')
            sheet.Columns(i).SetComments(str(1+int(i/2)))
            sheet.Columns(i+1).SetComments(str(1+int(i/2)))
            sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)
            sheet.Columns(i+1).SetType(PyOrigin.COLTYPE_DESIGN_Y)
            
            rng.Add('X', sheet, 0, i, -1, i) # Add worksheet's 2nd col as X.
            rng.Add('Y', sheet, 0, i+1, -1, i+1) # Add worksheet's 3rd col as Y.
            
        dp = gl.AddPlot(rng, 200)  
        PyOrigin.LT_execute('layer -g')
    if file == 'qcm_params':
        pass
    if file == 'main':
        pass

'''
# create graph page named 'file' using template named 'Origin'.
pgName = PyOrigin.CreatePage(PyOrigin.PGTYPE_GRAPH,
 file, 'Origin', 1)
gp = PyOrigin.Pages(str(pgName))
gp.LT_execute("layer1.x.opposite = 1;layer1.y.opposite = 1;")
gl = gp.Layers(0)

# Create data range and plot it into the graph layer.
rng = PyOrigin.NewDataRange()  # Create data range.
rng.Add('X', wks, 0, 1, -1, 1) # Add worksheet's 2nd col as X.
rng.Add('Y', wks, 0, 2, -1, 2) # Add worksheet's 3rd col as Y.
dp = gl.AddPlot(rng, 201)      # Plot data range.
'''     
 


# save origin file
save_origin_filename = 'C:\\Users\\Ivan\\Desktop\\'+exp_start_time+'\\'+exp_start_time+'_results.opj'
PyOrigin.Save(save_origin_filename)

img_save_path = 'C:\\Users\\Ivan\\Documents\\OriginLab\\User Files\\'+exp_start_time
PyOrigin.XF('expGraph', {'type':'png','export':'project','overwrite':'rename', 'filename':'<short name>', 'tr1.unit':2, 'tr1.width':600, 'path':'C:\\Users\\Ivan\\Desktop\\'+exp_start_time})
quit()
             





'''
# Create worksheet page named 'MyData' using template named 'Origin'.
pgName = PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS, str(file), "Origin", 1)
wp = PyOrigin.Pages(str(pgName)) # Get page
wks = PyOrigin.ActiveLayer()     # Get sheet

# Setup worksheet.
#wks.SetData(data, -1) # Put imported data into worksheet.
wks.SetName(file) # Set sheet name to file name without path.



if file == 'iv':
# create worksheet page named 'filename' using template named 'Origin'
iv_book = PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS,
                             file,
                             'Origin', 1)
if file == 'cv':
# create worksheet page named 'filename' using template named 'Origin'
cv_book = PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS,
                             file,
                             'Origin', 1)
if file == 'bs':
# create worksheet page named 'filename' using template named 'Origin'
bs_book = PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS,
                             file,
                             'Origin', 1)

if file == 'main':
# create worksheet page named 'filename' using template named 'Origin'
main_book = PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS,
                             file,
                            'Origin', 1)
'''



'''
# get page
wp = PyOrigin.Pages(origin_sheet_dict[file]) 
# get worksheet
sheet = PyOrigin.ActiveLayer()     
# put imported data into worksheet
sheet.SetData(data)  
# set sheet name as the file name
sheet.SetName(file) 
'''
'''

# set worksheet label rows
sheet.Columns(0).SetLongName(headers)

# set worksheet X column designations
for i in range(len(headers), 0, 2):
sheet.Columns(i).SetType(PyOrigin.COLTYPE_DESIGN_X)


'''

'''
file_dict = get_file_dict(exp_start_time, data_folder)
file0 = file_dict['iv']
data = pd.read_csv(file0)


# Create worksheet page named 'MyData' using template named 'Origin'.
pgName = PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS, "MyData", "Origin", 1)
wp = PyOrigin.Pages(str(pgName)) # Get page
wks = PyOrigin.ActiveLayer()     # Get sheet

# Setup worksheet.
wks.SetData(data, -1)                     # Put imported data into worksheet.
wks.SetName(file0.split('\\')[-1]) # Set sheet name to file name without path.



'''


'''


# Read all non-empty lines from file.
content = [i for i in open(dataFileName) if i[:-1]]
totalrow = len(content)

# Count header lines by finding first row with 80% of it's content is numeric.
elementFlag = []
rowFlag = []
for i in list(range(totalrow)):
	content[i] = content[i].rstrip().split("\t")
	elementFlag = [isNumber(element) for element in content[i]]
	if sum(elementFlag) / len(elementFlag) < 0.8:
		rowFlag.append(0)
	else:
		rowFlag.append(1)

headerlines = len(rowFlag) - rowFlag[::-1].index(0)
nheadercol = max([len(x) for x in content[0:headerlines]])

colUnits = content[headerlines - 2]    # second last header line has units
colComments = content[headerlines - 1] # last header line has comments
colLongNames = []
colLongNames.extend(''.join(element) for element in content[0:headerlines - 2])
colLongNames = '         '.join(colLongNames)

## Number of numeric columns and rows
ncol = max([len(x) for x in content[headerlines:totalrow]])
nrow = totalrow - headerlines

## Obtain numeric data in file "Step01.dat"
data = []
columns = []
for i in list(range(ncol)):
	columns = [float(element[i]) if isNumber(element[i]) else element[i] for element in content[headerlines:totalrow]]
	data.append(columns)

# Create worksheet page named 'MyData' using template named 'Origin'.
pgName = PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS, "MyData", "Origin", 1)
wp = PyOrigin.Pages(str(pgName)) # Get page
wks = PyOrigin.ActiveLayer()     # Get sheet

# Setup worksheet.
wks.SetData(data, -1)                     # Put imported data into worksheet.
wks.SetName(dataFileName.split("\\")[-1]) # Set sheet name to file name without path.

# Set worksheet X column designations.
for i in list(range(math.floor(ncol / 2))):
	wks.Columns(2 * i + 1).SetType(PyOrigin.COLTYPE_DESIGN_X)

# Set worksheet label rows.
wks.Columns(0).SetLongName(colLongNames)
for i in list(range(nheadercol)):
	wks.Columns(i).SetUnits(colUnits[i])
	wks.Columns(i).SetComments(colComments[i])

# Create graph page named 'MyGraph' using template named 'Origin'.
pgName = PyOrigin.CreatePage(PyOrigin.PGTYPE_GRAPH, "MyGraph", "Origin", 1)
gp = PyOrigin.Pages(str(pgName))
gp.LT_execute("layer1.x.opposite = 1;layer1.y.opposite = 1;")
gl = gp.Layers(0)

# Create data range and plot it into the graph layer.
rng = PyOrigin.NewDataRange()  # Create data range.
rng.Add('X', wks, 0, 1, -1, 1) # Add worksheet's 2nd col as X.
rng.Add('Y', wks, 0, 2, -1, 2) # Add worksheet's 3rd col as Y.
dp = gl.AddPlot(rng, 201)      # Plot data range.
'''