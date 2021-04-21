from __future__ import annotations
import typing as t


import enum
import dataclasses

import dawn4py.serialization as dawn_ser

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

    def to_sir(self):
        assert (
            self is VerticalIterationDirection.UPWARD
            or self is VerticalIterationDirection.DOWNWARD
        )
        if self is VerticalIterationDirection.UPWARD:
            return dawn_ser.AST.VerticalRegion.LoopOrder.Value("Forward")
        return dawn_ser.AST.VerticalRegion.LoopOrder.Value("Backward")


class VerticalIterationDomain:

    # unlike python semantics, end is inclusive here

    start: t.Optional[int]
    end: t.Optional[int]

    def __init__(self, start: t.Optional[int] = None, end: t.Optional[int] = None):
        self.start = start
        self.end = end

    def to_sir(self) -> t.Optional[dawn_ser.AST.Interval]:

        sir_start = dawn_ser.AST.Interval.SpecialLevel.Value("Start")
        sir_end = dawn_ser.AST.Interval.SpecialLevel.Value("End")

        if self.start is None:
            lower_level, lower_offset = sir_start, 0
        elif 0 <= self.start:
            lower_level, lower_offset = sir_start, self.start
        else:
            lower_level, lower_offset = sir_end, self.start

        if self.end is None:
            upper_level, upper_offset = sir_end, 0
        elif 0 <= self.end:
            upper_level, upper_offset = sir_start, self.end
        else:
            upper_level, upper_offset = sir_end, self.end

        return dawn_ser.make_interval(
            lower_level=lower_level,
            lower_offset=lower_offset,
            upper_level=upper_level,
            upper_offset=upper_offset,
        )

    @classmethod
    def from_index(cls, index) -> VerticalIterationDomain:
        if isinstance(index, int):
            return cls(index, index)

        if isinstance(index, slice):
            if index.step is not None:
                raise SemanticError("Cannot specify step sice for vertical intervals!")
            return cls(index.start, index.stop)

        raise SemanticError("Invalid vertical interval (expected `int` or `slice`)!")


class HorizontalMarker(CompileTimeConstant):
    encoding: int
    offset: int

    def __init__(self, encoding: int, offset: int = 0):
        self.encoding = encoding
        self.offset = offset

    def __add__(self, other) -> t.Union[HorizontalMarker, t.Type[NotImplemented]]:
        if not isinstance(other, int):
            return NotImplemented
        return HorizontalMarker(encoding=self.encoding, offset=self.offset + other)

    def __sub__(self, other) -> t.Union[HorizontalMarker, t.Type[NotImplemented]]:
        if not isinstance(other, int):
            return NotImplemented
        return HorizontalMarker(encoding=self.encoding, offset=self.offset - other)


class HorizontalIterationDomain:

    HorizontalRegion = t.Optional[t.Tuple[HorizontalMarker, HorizontalMarker]]

    region: HorizontalRegion

    def __init__(self, region: HorizontalRegion = None):
        self.region = region

    def to_sir(self) -> t.Optional[dawn_ser.AST.Interval]:
        if self.region is None:
            return None

        start, end = self.region

        # FIXME: should be `dawn_ser.make_magic_num_interval`
        return dawn_ser.utils.make_magic_num_interval(
            lower_level=start.encoding,
            lower_offset=start.offset,
            upper_level=end.encoding,
            upper_offset=end.offset,
        )

    @classmethod
    def from_index(cls, index) -> HorizontalIterationDomain:

        if (
            isinstance(index, slice)
            and index.step is None
            and isinstance(index.start, HorizontalMarker)
            and isinstance(index.stop, HorizontalMarker)
        ):
            return cls((index.start, index.stop))

        raise SemanticError(
            "Horizontal iteration domain must be a slice starting from and ending in horizontal markers!"
        )


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
