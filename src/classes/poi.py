from .location import Location
from .position import Position


class POI(Position, Location):
    priority = 3

    def __init__(self, name, level, x, y, titles):
        Position.__init__(self, level, x, y)
        Location.__init__(self, name, titles)
        self.name = name

    @property
    def subtitle(self):
        return self.room.title

    def __repr__(self):
        return 'POI%s' % repr((self.name, self.room, self.level, self.x, self.y))
