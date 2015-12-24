from flask.ext.babel import gettext as _

from .location import Location
from .position import Position


class UserPosition(Position, Location):
    user = True
    priority = 3

    def __init__(self, level, x, y, located=False):
        Position.__init__(self, level, x, y)
        Location.__init__(self, self.subtitle, {})
        self.located = located

    @property
    def title(self):
        room = self.room if not self.forced else self.room_before
        if room is not None:
            return (_('Your location in %(room)s', room=self.room.title) if self.located
                    else _('Custom location in %(room)s', room=self.room.title))
        return (_('Your location on level %(level)d', level=self.level) if self.located
                else _('Custom location on level %(level)d', level=self.level))

    @property
    def subtitle(self):
        return '%d:%d:%d' % (self.level, self.x, self.y)

    def __repr__(self):
        return 'UserPosition%s' % repr((self.level, self.x, self.y))
