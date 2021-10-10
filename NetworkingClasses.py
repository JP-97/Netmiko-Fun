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
