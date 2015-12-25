from flask.ext.babel import gettext as _

from .location import Location


class SuperRoom(Location):
    priority = 2

    def __init__(self, graph, name, titles={}):
        self.graph = graph
        super().__init__(name, titles)
        self.rooms = []

    @property
    def subtitle(self):
        levels = [room.level for room in self.rooms]
        return _('Room, Level %(min)d-%(max)d', min=min(levels), max=max(levels))

    @property
    def nodes(self):
        return sum((r.nodes for r in self.rooms), [])

    def __repr__(self):
        return 'SuperRoom(%s)' % repr(self.name)
