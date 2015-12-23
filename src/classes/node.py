from .position import Position


class Node(Position):
    def __init__(self, i, name, level, x, y):
        self.i = i
        self.name = name
        super().__init__(level, x, y)

    def __repr__(self):
        return 'Node%s' % repr((self.i, self.room, self.level, self.x, self.y))
