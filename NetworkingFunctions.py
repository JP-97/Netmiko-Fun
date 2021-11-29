import os
import json
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from datetime import date, datetime

def timer(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        print(f"Execution time of {func.__name__} was {end_time - start_time}s using arguments {args} and {kwargs}")
        return result
    return wrapper

def load_devices(device_list = None):
    """
    Loads in device list representative of the network
    :param device_list: location to file holding devices
    :return: dict containing json data
    """
    with open(device_list, 'r') as f:
        f_json = json.load(f)['devices']
        return f_json

@timer
def _send_command(device, command = None, enable_mode = False):
    """
    This helper function is used to add some runtime checking in case the ssh connection times out, etc.
    :param device: the dict corresponding to the device you're trying to connect too
    :param command: the command that will be issued to the device
    :param enable_mode: True if the command should be executed in the device's enable mode
    :return: result returned by issuing the command
    """
    try:
        net_connect = ConnectHandler(**device)

        if enable_mode:
            net_connect.enable()

        command_result = net_connect.send_command(command, use_textfsm = True)
        return command_result

    except NetmikoTimeoutException as e:
        print(f"Your connection timed out and the following was thrown: {e}")
    except NetmikoAuthenticationException as e:
        print(f"Script could not authenticate with device and the fololwing was thrown: {e}")

@timer
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

    for device in devices:
        cdp_device = _send_command(device, 'show cdp neighbors')
        if cdp_device:
            with open(connectivity_db,'a') as f:
                f.write("Neighbors for " + device["host"] + "\n")
                for neighbor in cdp_device:
                    f.write(neighbor['neighbor'] + '\t local int: ' + neighbor['local_interface'] + '\t neighbor_int: ' + neighbor['neighbor_interface'] + '\n')

@timer
def collate_run(device, running_config):
    """
    Used to collect the running configurations of all the devices and save them to the working directory
    :param device: device in which the running config is being pulled
    :param running_config: the running config response from 'show run'
    :return: None
    """
    script_location = os.path.dirname(__file__) #this will find the absolute path of the script directory
    run_time = datetime.now().strftime('%m-%d-%y %H%M')
    folder_name = "Running Configs " + run_time +"h"
    file_name = str(device['host'] + ".txt")

    if not os.path.exists(os.path.join(script_location, 'Running Configs')):
        os.mkdir(os.path.join(script_location,'Running Configs'))

    running_config_dir = os.path.join(script_location, 'Running Configs')

    if not os.path.exists(os.path.join(running_config_dir, folder_name)):
        os.mkdir(os.path.join(running_config_dir,folder_name))

    run_config_results = os.path.join(running_config_dir,folder_name,file_name)

    with open(run_config_results, 'w') as f:
        f.write(running_config)
