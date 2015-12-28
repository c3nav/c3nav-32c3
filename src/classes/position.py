import numpy as np


class Position:
    ltype = 'position'

    def __init__(self, level, x, y):
        self.level = level
        self.x = x
        self.y = y
        self.xy = np.array((x, y))
        self.room = None
        self.forced = False

    def __repr__(self):
        return 'Position%s' % repr((self.room, self.level, self.x, self.y))
