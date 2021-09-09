Network Automation Script

This script leverages the Netmiko library to poll active devices in the network via SSH. While polling, the script executes several cisco IOS command, such as _show cdp neighbors_ , to get an idea of the health of the connections between devices in the network. This polled data is then parsed, timestamped and stored to a database (currently a .txt file). From the polled data, the script also uses Networkx to draw a network diagram representative of the devices that were identified in devices.txt.  
