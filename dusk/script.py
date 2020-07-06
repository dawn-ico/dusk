from typing import TypeVar, Generic, Any, Callable


# TODO: implement mocks to help potential linters/static analysis


def stencil(stencil: Callable) -> Callable:
    return stencil


T = TypeVar("T")


class Field(Generic[T]):
    pass


class Edge:
    pass


class Cell:
    pass


class Vertex:
    pass


__LOCATION_TYPES__ = {Edge, Cell, Vertex}


class LoopOrder:
    def __getitem__(self, slice):
        raise NotImplementedError


forward = LoopOrder()
backward = LoopOrder()


class Neighbors:
    def __getitem__(self, slice):
        raise NotImplementedError


neighbors = Neighbors()


def reduce(*args, **kwargs) -> Any:
    raise NotImplementedError


def max(a: float, b: float) -> float:
    raise NotImplementedError


def min(a: float, b: float) -> float:
    raise NotImplementedError


def pow(base: float, exp: float) -> float:
    raise NotImplementedError


def sqrt(arg: float) -> float:
    raise NotImplementedError


def exp(exp: float) -> float:
    raise NotImplementedError


def log(arg: float) -> float:
    raise NotImplementedError


def sin(arg: float) -> float:
    raise NotImplementedError


def cos(arg: float) -> float:
    raise NotImplementedError


def tan(arg: float) -> float:
    raise NotImplementedError


def arcsin(arg: float) -> float:
    raise NotImplementedError


def arccos(arg: float) -> float:
    raise NotImplementedError


def arctan(arg: float) -> float:
    raise NotImplementedError


def fabs(arg: float) -> float:
    raise NotImplementedError


def floor(arg: float) -> float:
    raise NotImplementedError


def ceil(arg: float) -> float:
    raise NotImplementedError


def isinf(arg: float) -> float:
    raise NotImplementedError


def isnan(arg: float) -> float:
    raise NotImplementedError


__UNARY_MATH_FUNCTIONS__ = {
    sqrt,
    exp,
    log,
    sin,
    cos,
    tan,
    arcsin,
    arccos,
    arctan,
    fabs,
    floor,
    ceil,
    isinf,
    isnan,
}

__BINARY_MATH_FUNCTIONS__ = {
    max,
    min,
    pow,
}

