# IMES Software

This repository contains software for controlling the integrated multifunctional envinrmental system (IMES) at Center for Nanophase Materials Sciences (CNMS) at Oak Ridge National Laboratory (ORNL).

### Installing the software

The software requires no formal installation. It is recommnded to first download a scientific Python distribution such as *Anaconda* (https://www.anaconda.com/). The *imes_python* folder in this repository can then be cloned or downloaded to the local PC.

### Running the software

To run the software, open a Python editor like *Spyder*, which comes pre-packaged with *Anaconda*. In the editor, open *IMES.py* in the *imes_python* folder. Run *IMES.py* in the editor. If there are errors because of missing libraries, you must first install those libraries. To install them, open the Anaconda prompt which comes pre-packaged with *Anaconda*. In the Anaconda prompt, type `conda install library_name`, where *library_name* is the name of the missing linbrary. You can also do an internet search for "conda install X", where *X* is the library name, to figure out the best way to install the package through *Anaconda*.
<br>
When all libraries are installed correctly, the GUI will appear when *IMES.py* is run.


### Layout of the software



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

