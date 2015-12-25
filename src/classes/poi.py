from flask.ext.babel import gettext as _

from .location import Location
from .position import Position


class POI(Position, Location):
    priority = 5

    def __init__(self, name, level, x, y, titles):
        Position.__init__(self, level, x, y)
        Location.__init__(self, name, titles)
        self.name = name
        self.groups = []

    @property
    def subtitle(self):
        if not self.groups:
            return _('%(room)s', room=self.room.title)
        else:
            return _('%(poigroup)s, %(room)s', poigroup=self.groups[0].collection_title, room=self.room.title)

    def __repr__(self):
        return 'POI%s' % repr((self.name, self.room, self.level, self.x, self.y))
