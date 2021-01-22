import typing

import dusk.integration as integration

from dusk.script import internal

from dusk.script.math import *
from dusk.script.math import __all__ as __math_all__

__all__ = [
    "stencil",
    "Global",
    "Edge",
    "Cell",
    "Vertex",
    "Origin",
    "K",
    "Field",
    "IndexField",
    "domain",
    "HorizontalDomains",
    "sparse",
    "reduce_over",
    "mul",
    "sum_over",
    "min_over",
    "max_over",
] + __math_all__


def stencil(stencil: typing.Callable) -> typing.Callable:
    integration.stencil_collection.append(integration.StencilObject(stencil))
    return stencil


class Global:
    name: str

    def __init__(self, name: str):
        self.name = name


class Edge(metaclass=internal.LocationType):
    pass


class Cell(metaclass=internal.LocationType):
    pass


class Vertex(metaclass=internal.LocationType):
    pass


class Origin(metaclass=internal.LocationType):
    pass


class K:
    pass


class Field:
    @classmethod
    def __class_getitem__(cls, *args) -> type:
        pass


class IndexField:
    @classmethod
    def __class_getitem__(cls, *args) -> type:
        pass


domain = internal.Domain()


def HorizontalDomains(*markers) -> typing.Iterable:
    return map(internal.HorizontalMarker, markers)


sparse = internal.SparseFill()


def reduce_over(
    location_chain: type,
    expr: float,
    op: typing.Callable,
    /,
    *,
    init=None,
    weights=None,
) -> float:
    raise NotImplementedError


def sum_over(location_chain: type, expr: float, /, *, init=None, weights=None) -> float:
    raise NotImplementedError


# for reductions with a multiplication operator
def mul(x: float, y: float) -> float:
    raise NotImplementedError


def min_over(location_chain: type, expr: float, /, *, init=None, weights=None) -> float:
    raise NotImplementedError


def max_over(location_chain: type, expr: float, /, *, init=None, weights=None) -> float:
    raise NotImplementedError
