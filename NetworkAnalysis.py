from netmiko import ConnectHandler
from datetime import datetime, date
import json
import networkx as nx
import sys
import matplotlib.pyplot as plt
from contextlib import contextmanager
import os
from math import sqrt

#this class will model the data links interconnecting devices
class Link:

    def __init__(self, hostname, neigbor, local_int, neighbor_int):
        self.hostname = hostname
        self.neigbor = neigbor
        self.local_int = local_int
        self.neighbor_int = neighbor_int

    def get_edge(self):
        return (self.hostname, self.neigbor)

#this class will model network devices
class Device:

    def __init__(self, hostname, neighbors, IP):
        self.hostname = hostname
        self.neighbors = neighbors
        self.IP = IP

    def print_neighbors(self):
        for neighbor in self.neighbors:
            print(neighbor)

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

#This is the main body of the code to be executed
if __name__ == "__main__":

    nodes = [] #this will hold all the nodes in the network (ie. network devices)
    edges = [] #this will hold a list of tuples representing the links between each device
    interfaces = {} #this will hold all the interface details for each link
    device_db =  [] #this will hold all the network devices in in the network
    link_db = [] #this will hold all the  data link objects in the network

    devices = Load_Devices("devices.txt") #this will hold a dict that contains the network device info for netmiko
    Interconnectivity(devices, "Interconnectivity.txt")

    try:
        Collate_Run(devices)

    except:
        print('cant pull running configurations within the same minute. Please re-execute 1 minute after the most recent collation')

    #### CREATING THE GRAPH ####

    for device in devices:
        net_connect = ConnectHandler(**device) #represents the ssh instance to the device
        running_config = Get_Run(device)

        #parse out device hostname
        hostname = running_config.split("hostname ")
        hostname = hostname[1].split('\n')
        hostname = hostname[0]

        #fetch CDP neighbors to build edges
        cdp_device = net_connect.send_command('show cdp neighbors', use_textfsm = True)

        #populate database for all nodes in the network
        if hostname not in nodes: #here the list of nodes is acting as a running list of active devices known to the script
            nodes.append(hostname)
            device_db.append(Device(hostname, cdp_device, device["host"])) #create a unique Device object for each new device discovered in the network

    #iterate through all the possible edge combinations and build a database of unique edges
    for device in device_db:
        for neighbor in device.neighbors: #show cdp neighbors returns an array of the neighboring devices, so you need to iterate
            neighbor_device = neighbor['neighbor'].split(".")[0]
            if ((device.hostname,neighbor_device) and (neighbor_device, device.hostname) not in edges): ###currently using edges to keep track of known links in the network, need to come up with a better way
                edges.append((device.hostname,neighbor_device))
                link_db.append(Link(device.hostname, neighbor_device, neighbor['local_interface'], neighbor['neighbor_interface']))

    #Debug
    for link in link_db:
        print(link.hostname + ", " + link.neigbor)

    ###Creating network diagram
    plt.figure(1,figsize = (12,12))
    G = nx.Graph()

    #Graph objects
    G.add_nodes_from(nodes) #this creates a node based on each of the nodes in list(nodes)
    G.add_edges_from(edges) #this creates an edge based on each of the edges in list(tuple(edge))
    pos = nx.spring_layout(G)

    nx.draw_networkx(G, pos, node_size = 1000, font_size = 8)

    for edge in edges:
        for link in link_db:
            if(edge[0] == link.hostname and edge[1] == link.neigbor): #this will allow us to know which link we're updating the labels for
                print(edge)
                print(link.local_int)
                print(link.neighbor_int)
                nx.draw_networkx_edge_labels(G, pos, edge_labels = {edge:link.local_int} , label_pos = 0.7) #this will create the label for the "host" (ie. the device that executed the cdp call)
                nx.draw_networkx_edge_labels(G, pos, edge_labels = {edge:link.neighbor_int}, label_pos = 0.3) #this will create the lable for the "neighbor" (ie. the device on the opposite end of the link relative to the host)


    plt.savefig("network_diagram.png")

    print("Script execution has finished successfully!")










