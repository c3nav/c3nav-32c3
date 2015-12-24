from .location import Location
from .position import Position


class UserPosition(Position, Location):
    user = True
    priority = 3

    def __init__(self, level, x, y):
        Position.__init__(self, level, x, y)
        Location.__init__(self, self.subtitle, {})

    @property
    def title(self):
        room = self.room if not self.forced else self.room_before
        if room is not None:
            return 'Custom location in %s' % self.room.title
        return 'Custom location on level %d' % self.level

    @property
    def subtitle(self):
        return '%d:%d:%d' % (self.level, self.x, self.y)

    def __repr__(self):
        return 'UserPosition%s' % repr((self.level, self.x, self.y))
