from .location import Location


class RoomGroup(Location):
    priority = 10

    def __init__(self, graph, name, titles={}):
        super().__init__(name, titles)
        self.graph = graph
        self.rooms = []

    @property
    def subtitle(self):
        return '%d rooms' % (len(self.rooms))

    @property
    def nodes(self):
        return sum((r.nodes for r in self.rooms), [])

    def __repr__(self):
        return 'RoomGroup(%s)' % repr(self.name)
