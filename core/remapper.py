class Remapper:

    def __init__(self, layout):
        self.layout = layout

    def transform(self, key):

        if key in self.layout:
            return self.layout[key]

        return key