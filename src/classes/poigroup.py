from flask import g
from flask.ext.babel import ngettext

from .location import Location


class POIGroup(Location):
    priority = 4

    def __init__(self, graph, name, titles={}, any_titles={}):
        super().__init__(name, titles)
        self.graph = graph
        self.any_titles = any_titles
        self.pois = []

    @property
    def subtitle(self):
        return ngettext('%(num)d POI', '%(num)d POIs', num=len(self.pois))

    @property
    def title(self):
        return self.any_titles.get(g.locale, self.name)

    @property
    def collection_title(self):
        return super().title

    def __repr__(self):
        return 'POIGroup(%s)' % repr(self.name)
