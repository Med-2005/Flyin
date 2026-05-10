class Zone:
    def __init__(self, name, x, y, zone_type, max_drones, color):
        self.name = name
        self.x = x
        self.y = y
        self.type = zone_type
        self.max_drones = max_drones
        self.color = color


class Connection:
    def __init__(self, zone1, zone2, max_link_capacity):
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = max_link_capacity


class Drone:
    def __init__(self, ID, curr_location, nex_dest, mov_state):
        self.ID = ID
        self.curr_loc = curr_location
        self.nex_dest = nex_dest
        self.mov_state = mov_state
