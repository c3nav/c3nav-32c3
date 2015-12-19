from matplotlib.path import Path


class Barrier():
    def __init__(self, level, x1, y1, x2, y2):
        self.level = level
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.rooms = []

        mpl_xy = [[x1, y1], [x2, y2]]
        mpl_codes = [Path.MOVETO, Path.LINETO]
        self.mpl_path = Path(mpl_xy, codes=mpl_codes)
