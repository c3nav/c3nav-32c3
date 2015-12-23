import math
from collections import OrderedDict

from flask import escape
from flask.ext.babel import gettext as _


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
                from_room = '<strong>'+self.graph.rooms[path['from']['room']].title+'</strong>'
                to_room = '<strong>'+self.graph.rooms[path['to']['room']].title+'</strong>'

                desc = {
                    'icon': '',
                    'text': '',
                }
                if j == 0:
                    part['desc'] = _('You are now in %(room)s on %(level)s.',
                                     room=from_room if i == 0 else to_room,
                                     level='<strong>'+_('level %(level)d', level=part['level'])+'</strong>'
                                     ).replace('&lt;strong&gt;', '<strong>').replace('&lt;/strong&gt;', '</strong>')

                if i != 0 and j == 0:
                    desc['ignore'] = True
                path['desc'] = desc

                turning = 'straight'
                direction_change = path.get('direction_change', 0)
                if 20 < direction_change <= 75:
                    turning = 'light_left'
                elif -75 <= direction_change < -20:
                    turning = 'light_right'
                elif 75 < direction_change:
                    turning = 'left'
                elif direction_change < -75:
                    turning = 'right'

                level = path.get('level', '')
                desc['icon'] = turning if path['ctype'] == 'default' else (path['ctype']+'-'+str(level))

                if desc['icon'] in self.avoided_ctypes:
                    has_avoided_ctypes = True

                located = ''
                located_icon = 'straight'
                if 30 < direction_change:
                    located = _(' on the left')
                    located_icon = 'light_left'
                elif direction_change < -30:
                    located = _(' on the right')
                    located_icon = 'light_right'

                desc['can_merge_to_next'] = False

                if path['ctype'] in ('stairs', 'steps', 'escalator', 'elevator'):
                    args = {'located': '', 'to_level': ''}
                    if len(routeparts) > i+1 and len(part['path']) == j+1:
                        level = '<strong>'+_('level %(level)d', level=routeparts[i+1]['level'])+'</strong>'
                        args['to_level'] = _(' to %(level)s', level=level)

                    if path['ctype'] == 'steps':
                        desc['can_merge_to_last'] = True

                    desc['text'] = {
                        'steps-up': _('Go up the steps%(located)s.', **args),
                        'steps-down': _('Go down the steps%(located)s.', **args),
                        'stairs-up': _('Go up the stairs%(located)s%(to_level)s.', **args),
                        'stairs-down': _('Go down the stairs%(located)s%(to_level)s.', **args),
                        'escalator-up': _('Take the escalator%(located)s up%(to_level)s.', **args),
                        'escalator-down': _('Take the escalator%(located)s down%(to_level)s.', **args),
                        'elevator-up': _('Take the elevator%(located)s up%(to_level)s.', **args),
                        'elevator-down': _('Take the elevator%(located)s down%(to_level)s.', **args)
                    }.get(desc['icon'])

                elif path['from']['room'] != path['to']['room']:
                    desc['icon'] = located_icon
                    if j > 0:
                        desc['text'] = _('Enter %(room)s%(located)s.',
                                         room='<strong>'+to_room+'</strong>', located=located)
                    else:
                        desc['text'] = _('Leave %(from_room)s and enter %(to_room)s.',
                                         from_room=from_room, to_room=to_room)
                    desc['can_merge_to_next'] = len(located) == 0
                    desc['can_merge_to_last'] = True

                else:
                    d = path['distance']/100
                    desc['text'] = {
                        'light_left': _('Turn light to the left and continue for %(d).1f meters.', d=d),
                        'light_right': _('Turn light to the right and continue for %(d).1f meters.', d=d),
                        'left': _('Turn left and continue for %(d).1f meters.', d=d),
                        'right': _('Turn right and continue for %(d).1f meters.', d=d)
                    }.get(turning, _('Continue for %(d).1f meters.', d=d))

                desc['text'] = str(escape(desc['text'])).replace(
                    '&lt;strong&gt;', '<strong>'
                ).replace(
                    '&lt;/strong&gt;', '</strong>'
                )

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
