import numpy as np
from matplotlib.path import Path

from .location import Location


class Room(Location):
    priority = 2

    def __init__(self, graph, name, level, titles, shape):
        super().__init__(name, titles)
        self.graph = graph
        self.level = level
        self.shape = shape
        self.nodes = []
        self.pois = []
        self.barriers = []
        self.groups = []

        mpl_xy = self.shape+self.shape[-1:]
        mpl_codes = [Path.MOVETO] + [Path.LINETO]*len(self.shape)
        self.mpl_path = Path(np.array(mpl_xy), codes=mpl_codes)

    @property
    def priority(self):
        return 1 if self.groups else 2

    def contains_position(self, position):
        if position.level != self.level:
            return False

        return self.mpl_path.contains_point((position.x, position.y))

    def get_barriers(self):
        return (b for b in self.graph.barriers
                if b.level == self.level and self.mpl_path.intersects_path(b.mpl_path, True))

    def barrier_paths(self):
        return [self.mpl_path] + [b.mpl_path for b in self.barriers]

    @property
    def subtitle(self):
        return 'Room, Level %d' % self.level

    def __repr__(self):
        return 'Room(%s)' % repr(self.name)
