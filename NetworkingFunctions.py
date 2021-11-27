import sys
import os
import json
from netmiko import ConnectHandler
from datetime import date, datetime

#This function will load in the network inventory
def Load_Devices(device_list = None):
    devices = open(device_list, "r")
    devices = json.load(devices)['devices']
    return devices

#This function will return a .txt the shows all the device interconnectivity
def Interconnectivity(devices, connectivity_db):
    for device in devices: #### Need to create a function that performs this loop so we dont need to keep re-writing this code
        net_connect = ConnectHandler(**device)
        cdp_device = net_connect.send_command('show cdp neighbors', use_textfsm = True)

        with open(connectivity_db,'a') as f: # with statement is used as a context manager. so long as we're within the with block the file will stay open. as soon as we leave, the file will be closed.
            f.write(str(date.today()) + "\n")
            f.write("Neighbors for " + device["host"] + "\n")
            for neighbor in cdp_device:
                f.write(neighbor['neighbor'] + '\t local int: ' + neighbor['local_interface'] + '\t neighbor_int: ' + neighbor['neighbor_interface'] + '\n')

#This function will return a folder containing each device's running configuration
def Collate_Run(devices):
    script_location = os.path.dirname(__file__) #this will find the absolute path of the script location
    run_time = datetime.now()
    run_time = run_time.strftime('%m-%d-%y %H%M')
    folder_name = "Running Configs " + run_time +"h"

    os.mkdir(folder_name)

    for device in devices:
        net_connect = ConnectHandler(**device)
        running_config = net_connect.send_command('show run', use_textfsm = True) #use textfsm to format output into dict

        file_name = str(device['host'] + ".txt")
        run_config_location = os.path.join(script_location,folder_name,file_name) #creates a folder in the working directory that is date stamped with the relevant host name

        with open(run_config_location, 'w') as f:
            f.write(running_config)

#returns the running config for a single device
def Get_Run(device):
    net_connect = ConnectHandler(**device)
    return net_connect.send_command('show run', use_textfsm = True)
