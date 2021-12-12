from netmiko import ConnectHandler
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import NetworkingFunctions
from NetworkingClasses import Link, Device
from NetworkingFunctions import *
from NetworkingFunctions import _send_command
import sys

# Handle command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-I',
                    '--Interconnectivity',
                    action='store_true',
                    help='Only interconnectivity will be captured')

parser.add_argument('-R',
                    '--Running_Configs',
                    action='store_true',
                    help='Only running configs will be captured')

parser.add_argument('-S',
                    '--Interface_Stats',
                    action='store_true',
                    help='Only interface stats will be captured')

args = parser.parse_args()



nodes = []  # this will hold all the nodes in the network (ie. network devices)
edges = []  # this will hold a list of tuples representing the links between each device
interfaces = {}  # this will hold all the interface details for each link
device_db = []  # this will hold all the network devices in in the network
link_db = []  # this will hold all the  data link objects in the network

@timer
def main():
    """
    This function captures the main checks performed against the network. Writing this within a function allows us to
    use the timer decorator more easily
    :return: None
    """
    check_interconnectivity(
        devices, NetworkingFunctions.SCRIPT_LOCATION + "\\Interconnectivity Status\\Interconnectivity_Master.txt")
    _execute_single_run_capture()
    _gather_interface_stats()

def _execute_single_run_capture():
    same_device_list = True  # used so that running configs aren't split into two running config directories
    while same_device_list:
        try:
            for device in devices:
                running_config = _send_command(device, 'show run')
                collate_run(device, running_config)
        except Exception as e:
            print(
                'The configuration can\'t be polled twice in the same minute, the following exception was thrown: ',
                e)
        finally:
            same_device_list = False

def _gather_interface_stats():
    for device in devices:
        interface_data = _send_command(device, 'show interfaces')
        # print(interface_data)
        parse_interface_data(interface_data, device['host'])

if __name__ == "__main__":
    """
    Script launching point. Runs initial config checks and processes command line arguments.
    """

    validate_working_directory()
    devices = load_devices("devices.txt")

    if args.Interconnectivity:
        check_interconnectivity(
            devices, NetworkingFunctions.SCRIPT_LOCATION + "\\Interconnectivity Status\\Interconnectivity_Master.txt")

    if args.Running_Configs:
        _execute_single_run_capture()

    if args.Interface_Stats:
        _gather_interface_stats()

    if len(sys.argv) == 1:
        main()

    #### CREATING THE GRAPH ####
    #
    # for device in devices:
    #     net_connect = ConnectHandler(**device) #represents the ssh instance to the device
    #     running_config = Get_Run(device)
    #
    #     #parse out device hostname
    #     hostname = running_config.split("hostname ")
    #     hostname = hostname[1].split('\n')
    #     hostname = hostname[0]
    #
    #     #fetch CDP neighbors to build edges
    #     cdp_device = net_connect.send_command('show cdp neighbors', use_textfsm = True)
    #
    #     #populate database for all nodes in the network
    #     if hostname not in nodes: #here the list of nodes is acting as a running list of active devices known to the script
    #         nodes.append(hostname)
    #         device_db.append(Device(hostname, cdp_device, device["host"])) #create a unique Device object for each new device discovered in the network
    #
    # #iterate through all the possible edge combinations and build a database of unique edges
    # for device in device_db:
    #     for neighbor in device.neighbors: #show cdp neighbors returns an array of the neighboring devices, so you need to iterate
    #         neighbor_device = neighbor['neighbor'].split(".")[0]
    #         if ((device.hostname,neighbor_device) and (neighbor_device, device.hostname) not in edges): ###currently using edges to keep track of known links in the network, need to come up with a better way
    #             edges.append((device.hostname,neighbor_device))
    #             link_db.append(Link(device.hostname, neighbor_device, neighbor['local_interface'], neighbor['neighbor_interface']))
    #
    # #Debug
    # for link in link_db:
    #     print(link.hostname + ", " + link.neigbor)
    #
    # ###Creating network diagram
    # plt.figure(1,figsize = (12,12))
    # G = nx.Graph()
    #
    # #Graph objects
    # G.add_nodes_from(nodes) #this creates a node based on each of the nodes in list(nodes)
    # G.add_edges_from(edges) #this creates an edge based on each of the edges in list(tuple(edge))
    # pos = nx.spring_layout(G)
    #
    # nx.draw_networkx(G, pos, node_size = 1000, font_size = 8)
    #
    # for edge in edges:
    #     for link in link_db:
    #         if(edge[0] == link.hostname and edge[1] == link.neigbor): #this will allow us to know which link we're updating the labels for
    #             print(edge)
    #             print(link.local_int)
    #             print(link.neighbor_int)
    #             nx.draw_networkx_edge_labels(G, pos, edge_labels = {edge:link.local_int} , label_pos = 0.7) #this will create the label for the "host" (ie. the device that executed the cdp call)
    #             nx.draw_networkx_edge_labels(G, pos, edge_labels = {edge:link.neighbor_int}, label_pos = 0.3) #this will create the lable for the "neighbor" (ie. the device on the opposite end of the link relative to the host)
    #
    #
    # plt.savefig("network_diagram.png")
    #
    # print("Script execution has finished successfully!")










