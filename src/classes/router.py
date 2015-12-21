import json
from collections import deque
from datetime import datetime
from functools import lru_cache

import numpy as np
from flask.ext.babel import gettext as _
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

from .position import Position
from .route import Route


class Router():
    default_settings = {
        'steps': 'yes',
        'stairs': 'yes',
        'escalators': 'yes',
        'elevators': 'yes',
        'route': 'fast',
        'e': (),
        'i': (),
        's-default': 160,
        's-elevator': 20,
        's-stairs-up': 130,
        's-stairs-down': 160,
        's-escalator-up': 160,
        's-escalator-down': 160,
    }

    def __init__(self, graph, settings={}):
        self.graph = graph
        self.settings = self.default_settings.copy()
        self.settings.update(graph.overwrite_default_settings)
        self.update_settings(settings)

    def update_settings(self, settings):
        for name in ('steps', 'stairs', 'escalators', 'elevators'):
            if settings.get(name) in ('yes', 'up', 'down', 'no'):
                self.settings[name] = settings[name]

        if settings.get('elevator', '').isdigit() and int(settings.get('elevator')) in range(0, 900):
            self.settings['elevator'] = int(settings.get('elevator'))

        for name in ('s-walking', 's-stairs-up', 's-stairs-down', 's-escalator-up', 's-escalator-down'):
            if name not in settings or not str(settings[name]).isdigit():
                continue

            if int(settings[name]) in range(1, 30000):
                self.settings[name] = int(settings[name])

        if settings.get('route') in ('fast', 'short'):
            self.settings['route'] = settings['route']

        if 'e' in settings:
            self.settings['e'] = set(e for e in tuple(self.settings['e'])+tuple(settings['e'])
                                     if e in self.graph.selectable_locations)

        if 'i' in settings:
            self.settings['e'] = set(self.settings['e']) - set(settings['i'])
            self.settings['i'] = set(i for i in tuple(self.settings['i'])+tuple(settings['i'])
                                     if i in self.graph.selectable_locations)

        self.settings['e'] = tuple(self.settings['e'])
        self.settings['i'] = tuple(self.settings['i'])

    def create_routing_table(self):
        self.excluded_nodes, g_dense = Router.create_dense_matrix(self.graph, tuple(self.settings.items()))
        self.shortest_paths, self.predecessors = Router.shortest_path(g_dense.tostring(), g_dense.shape)

    @classmethod
    def get_factors_by_settings(cls, settings):
        return {
            'default': 1/settings['s-default'],
            'steps-up': 1/settings['s-default'],
            'steps-down': 1/settings['s-default'],
            'stairs-up': 1/settings['s-stairs-up'],
            'stairs-down': 1/settings['s-stairs-down'],
            'escalator-up': 1/settings['s-escalator-up'],
            'escalator-down': 1/settings['s-escalator-down'],
            'elevator-up': settings['s-elevator'],
            'elevator-down': settings['s-elevator']
        }

    @classmethod
    @lru_cache(maxsize=128)
    def create_dense_matrix(cls, graph, settings):
        # First, we select all routing matrices of the allowed connection types,
        # multiply them with their speed and combine them
        settings = dict(settings)
        g_dense = np.zeros(graph.matrices['default'].shape)

        factors = {}
        if settings['route'] == 'fast':
            factors = cls.get_factors_by_settings(settings)
        else:
            factors = {
                'default': 1, 'steps-up': 1, 'steps-down': 1, 'stairs-up': 1, 'stairs-down': 1, 'escalator-up': 1,
                'escalator-down': 1, 'elevator-up': 1, 'elevator-down': 1
            }

        if settings['steps'] not in ('yes', 'up'):
            factors['steps-up'] *= 10000000

        if settings['steps'] not in ('yes', 'down'):
            factors['steps-down'] *= 10000000

        if settings['stairs'] not in ('yes', 'up'):
            factors['stairs-up'] *= 10000000

        if settings['stairs'] not in ('yes', 'down'):
            factors['stairs-down'] *= 10000000

        if settings['escalators'] not in ('yes', 'up'):
            factors['escalator-up'] *= 10000000

        if settings['escalators'] not in ('yes', 'down'):
            factors['escalator-down'] *= 10000000

        if settings['elevators'] not in ('yes', 'up'):
            factors['elevator-up'] *= 10000000

        if settings['elevators'] not in ('yes', 'down'):
            factors['elevator-down'] *= 10000000

        for name, factor in factors.items():
            g_dense += graph.matrices[name]*factor

        # Its time to find out which nodes exactly were excluded from routing
        excluded = set(sum(([p.i for p in graph.selectable_locations[e].nodes]
                            for e in settings['e']), []))

        # And now lets exclude the nodes from exclusion that were explicitely included
        excluded -= set(sum(([p.i for p in graph.selectable_locations[i].nodes]
                            for i in settings['i']), []))

        # We know now what should be excluded, so let's make this connection almost impossible
        ex = tuple(excluded)
        g_dense[ex, :] *= 10000000
        g_dense[:, ex] *= 10000000

        return excluded, g_dense

    @classmethod
    @lru_cache(maxsize=128)
    def shortest_path(cls, data, shape):
        # let scipy do it's magic and calculate all shortest paths in the remaining graph
        g_sparse = csr_matrix(np.ma.masked_values(np.fromstring(data).reshape(shape), 0))
        return shortest_path(g_sparse, return_predecessors=True)

    def avoided_ctypes(self):
        avoided_ctypes = set()
        if self.settings['steps'] not in ('yes', 'up'):
            avoided_ctypes.add('steps-up')
        if self.settings['steps'] not in ('yes', 'down'):
            avoided_ctypes.add('steps-down')
        if self.settings['stairs'] not in ('yes', 'up'):
            avoided_ctypes.add('stairs-up')
        if self.settings['stairs'] not in ('yes', 'down'):
            avoided_ctypes.add('stairs-down')
        if self.settings['escalators'] not in ('yes', 'up'):
            avoided_ctypes.add('escalator-up')
        if self.settings['escalators'] not in ('yes', 'down'):
            avoided_ctypes.add('escalator-down')
        if self.settings['elevators'] not in ('yes', 'up'):
            avoided_ctypes.add('elevator-up')
        if self.settings['elevators'] not in ('yes', 'down'):
            avoided_ctypes.add('elevator-down')

        return avoided_ctypes

    def get_route(self, origin, destination):
        print(datetime.now(), origin, destination, json.dumps(self.settings))
        messages = []

        if isinstance(origin, Position) and not hasattr(origin, 'nodes'):
            self.graph.connect_position(origin)

        if isinstance(destination, Position) and not hasattr(destination, 'nodes'):
            self.graph.connect_position(destination)

        origin_nodes = set(p.i for p in origin.nodes)
        destination_nodes = set(p.i for p in destination.nodes)

        self.create_routing_table()

        if not (origin_nodes - self.excluded_nodes):
            messages.append(('warn', _('This route contains locations that you wanted to avoid '
                                       'because your origin has no point outside of them.')))

        if not (destination_nodes - self.excluded_nodes):
            messages.append(('warn', _('This route contains locations that you wanted to avoid '
                                       'because your destination has no point outside of them.')))

        if origin_nodes & destination_nodes:
            if ((not isinstance(origin, Position) and not isinstance(destination, Position)) or
                    (origin.level == destination.level and origin.x == destination.x and origin.y == destination.y)):
                messages.append(('success', _('Congratulations – you are already there!')))
                return messages, None

            if self.graph.can_connect_positions(origin, destination):
                return messages, Route(self.graph, [origin, destination], self.settings, [])

            via = None
            via_dist = float('inf')
            for i in (origin_nodes & destination_nodes):
                distance = (self.graph.get_connection(origin, self.graph.nodes[i])[1] +
                            self.graph.get_connection(origin, self.graph.nodes[i])[1])
                if distance < via_dist:
                    via = i
                    via_dist = distance

            return messages, Route(self.graph, [origin, self.graph.nodes[via], destination], self.settings, [])

        # Remove all routes that dont have the correct origin or destination
        # If we have free placed points, add the delay to their nodes
        possible_routes = self.shortest_paths.copy()
        wayfactor = (1/self.settings['s-default']) if self.settings['route'] == 'fast' else 1
        for i in range(len(self.graph.nodes)):
            if i not in origin_nodes:
                possible_routes[i, :] = np.inf
            elif isinstance(origin, Position):
                possible_routes[i, :] += origin.node_distances[i]*wayfactor

            if i not in destination_nodes:
                possible_routes[:, i] = np.inf
            elif isinstance(destination, Position):
                possible_routes[i, :] += destination.node_distances[i]*wayfactor

        # We may still have multiple routes if we had multiple origin or destination nodes
        # So let's pick the best route
        best_route = tuple(np.transpose(np.where(possible_routes == possible_routes.min()))[0])

        # Collect all route nodes
        firstnode, prevnode = best_route
        route = deque()
        while prevnode >= 0:
            route.appendleft(prevnode)
            prevnode = self.predecessors[firstnode, prevnode]

        if (set(route) - origin_nodes - destination_nodes) & self.excluded_nodes:
            messages.append(('warn', _('This route contains locations that you wanted to avoid '
                                       'because otherwise no route would be possible.')))

        positions = [self.graph.nodes[i] for i in route]

        if isinstance(origin, Position):
            positions.insert(0, origin)

        if isinstance(destination, Position):
            positions.append(destination)

        avoided_ctypes = self.avoided_ctypes()

        return messages, Route(self.graph, positions, self.settings, avoided_ctypes)
