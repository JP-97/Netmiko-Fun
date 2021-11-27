from netmiko import ConnectHandler
import networkx as nx
import matplotlib.pyplot as plt
from contextlib import contextmanager
from math import sqrt
from NetworkingClasses import Link, Device
from NetworkingFunctions import load_devices, check_interconnectivity, Collate_Run, Get_Run

nodes = []  # this will hold all the nodes in the network (ie. network devices)
edges = []  # this will hold a list of tuples representing the links between each device
interfaces = {}  # this will hold all the interface details for each link
device_db = []  # this will hold all the network devices in in the network
link_db = []  # this will hold all the  data link objects in the network


if __name__ == "__main__":

    #Load in the network devices from json devices.txt
    devices = load_devices("devices.txt")

    #validate the connections in the network
    check_interconnectivity(devices, "Interconnectivity.txt")

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










