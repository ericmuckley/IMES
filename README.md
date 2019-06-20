# IMES Software

This repository contains software for controlling the integrated multifunctional envinrmental system (IMES) at Center for Nanophase Materials Sciences (CNMS) at Oak Ridge National Laboratory (ORNL).

### Installing the software

The software requires no formal installation. It is recommnded to first download a scientific Python distribution such as Anaconda (https://www.anaconda.com/). The *imes_python* folder in this repository can then be cloned or downloaded to the local PC.

### Running the software

To run the software, 


### Layout of the software



*cades.py*: module for communicating with CADES virtual machine;
*eis.py*: module for controlling Solartron 1260 electrochemical impedance spectrometer;
*jkem.py*: module for controlling J-KEM temperature controller;
*keith.py*:	module for controlling Keithley 2420 multimeter;
*libusb-1.0.dll*: USB windows library which is needed for running IMES.py;
*ops.py*:	module for controlling main operations of IMES, like reading/writing data files, communication with Origin
*origin.py*: module for communicating with Origin for plotting experimental results
*realtimeplot.py*: module for creating real-time updating plots using the pyqtgraph library
*rh200.py*:	module for controlling the RH-200 relative humidity generator
*rhmeter.py*: module for controlling relative humidity and temperature meter
*sark.py*: module for controlling SARK-110 antenna analyzer for QCM measurements
*spec.py*: module for controlling Ocean Optics optical spectormeter
*vac.py*: module for controlling the vacuum system pressure controller, valve, turbo pump, and mass flow controllers

