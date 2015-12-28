from flask import g


class Location:
    ltype = 'location'

    """ has nodes and a title """
    def __init__(self, name, titles):
        self.name = name
        self.titles = titles

    @property
    def title(self):
        return self.titles.get(g.locale, self.name)

    @property
    def single_title(self):
        return self.title
