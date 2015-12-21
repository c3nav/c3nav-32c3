from flask import g


class Location:
    """ has nodes and a title """
    def __init__(self, name, titles):
        self.name = name
        self.titles = titles

    @property
    def title(self):
        return self.titles.get(g.locale, self.name)
