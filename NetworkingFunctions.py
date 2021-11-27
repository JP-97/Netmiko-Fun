import sys
import os
import json
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from datetime import date, datetime

def load_devices(device_list = None):
    """
    Loads in device list representative of the network
    :param device_list: location to file holding devices
    :return: dict containing json data
    """
    with open(device_list, 'r') as f:
        f_json = json.load(f)['devices']
        return f_json

def _establish_connection(device, command = None, enable_mode = False, credentials = None):
    """
    This helper function is used to add some runtime checking in case the ssh connection times out, etc.
    :param device: the dict corresponding to the device you're trying to connect too
    :param command: the command that will be issued to the device
    :param enable_mode: True if the command should be executed in the device's enable mode
    :param credentials: enable mode credentials
    :return:
    """
    try:
        net_connect = ConnectHandler(**device)

        if enable_mode: #need to add functionality to pass enable credentials if there are any
            net_connect.enable()

        command_result = net_connect.send_command(command, use_textfsm = True)
        return command_result

    except NetmikoTimeoutException as e:
        print(f"Your connection timed out and the following was thrown: {e}")
    except NetmikoAuthenticationException as e:
        print(f"Script could not authenticate with device and the fololwing was thrown: {e}")


def check_interconnectivity(devices, connectivity_db):
    """
    This function writes all of the active connections, from each device's perspective, to a database
    :param devices: dict containing all the devices imported from load_devices
    :param connectivity_db: .txt file where the results will be written
    :return: None
    """
    #Add the date prior to iterating through all the devices
    with open(connectivity_db, 'a') as f:
        f.write(str(date.today()) + "\n")

    for device in devices: #### Need to create a function that performs this loop so we dont need to keep re-writing this code
        cdp_device = _establish_connection(device, 'show cdp neighbors')
        if cdp_device:
            with open(connectivity_db,'a') as f:
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
