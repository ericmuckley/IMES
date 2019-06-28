# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 16:19:04 2019

@author: ericmuckley@gmail.com
"""

import serial

vac_dict = {'turbo_dev': None}

vac_dict['turbo_dev'] = serial.Serial('COM3', 19200, timeout=5.0)

# command = vac_dict['turbo_dev'].write(command.encode('ascii'))




# create byte string out of hex
hex_str1 = '02 16 00 10 18 00 00 00 00 00 00 04 '
hex_str2 = '00 00 00 00 00 00 00 00 00 00 19'
hex_str_on = '01 '
hex_str_off = '00 '

on_command = bytes.fromhex(hex_str1 + hex_str_on + hex_str2)
off_command = bytes.fromhex(hex_str1 + hex_str_off + hex_str2)

print(on_command)
print(off_command)


vac_dict['turbo_dev'].write(on_command)#.encode('ascii'))

vac_dict['turbo_dev'].close()
