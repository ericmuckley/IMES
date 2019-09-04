# IMES Software

This repository contains software for controlling the Integrated Multifunctional Environmental System (IMES) at Center for Nanophase Materials Sciences (CNMS) at Oak Ridge National Laboratory (ORNL).

### Installing the software

The software requires no formal installation, but installation of missing Python libraries will likely be required when running the software for the first time. To download the missing libraries, it is recommended to use the scientific Python distribution _Anaconda_ (https://www.anaconda.com/). If _Anaconda_ is not present on the local PC, download it from its website and download the _imes_python_ folder in this repository to the local PC and unzip it.
<br><br>
To avoid installing individual libraries, the complete Python installation which includes all necessary packages is located in this folder as a _.yml_ file. Alternatively, the same _.yml_ file can be downloaded from Anaconda Cloud (https://anaconda.org/ericmuckley/imes_env_july2019)

### Installing Anaconda dependencies from the _.yml_ file

First, download the IMES folder from this page. Then unzip the folder and put it on your local PC. Open the Anaconda terminal window. Navigate to your IMES folder by typing ```cd C:\Users\a6q\Desktop\IMES``` in ther terminal window, but use the path to your own IMES folder. The terminal prompt should show you that you're now inside the IMES folder. Now you must install dependencies for running the software from the _.yml_ file.

In the Anaconda terminal (which has been already been navigated to the IMES folder), type ```conda env create --name envname --file=imes_env_july2019.yml```
This will create a new conda environment using the _imes_env_july2019.yml_ file, and name the new environment _envname_.

Now you can enter/activate the envirnment by typing ```conda activate envname```. Your terminal prompt should change to show that you're inside the new environment. Now you can type ```spyder``` and _Spyder_ should open inside your new environment. With _Spyder_ open, you can open the _IMES.py_ file and run it.

### Running the software

To run the IMES software, open a Python editor like *Spyder*, which comes pre-packaged with *Anaconda*. In the editor, open *IMES.py* in the *imes_python* folder. Run *IMES.py* in the editor. If there are errors because of missing libraries, you must first install those libraries. To install them, open the *Anaconda prompt*, which comes pre-packaged with *Anaconda*. In the Anaconda prompt, type `conda install library_name`, where *library_name* is the name of the missing library. You can do an internet search for "conda install X", where *X* is the missing library name to figure out the best way to install the package through *Anaconda*.
<br><br>
When all libraries are installed correctly and *IMES.py* runs successfully, a file browser dialog will pop up ask ask you to designate a folder in which to save the experimental data files. You may select an existing folder or create a new one and select it. After selecting a folder for data files, the GUI window will appear. 
<br><br>
To connect instuments, check the checkboxes on the left-hand side of the window. Before connecting an instument, change its address so it matches the actual physical address of the instument in the PC. It is easy to see which device addresses are connected using Windows *Device Manager* or National Instruments *Measurement and Automation Explorer*.
<br><br>
While the IMES software is running, the output box in the lower left-hand corner of the window displays messages to the user. Instument and measurement setttings can be adjusted on the front panel of the GUI, and measurements and sequences of measurements can be initiated using the top toolbar.

### Layout of the software

The main *IMES.py* file calls a number of files:\
**IMES_layout.ui**: the GUI layout file, which dictates where GUI objects are placed and their names\
**libusb-1.0.dll**: a Windows USB library which may be required for communication with USB devices\
**ornl_cnms_logo.png**: raw image file of CNMS logo which is embedded on GUI\
**ornl_cnms_logo.qrc**: Qt resource file created from raw png image\
**ornl_cnms_logo.py**: Python file freated from Qt resource file\
<br>
<br>
*IMES.py* also imports modules from the *IMES_libs* folder. These modules contain code for controlling instruments and measurement conditions inside the environmental chamber:\
**cades.py**: module for communicating with CADES server at ORNL\
**eis.py**: module for controlling Solartron 1260 impedance spectrometer\
**jkem.py**: module for controlling J-KEM temperature controller\
**keith.py**:	module for controlling Keithley 2420 multimeter\
**libusb-1.0.dll**: USB windows library which is needed for running IMES.py\
**ops.py**:	module for system operations like reading/writing data files, communication with Origin\
**origin.py**: module for communicating with Origin for plotting experimental results\
**realtimeplot.py**: module for creating real-time updating plots using the pyqtgraph library\
**rh200.py**:	module for controlling the RH-200 relative humidity generator\
**rhmeter.py**: module for controlling relative humidity and temperature meter\
**sark.py**: module for controlling SARK-110 antenna analyzer for QCM measurements\
**spec.py**: module for controlling Ocean Optics optical spectormeter\
**vac.py**: module for controlling the vacuum pressure, valve, turbo pump, and mass flow controllers\
<br>
<br>
Data is transferred between the main *IMES.py* script and the other modules using dictionaries which hold references to devices, front panel GUI objects, and measured parameters. There is a different dictionary associated with each module. For example, *vac_dict* holds information about the vacuum system and is used to communicate with the *vac.py* module, while *keith_dict* is used to transfer data to and from the *keith.py* module for controlling the Keithley multimeter. 


### Editing the software

To edit the GUI layout, use *QtDesigner* which comes pre-packaged with *Anaconda*, and open the *IMES_layout.ui* file. This is the editable layout file for designing the GUI. Front panel objects can be added, deleted and modified. New objects should be named according to their function, as referencing them in the code will require their name. For example, a new text box named *text_box5* will be referenced in the main GUI class in *IMES.py* as `self.ui.text_box5`.
<br><br>
*IMES.py* and other modules inside the *IMES_libs* folder are all editable. When changes are made to the GUI layout file, they should usually be accompanied by corresponding changes in the Python scripts. 
