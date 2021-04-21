from dusk import util


class Annotatable:
    annotations: util.DotDict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.annotations = util.DotDict()
