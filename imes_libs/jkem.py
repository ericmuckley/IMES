# -*- coding: utf-8 -*-
"""
This module allows communication between a local PC and a CADES virtual
machine instance at ORNL.

Packages required:
paramiko

Created on Tue Jan 15 17:33:40 2019
@author: ericmuckley@gmail.com
"""

def open_ssh_tunnel(cades_ip='172.22.5.231',
                    key_file_path='C:\\Users\\a6q\\tf-container.pem'):
    '''Open a connection to ORNL CADES virtual machine using the CADES 
    IP address and a path to the .pem private key file for the CADES instance.
    Example inputs:
        cades_ip = '172.22.5.231'    
        key_file_path = 'C:\\Users\\a6q\\tf-container.pem'
    Returns an SSH session instance.
    '''
    import paramiko
    k = paramiko.RSAKey.from_private_key_file(key_file_path)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_system_host_keys()
    ssh.connect(hostname=cades_ip, username='cades', pkey=k)
    return ssh

def send_to_cades(ssh, local_file_path, cades_file_path):
    '''Send a local file to CADES.
    Example inputs:
        ssh = open_ssh_tunnel(cades_ip, key_file_path)
        local_file_path = 'C:\\Users\\a6q\\exp_data\\my_text.txt'
        cades_file_path = '/home/cades/my_text.txt'
    '''
    ftp = ssh.open_sftp()
    ftp.put(local_file_path, cades_file_path)
    ftp.close()

def pull_from_cades(ssh, local_file_path, cades_file_path):
    '''Pull a file from CADES onto local PC.
    Example inputs:
        ssh = open_ssh_tunnel(cades_ip, key_file_path)    
        local_file_path = 'C:\\Users\\a6q\\exp_data\\my_text.txt'
        cades_file_path = '/home/cades/my_text.txt'
    '''
    ftp = ssh.open_sftp()
    ftp.get(cades_file_path, local_file_path)
    ftp.close()

def run_script_on_cades(ssh, cades_script_path):
    '''Run a Python script on CADES from the local PC and 
    prints the output and errors from the script.
    Example inputs:
        ssh = open_ssh_tunnel(cades_ip, key_file_path)    
        cades_script_path = '/home/cades/scripts/my_python_script.py'
    '''
    stdin, stdout, stderr = ssh.exec_command('python '+cades_script_path)
    [print(line) for line in stdout.readlines()]
    [print(line) for line in stderr.readlines()]