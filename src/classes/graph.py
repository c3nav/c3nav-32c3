import numpy as np
from matplotlib.path import Path

from .barrier import Barrier
from .node import Node
from .poi import POI
from .room import Room
from .roomgroup import RoomGroup
from .superroom import SuperRoom
from .wifilocator import WifiLocator


class Graph():
    connection_types = ('default', 'steps-up', 'steps-down', 'stairs-up', 'stairs-down',
                        'escalator-up', 'escalator-down', 'elevator-up', 'elevator-down')
    diag = 2**0.5

    def __init__(self, data, room_positions=True, auto_connect=False, load_wifi=False):
        self.data = data
        self.did_room_positions = False
        self.did_room_barriers = False
        self.did_auto_connect = False

        # load basic data
        self.name = data['name']
        self.levels = data['levels']
        self.width = data['width']
        self.height = data['height']
        self.cm_per_px = data['cm_per_px']
        self.titles = data['titles']
        self.overwrite_default_settings = data['overwrite_default_settings']

        if load_wifi:
            self.wifi = WifiLocator(self, data['wifidata'])

        # load rooms
        self.rooms = {}
        self.superrooms = {}
        self.roomgroups = {}
        for name, rdata in data['rooms'].items():
            shape = [[int(i) for i in p.split(',')] for p in rdata['shape'].split(' ')]
            room = Room(self, name, rdata['level'], data['titles'].get(name, {}), shape)

            superroom_name = rdata.get('superroom')
            if superroom_name:
                superroom = self.superrooms.get(superroom_name)
                if superroom is None:
                    superroom = SuperRoom(self, superroom_name, data['titles'].get(superroom_name, {}))
                    self.superrooms[superroom_name] = superroom
                superroom.rooms.append(room)
                room.superroom = superroom

            for groupname in rdata.get('groups', ()):
                roomgroup = self.roomgroups.get(groupname)
                if roomgroup is None:
                    roomgroup = RoomGroup(self, groupname, data['titles'].get(groupname, {}))
                    self.roomgroups[groupname] = roomgroup
                roomgroup.rooms.append(room)
                room.groups.append(roomgroup)

            self.rooms[name] = room

        # load nodes
        self.nodes = tuple(Node(i, n, p['level'], p['x'], p['y'])
                           for i, (n, p) in enumerate(data['nodes'].items()))
        self.nodes_by_name = {p.name: p.i for p in self.nodes}

        # load POIs
        self.pois = {n: POI(n, p['level'], p['x'], p['y'], data['titles'].get(n, {}))
                     for n, p in data['pois'].items()}

        # create distance matrices, one for every connection type
        self.matrices = {ctype: np.zeros((len(self.nodes), len(self.nodes)))
                         for ctype in self.connection_types}
        for c in data['connections']:
            p0 = self.nodes[self.nodes_by_name[c['node0']]]
            p1 = self.nodes[self.nodes_by_name[c['node1']]]
            directed = c.get('directed', False)
            ctype = c.get('ctype', 'default')
            l0, l1 = ('down', 'up') if p0.level > p1.level else ('up', 'down')
            distance = np.linalg.norm(p0.xy-p1.xy)*self.cm_per_px
            if ctype == 'default':
                self.matrices['default'][p0.i, p1.i] = distance
                if not directed:
                    self.matrices['default'][p1.i, p0.i] = distance
            elif ctype == 'steps':
                self.matrices['steps-'+l0][p0.i, p1.i] = distance
                if not directed:
                    self.matrices['steps-'+l1][p1.i, p0.i] = distance
            elif ctype == 'stairs':
                self.matrices['stairs-'+l0][p0.i, p1.i] = distance * self.diag
                if not directed:
                    self.matrices['stairs-'+l1][p1.i, p0.i] = distance * self.diag
            elif ctype == 'escalator':
                self.matrices['escalator-'+l0][p0.i, p1.i] = distance * self.diag
                if not directed:
                    self.matrices['escalator-'+l1][p1.i, p0.i] = distance * self.diag
            elif ctype == 'elevator':
                self.matrices['elevator-'+l0][p0.i, p1.i] = 1
                if not directed:
                    self.matrices['elevator-'+l1][p1.i, p0.i] = 1

        # load barriers
        self.barriers = []
        for bdata in data['barriers']:
            self.barriers.append(Barrier(bdata['level'], bdata['x1'], bdata['y1'], bdata['x2'], bdata['y2']))

        # selectable locations
        self.selectable_locations = {}
        self.selectable_locations.update(self.rooms)
        self.selectable_locations.update(self.superrooms)
        self.selectable_locations.update(self.roomgroups)
        self.selectable_locations.update(self.pois)

        if room_positions:
            self.room_positions()
        if auto_connect:
            self.auto_connect()

    def room_positions(self):
        self.did_room_positions = True
        for node, room in ((node, self.get_room(node)) for node in self.nodes):
            if room is not None:
                node.room = room
                room.nodes.append(node)

        for poi, room in ((poi, self.get_room(poi)) for poi in self.pois.values()):
            if room is not None:
                poi.room = room
                room.pois.append(poi)

    def get_room(self, location):
        for room in (r for r in self.rooms.values() if r.level == location.level):
            if room.contains_position(location):
                return room
        return None

    def room_barriers(self):
        self.did_room_barriers = True
        for barrier in self.barriers:
            for room in (r for r in self.rooms.values() if r.level == barrier.level):
                if room.mpl_path.intersects_path(barrier.mpl_path, True):
                    barrier.rooms.append(room)
                    room.barriers.append(barrier)

    def auto_connect(self):
        if not self.did_room_positions:
            self.room_positions()
        if not self.did_room_barriers:
            self.room_barriers()

        self.did_auto_connect = True
        for name, room in self.rooms.items():
            paths = room.barrier_paths()
            for i, p0 in enumerate(room.nodes):
                for p1 in room.nodes[i+1:]:
                    for path in paths:
                        if path.intersects_path(Path(np.vstack((p0.xy, p1.xy))), False):
                            break
                    else:
                        distance = np.linalg.norm(p0.xy-p1.xy)*self.cm_per_px
                        self.matrices['default'][p0.i, p1.i] = distance
                        self.matrices['default'][p1.i, p0.i] = distance

        for name, poi in self.pois.items():
            self.connect_position(poi)

    def connect_position(self, position):
        if not self.did_room_positions:
            self.room_positions()
        if position.room is None:
            position.room = self.get_room(position)

        position.nodes = []
        position.node_distances = {}
        paths = position.room.barrier_paths()
        for p in position.room.nodes:
            for path in paths:
                if path.intersects_path(Path(np.vstack((position.xy, p.xy))), False):
                    break
            else:
                position.nodes.append(p)
                distance = np.linalg.norm(position.xy-p.xy)*self.cm_per_px
                position.node_distances[p.i] = distance

    def can_connect_positions(self, p0, p1):
        if p0.room != p1.room:
            return False
        paths = p0.room.barrier_paths()
        for path in paths:
            if path.intersects_path(Path(np.vstack((p0.xy, p1.xy))), False):
                return False
        return True

    def get_connection(self, p0, p1):
        if not isinstance(p0, Node) or not isinstance(p1, Node):
            return 'default', np.linalg.norm(p0.xy-p1.xy)*self.cm_per_px
        p0 = p0.i
        p1 = p1.i
        for ctype, matrix in self.matrices.items():
            distance = matrix[p0, p1]
            if distance:
                return ctype, distance
        return None, None

    def get_by_levels(self):
        levels = {i: {'nodes': [], 'pois': [], 'barriers': [], 'connections': []} for i in self.levels}

        for node in self.nodes:
            levels[node.level]['nodes'].append(node)

        for poi in self.pois.values():
            levels[poi.level]['pois'].append(poi)

        for c in self.data['connections']:
            p0 = self.nodes[self.nodes_by_name[c['node0']]]
            p1 = self.nodes[self.nodes_by_name[c['node1']]]
            for level in set((p0.level, p1.level)):
                levels[level]['connections'].append({
                    'p0': p0,
                    'p1': p1,
                    'ctype': c.get('ctype', 'default'),
                    'directed': c.get('directed', False)
                })

        for i in self.levels:
            levels[i]['rooms'] = [room for room in self.rooms.values() if room.level == i]
            levels[i]['barriers'] = [b for b in self.barriers if b.level == i]
        return levels

    name_chars = 'abcdefghijklmnopqrstuvwxyz0123456789-'
    url_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~'

    def _data_to_path(self, data):
        result = ''
        while data:
            result += self.url_chars[data % len(self.url_chars)]
            data = int(data/len(self.url_chars))
        return result[::-1]

    def location_to_data(self, location, mode='o'):
        if mode not in ('o', 'd'):
            raise ValueError

        data = self.levels.index(int(location.level))
        data = data*self.width + int(location.x)
        data = data*self.height + int(location.y)
        data = data*4 + (mode == 'd')*2 + 0
        return self._data_to_path(data)

    def name_to_data(self, name, mode='o'):
        if mode not in ('o', 'd') or name not in self.selectable_locations:
            raise ValueError

        data = 0
        for c in name:
            data = data*len(self.name_chars) + self.name_chars.index(c)
        data = data*4 + (mode == 'd')*2 + 1
        return self._data_to_path(data)
