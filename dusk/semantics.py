from __future__ import annotations
from typing import NewType, Optional, ClassVar, Iterator, Iterable, List, Dict

from enum import Enum, auto, unique
from dataclasses import dataclass
from contextlib import contextmanager
from itertools import chain

from dawn4py.serialization import SIR as sir

from dusk.errors import DuskSyntaxError, DuskInternalError


@unique
class SymbolKind(Enum):
    Field = auto()
    VerticalIterationVariable = auto()


class Symbol:
    # Subclasses should be be limited to `SymbolKind`
    # `Symbol` should be considered an algebraic data type
    kind: ClassVar[SymbolKind]


class VerticalIterationVariable(Symbol):
    kind: ClassVar[SymbolKind] = SymbolKind.VerticalIterationVariable


@dataclass
class Field(Symbol):
    kind: ClassVar[SymbolKind] = SymbolKind.Field

    sir: sir.Field


class Scope(Iterable[Symbol]):
    symbols: Dict[str, Symbol]
    parent: Optional[Scope]

    # TODO: better error messages
    def __init__(self, parent: Optional[Scope] = None) -> None:
        self.symbols = {}
        self.parent = parent

    def contains(self, name: str) -> bool:
        if name in self.symbols.keys():
            return True
        if self.parent is not None:
            return self.parent.contains(name)
        return False

    def fetch(self, name: str) -> Symbol:
        if name in self.symbols.keys():
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.fetch(name)
        raise KeyError

    def add(self, name: str, symbol: Symbol) -> None:
        if self.contains(name):
            raise KeyError

        self.symbols[name] = symbol

    def __iter__(self) -> Iterator[Symbol]:
        if self.parent is None:
            return iter(self.symbols.values())
        return chain(iter(self.symbols.values()), self.parent)


class ScopeHelper:

    current_scope: Scope

    def __init__(self) -> None:
        super().__init__()
        self.current_scope = Scope()

    # to be used in a `with` statement
    @contextmanager
    def new_scope(self):
        old_scope = self.current_scope
        self.current_scope = Scope(old_scope)
        yield self.current_scope
        self.current_scope = old_scope


LocationTypeValue = NewType("LocationTypeValue", int)
LocationChain = List[LocationTypeValue]


class LocationHelper:

    in_vertical_region: bool
    in_loop_stmt: bool
    in_reduction: bool
    neighbor_iterations: List[LocationChain]

    @staticmethod
    def is_dense(field: sir.Field) -> bool:
        assert (
            field.field_dimensions.WhichOneof("horizontal_dimension")
            == "unstructured_horizontal_dimension"
        )
        return 1 >= len(
            field.field_dimensions.unstructured_horizontal_dimension.sparse_part
        )

    @staticmethod
    def is_ambiguous(chain: LocationChain) -> bool:
        assert 1 < len(chain)
        return chain[0] == chain[-1]

    def __init__(self):
        self.in_vertical_region = False
        self.in_loop_stmt = False
        self.in_reduction = False
        self.neighbor_iterations = []

    @property
    def current_neighbor_iteration(self) -> LocationChain:
        assert self.in_neighbor_iteration
        return self.neighbor_iterations[-1]

    @property
    def in_neighbor_iteration(self) -> bool:
        return 0 < len(self.neighbor_iterations)

    @contextmanager
    def vertical_region(self):
        if self.in_vertical_region:
            raise DuskSyntaxError("Vertical regions can't be nested!")
        if self.in_loop_stmt or self.in_reduction:
            raise DuskSyntaxError(
                "Encountered vertical region inside reduction or loop statement!"
            )
        self.in_vertical_region = True
        yield
        self.in_vertical_region = False

    @contextmanager
    def _neighbor_iteration(self, location_chain: LocationChain):

        if not self.in_vertical_region:
            raise DuskSyntaxError(
                "Reductions or loop statements can only occur inside vertical regions!"
            )

        if len(location_chain) <= 1:
            raise DuskSyntaxError(
                "Reductions and loop statements must have a location chain of"
                "length longer than 1!"
            )

        self.neighbor_iterations.append(location_chain)
        yield
        self.neighbor_iterations.pop()

    @contextmanager
    def loop_stmt(self, location_chain: LocationChain):

        if self.in_loop_stmt:
            raise DuskSyntaxError("Nested loop statements aren't allowed!")
        if self.in_reduction:
            raise DuskSyntaxError("Loop statements can't occur inside reductions!")

        self.in_loop_stmt = True
        with self._neighbor_iteration(location_chain):
            yield
        self.in_loop_stmt = False

    @contextmanager
    def reduction(self, location_chain: LocationChain):
        self.in_reduction = True
        with self._neighbor_iteration(location_chain):
            yield
        self.in_reduction = False

    def is_valid_horizontal_index(
        self, field: sir.Field, hindex: LocationChain = None
    ) -> bool:
        raise NotImplementedError


class DuskContextHelper:
    def __init__(self) -> None:
        self.location = LocationHelper()
        self.scope = ScopeHelper()

    @contextmanager
    def vertical_region(self, name: Optional[str] = None):
        with self.location.vertical_region(), self.scope.new_scope():
            if name is not None:
                self.scope.current_scope.add(name, VerticalIterationVariable())
            yield
