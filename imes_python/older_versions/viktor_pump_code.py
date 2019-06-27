import serial

vac_dict = {'turbo_on': True,
            'turbo_address' = 'COM3',
            }



def turbo_checked(vac_dict):
    # run this function when turbo pump checkbox is checked/unchecked on GUI
    if vac_dict['turbo_on'].isChecked():
        vac_dict['turbo_dev'] = serial.Serial(vac_dict['turbo_address'], 19200, timeout=1.0)
    if not vac_dict['turbo_on'].isChecked():
        vac_dict['turbo_dev'].close()


def operate_turbo(vac_dict, run_pump=False):
    if run_pump:
        vac_dict['turbo_dev'].write(bytes.fromhex(
                '02 16 00 10 18 00 00 00 00 00 00 04 01 00 00 00 00 00 00 00 00 00 00 19'))
        read_message = vac_dict['turbo_dev'].readline().hex()
        print(read_message)
        vac_dict['turbo_speed'] = ((eval("0x"+read_message) & 0xffff000000000000000000) >> 72)
        print(vac_dict['turbo_speed'])
    else:
        vac_dict['turbo_dev'].write(bytes.fromhex(
                '02 16 00 10 18 00 00 00 00 00 00 04 00 00 00 00 00 00 00 00 00 00 00 18'))
        read_message = vac_dict['turbo_dev'].readline().hex()
        print(read_message)
        vac_dict['turbo_speed'] = 0
    return vac_dict['turbo_speed']
