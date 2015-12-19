class Location:
    """ has nodes and a title """
    def __init__(self, name, titles):
        self.name = name
        self.titles = titles

    @property
    def title(self):
        return self.titles.get('en', self.name)
