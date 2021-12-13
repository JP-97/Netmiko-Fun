import os
import json
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from datetime import date, datetime
import pprint
import re

SCRIPT_LOCATION = os.path.dirname(__file__)

def timer(func):
    """
    Basic decorator function to calculate the execution time of various parts of the script
    :param func: original function
    :return: wrapped function as 'wrapper'
    """
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
def _send_command(device, command = None, enable_mode = False, retries = 3):
    """
    This helper function is used to add some runtime checking in case the ssh connection times out, etc.
    :param device: the dict corresponding to the device you're trying to connect too
    :param command: the command that will be issued to the device
    :param enable_mode: True if the command should be executed in the device's enable mode
    :return: result returned by issuing the command
    """
    current_try = 0

    while current_try <= retries:
        try:
            net_connect = ConnectHandler(**device)

            if enable_mode:
                net_connect.enable()

            command_result = net_connect.send_command(command, use_textfsm = True)
            return command_result

        except NetmikoTimeoutException as e:
            print(f"Your connection timed out and the following was thrown: {e} \n")

        except NetmikoAuthenticationException as e:
            print(f"Script could not authenticate with device and the following was thrown: {e}")

        current_try += 1
        if not current_try > retries:
            print(f"Retrying connection... retry attempt number {current_try}")

    print("Max number of tries has been reached... return Null")
    return None

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
                    f.write(neighbor['neighbor'] + '\t local int: ' + neighbor['local_interface'] + '\t '
                                                   'neighbor_int: ' + neighbor['neighbor_interface'] + '\n')

@timer
def collate_run(device, running_config):
    """
    Used to collect the running configurations of all the devices and save them to the working directory
    :param device: device in which the running config is being pulled
    :param running_config: the running config response from 'show run'
    :return: None
    """
    device_hostname = _get_hostname(running_config)
    dir_name = _get_runtime_dir('Running Configs')
    file_name = str(device['host'] + ' (' + device_hostname + ')' + ".txt")

    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    run_config_results = os.path.join(dir_name,file_name)

    with open(run_config_results, 'w') as f:
        f.write(running_config)

@timer
def parse_interface_data(raw_data, hostIP = None):
    """
    This function will parse the interface statistics yielded by the show interfaces command
    :param raw_data: data returned by show interfaces command
    :param hostIP: the IP address corresponding to the device that ran show interfaces
    :return: None
    """
    interface_db = []

    for interface in raw_data:
        interface_dict = dict()

        if interface['ip_address']: #don't want to create a dict for interfaces that have no configurations
            interface_dict['interface'] = interface['interface']
            interface_dict['ip address'] = interface['ip_address']
            interface_dict['description'] = interface['description']
            interface_dict['input packets'] = interface['input_packets']
            interface_dict['output packets'] = interface['output_packets']
            interface_dict['input errors'] = interface['input_errors']
            interface_dict['crc errors'] = interface['crc']
            interface_dict['output errors'] = interface['output_errors']

            interface_db.append({hostIP : interface_dict})

    try:
        with open('interfaces_stats.txt', 'a') as f:
            pprint.pprint(interface_db, stream = f, sort_dicts=False)

    except Exception as e:
        print(f'The following exception was raised: {e}')

@timer
def validate_working_directory():
    """
    This function validates that:
        1. The Running Configs folder exists
        2. The Interface Stats folder exists
        3. The interconnectivity folder exists
    :return: None
    """
    paths = (SCRIPT_LOCATION+'\\Running Configs',
             SCRIPT_LOCATION+'\\Interface Stats',
             SCRIPT_LOCATION+'\\Interconnectivity Status')

    for path in paths:
        if not os.path.exists(path):
            print(f'Creating {path}')
            os.mkdir(path)
        else:
            print(f'{path} already exists')

def _get_runtime_dir(parent_dir):
    """
    Helper function to return a timestamped directory name
    :param parent_dir is the parent directory where you will make the sub_dir (ie. Running Configs)
    :return: Directory name in path notation
    """
    run_time = datetime.now().strftime('%m-%d-%y %H%M')
    dir_name = parent_dir + '\\' + parent_dir + ' ' + run_time + "h"

    return os.path.join(SCRIPT_LOCATION, dir_name)

def _get_hostname(data):
    """
    Helper function to parse the hostname from a running config
    :param data: running_config_data (for now)
    :return: hostname
    """
    match = re.search(r'hostname (\w+)', data)
    return match.group(1)