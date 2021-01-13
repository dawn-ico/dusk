from __future__ import annotations
import typing as t


import enum
import dataclasses

from dusk.errors import SemanticError


class CompileTimeConstant:
    # Marker that the class is a compile time constant
    pass


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


# TODO: put these classes in appropriate places


@enum.unique
class VerticalIterationDirection(enum.Enum):
    UPWARD = enum.auto()
    DOWNWARD = enum.auto()


class VerticalIterationDomain:
    # TODO: implement properly + SIR encoding
    _index: t.Any

    def __init__(self, index=None):
        self._index = index

    @classmethod
    def from_index(cls, index) -> VerticalIterationDomain:
        # TODO: check that `index` is valid
        return cls(index)


class HorizontalIterationDomain:
    # TODO: implement properly + SIR encoding
    _index: t.Any

    def __init__(self, index=None):
        self._index = index

    @classmethod
    def from_index(cls, index) -> VerticalIterationDomain:
        # TODO: check that `index` is valid
        return cls(index)


@dataclasses.dataclass
class Domain(CompileTimeConstant):

    vertical_direction: t.Optional[VerticalIterationDirection] = None
    vertical_domain: VerticalIterationDomain = dataclasses.field(
        default_factory=VerticalIterationDomain
    )
    horizontal_domain: HorizontalIterationDomain = dataclasses.field(
        default_factory=HorizontalIterationDomain
    )
    _in_horizontal_direction: bool = False
    _indexable: bool = False

    @property
    def upward(self):
        if self._across_without_index():
            raise SemanticError("`across` requires an Index!")
        return dataclasses.replace(
            self,
            vertical_direction=VerticalIterationDirection.UPWARD,
            _in_horizontal_direction=False,
            _indexable=True,
        )

    @property
    def downward(self):
        if self._across_without_index():
            raise SemanticError("`across` requires an Index!")
        return dataclasses.replace(
            self,
            vertical_direction=VerticalIterationDirection.DOWNWARD,
            _in_horizontal_direction=False,
            _indexable=True,
        )

    @property
    def across(self):
        return dataclasses.replace(self, _in_horizontal_direction=True, _indexable=True)

    def __getitem__(self, index):
        if not self._indexable:
            raise SemanticError("Invalid index (double index?)!")
        if self._in_horizontal_direction:
            return dataclasses.replace(
                self,
                horizontal_domain=HorizontalIterationDomain.from_index(index),
                _indexable=False,
            )
        else:
            return dataclasses.replace(
                self,
                vertical_domain=VerticalIterationDomain.from_index(index),
                _indexable=False,
            )

    def _across_without_index(self) -> bool:
        return self._in_horizontal_direction and self._indexable

    def valid(self) -> bool:
        return not self._across_without_index() and self.vertical_direction is not None


class SparseFill(Slicable, ContextManager):
    pass


class HorizontalMarker:
    def __init__(self, encoding: int):
        self.__encoding = encoding
