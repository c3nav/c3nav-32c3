import math
from collections import OrderedDict


class Route():
    def __init__(self, graph, points, settings, avoided_ctypes=()):
        self.graph = graph
        self.points = points
        self.settings = settings.copy()
        self.avoided_ctypes = avoided_ctypes

    def describe(self, merge_descriptions=True):
        routeparts = self._into_parts()
        has_avoided_ctypes = False

        for i, part in enumerate(routeparts):
            for j, path in enumerate(part['path']):
                desc = {
                    'icon': '',
                    'text': '',
                }
                if i != 0 and j == 0:
                    desc['ignore'] = True
                path['desc'] = desc

                turning = 'straight'
                if 'direction_change' not in path:
                    pass
                elif 20 < path['direction_change'] <= 75:
                    turning = 'light_left'
                elif -75 <= path['direction_change'] < -20:
                    turning = 'light_right'
                elif 75 < path['direction_change']:
                    turning = 'left'
                elif path['direction_change'] < -75:
                    turning = 'right'

                desc['icon'] = turning
                if path['ctype'] == 'stairs':
                    desc['icon'] = 'stairs-%s' % path['level']
                elif path['ctype'] == 'elevator':
                    desc['icon'] = 'elevator-%s' % path['level']
                elif path['ctype'] == 'escalator':
                    desc['icon'] = 'escalator-%s' % path['level']
                elif path['ctype'] == 'steps':
                    desc['icon'] = 'steps-%s' % path['level']
                elif path['ctype'] == 'stairs':
                    desc['icon'] = 'stairs-%s' % path['level']

                if desc['icon'] in self.avoided_ctypes:
                    has_avoided_ctypes = True

                from_room = self.graph.rooms[path['from']['room']].titles.get('en', path['from']['room'])
                to_room = self.graph.rooms[path['to']['room']].titles.get('en', path['to']['room'])

                located = ''
                located_icon = 'straight'
                if 'direction_change' not in path:
                    pass
                elif 30 < path['direction_change']:
                    located = ' on the left'
                    located_icon = 'light_left'
                elif path['direction_change'] < -30:
                    located = ' on the right'
                    located_icon = 'light_right'

                desc['can_merge_to_next'] = False

                if path['ctype'] in ('stairs', 'steps', 'escalator', 'elevator'):
                    to_level = ''
                    if len(routeparts) > i+1 and len(part['path']) == j+1:
                        to_level = ' to <strong>level %d</strong>' % routeparts[i+1]['level']

                    if path['ctype'] == 'steps':
                        desc['can_merge_to_last'] = True
                        desc['text'] = 'Go %s the steps<strong>%s</strong>.' % (path['level'], located)
                    if path['ctype'] == 'stairs':
                        desc['text'] = 'Go %s the stairs%s<strong>%s</strong>.' % (path['level'], located, to_level)
                    elif path['ctype'] == 'escalator':
                        desc['text'] = ('Take the escalator%s %s<strong>%s</strong>.' %
                                        (located, path['level'], to_level))
                    elif path['ctype'] == 'elevator':
                        desc['text'] = ('Take the elevator%s %s<strong>%s</strong>.' %
                                        (located, path['level'], to_level))

                elif path['from']['room'] != path['to']['room']:
                    desc['icon'] = located_icon
                    if j > 0:
                        desc['text'] = 'Enter <strong>%s</strong>%s.' % (to_room, located)
                    else:
                        desc['text'] = ('Leave <strong>%s</strong> and enter <strong>%s</strong>.' %
                                        (from_room, to_room))
                    desc['can_merge_to_next'] = len(located) == 0
                    desc['can_merge_to_last'] = True

                else:
                    desc['text'] = {
                        'light_left': 'Turn light to the left and continue for %.1f meters.',
                        'light_right': 'Turn light to the right and continue for %.1f meters.',
                        'left': 'Turn left and continue for %.1f meters.',
                        'right': 'Turn right and continue for %.1f meters.'
                    }.get(turning, 'Continue for %.1f meters.') % (path['distance']/100)

        if merge_descriptions:
            self._merge_descriptions(routeparts)

        return routeparts, has_avoided_ctypes

    def _into_parts(self):
        routeparts = []
        currentpart = []
        currentlevel = None
        for point in self.points:
            currentpart.append(point)
            if point.room.level != currentlevel:
                if currentlevel is not None:
                    routeparts.append(self._convert_routepath(currentpart, currentlevel))
                currentlevel = point.room.level
                currentpart = currentpart[-2:]
        routeparts.append(self._convert_routepath(currentpart, currentlevel))

        # skip lift-only-routeparts
        for i in reversed(range(len(routeparts))):
            routepart = routeparts[i]
            path = routepart['path']
            if not [p for p in path if p['ctype'] != 'elevator']:
                newp = path[0]
                newp['duration'] += path[1]['duration']
                newp['to'] = path[1]['to']
                if i > 0:
                    routeparts[i-1]['path'][-1] = newp.copy()
                if i < len(routeparts)-1:
                    routeparts[i+1]['path'][0] = newp.copy()
                if i > 0 and i < len(routeparts)-1:
                    routeparts.pop(i)

        # skip stairs-only-routeparts
        for i in reversed(range(len(routeparts))):
            routepart = routeparts[i]
            path = routepart['path']
            if not [p for p in path if p['ctype'] != 'stairs'] and len(path) > 1:
                newp = path[0]
                newp['duration'] += path[1]['duration']
                newp['distance'] += path[1]['distance']
                newp['to'] = path[1]['to']
                if i > 0:
                    routeparts[i-1]['path'][-1] = newp.copy()
                if i < len(routeparts)-1:
                    routeparts[i+1]['path'][0] = newp.copy()
                if i > 0 and i < len(routeparts)-1:
                    routeparts.pop(i)

        return routeparts

    def _convert_routepath(self, points, level):
        from .router import Router
        routepart = OrderedDict()
        routepart['level'] = level
        routepart['path'] = []

        total_distance = 0
        total_duration = 0

        lastpoint = points[0]
        lastdirection = None
        for point in points[1:]:
            ctype, distance = self.graph.get_connection(lastpoint, point)
            line = OrderedDict()
            line['from'] = OrderedDict((('x', lastpoint.x), ('y', lastpoint.y), ('room', lastpoint.room.name)))
            line['to'] = OrderedDict((('x', point.x), ('y', point.y), ('room', point.room.name)))

            line['ctype'] = ctype
            if ctype != 'default':
                line['ctype'], line['level'] = ctype.split('-', 1)

            if ctype != 'elevator':
                direction = int(math.degrees(math.atan2(lastpoint.y-point.y, point.x-lastpoint.x))) % 360
                line['direction'] = direction
                if lastdirection is not None:
                    line['direction_change'] = ((direction-lastdirection+180)) % 360 - 180
                lastdirection = direction
            else:
                lastdirection = None

            line['distance'] = distance
            total_distance += distance

            duration = Router.get_factors_by_settings(self.settings)[ctype]*distance
            line['duration'] = duration
            total_duration += duration

            routepart['path'].append(line)
            lastpoint = point

        routepart['minx'] = min(p.x for p in points if p.level == level)-20
        routepart['maxx'] = max(p.x for p in points if p.level == level)+20
        routepart['miny'] = min(p.y for p in points if p.level == level)-20
        routepart['maxy'] = max(p.y for p in points if p.level == level)+20

        routepart['distance'] = total_distance
        routepart['duration'] = total_duration

        width = routepart['maxx']-routepart['minx']
        if width < 150:
            routepart['minx'] -= math.floor((150-width)/2)
            routepart['maxx'] += math.ceil((150-width)/2)

        height = routepart['maxy']-routepart['miny']
        if height < 150:
            routepart['miny'] -= math.floor((150-height)/2)
            routepart['maxy'] += math.ceil((150-height)/2)

        return routepart

    def _merge_descriptions(self, routeparts):
        for i, part in enumerate(routeparts):
            paths = part['path'].copy()
            newpaths = []
            while paths:
                p = paths.pop(0)
                if paths and paths[0]['desc'].get('can_merge_to_last'):
                    p2 = paths.pop(0)
                    p['desc']['text'] = p['desc']['text']+'<br />'+p2['desc']['text']
                    p2['desc']['merged_to_last'] = True
                    if 'can_merge_to_next' in p2['desc']:
                        p2['desc'].pop('can_merge_to_next')
                    newpaths.append(p)
                    newpaths.append(p2)
                elif p['desc'].get('can_merge_to_next') and paths:
                    p['desc']['merged_to_next'] = True
                    p2 = paths.pop(0)
                    p2['desc']['text'] = p['desc']['text']+'<br />'+p2['desc']['text']
                    newpaths.append(p)
                    newpaths.append(p2)
                else:
                    newpaths.append(p)
            part['path'] = newpaths
