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


def sum_over(*args, **kwargs) -> Any:
    raise NotImplementedError
