class LocationType(type):
    def __new__(cls, name, bases, dict):
        return super().__new__(cls, name, bases, dict)

    def __gt__(cls, other_cls):
        return cls

    def __add__(cls, other_cls):
        return cls

class Slicable:
    def __getitem__(self, slice):
        raise NotImplementedError


class ContextManager:
    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, *args):
        raise NotImplementedError


class VerticalRegion(Slicable, ContextManager):
    pass


class SparseFill(Slicable, ContextManager):
    pass
