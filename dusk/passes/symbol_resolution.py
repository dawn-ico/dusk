from __future__ import annotations

import typing as t
from types import CellType

import builtins
from ast import *

from dusk import grammar, errors
from dusk.match import (
    does_match,
    Ignore as _,
    Optional,
    Capture,
    FixedList,
    EmptyList,
    name,
)
from dusk.integration import StencilObject


def resolve_symbols(stencil_object: StencilObject) -> None:
    SymbolResolver(stencil_object).resolve_symbols()


class SymbolResolver:

    # TODO: check preconditions?
    # TODO: check postconditions?

    stencil_object: StencilObject
    externals: DictScope[t.Any]
    api_fields: DictScope[t.Any]
    temp_fields: DictScope[t.Any]
    _current_scope: DictScope[t.Any]

    def __init__(self, stencil_object: StencilObject):
        self.stencil_object = stencil_object

        _builtins: DictScope[t.Any] = DictScope(
            symbols=builtins.__dict__,
            can_add_symbols=False,
            allow_shadowing=True,
            parent=None,
        )
        globals: DictScope[t.Any] = DictScope(
            symbols=stencil_object.callable.__globals__,
            can_add_symbols=False,
            allow_shadowing=True,
            parent=_builtins,
        )
        closure = {}
        if stencil_object.callable.__closure__ is not None:
            # FIXME: add a test for a proper closure
            closure = dict(
                zip(
                    stencil_object.callable.__code__.co_freevars,
                    (c.cell_contents for c in stencil_object.callable.__closure__),
                )
            )

        self.externals: DictScope[t.Any] = DictScope(
            symbols=closure,
            can_add_symbols=False,
            allow_shadowing=True,
            parent=globals,
        )
        self.api_fields = DictScope(parent=self.externals)
        self.temp_fields = DictScope(parent=self.api_fields)
        self._current_scope = self.temp_fields

        stencil_object.stencil_scope = self.temp_fields

    def resolve_symbols(self):
        self.stencil(self.stencil_object.pyast)

    @grammar.transform(
        FunctionDef(
            name=_,
            args=arguments(
                posonlyargs=EmptyList,
                args=Capture(list).to("api_fields"),
                vararg=None,
                kwonlyargs=EmptyList,
                kw_defaults=EmptyList,
                kwarg=None,
                defaults=EmptyList,
            ),
            body=Capture(list).to("body"),
            decorator_list=_,
            returns=_,
            type_comment=None,
        )
    )
    def stencil(self, api_fields: t.List[arg], body: t.List[stmt]):
        for field in api_fields:
            self.api_field(field)

        remaining_stmts = []
        for stmt in body:

            if isinstance(stmt, AnnAssign):
                self.temp_field(stmt)
            # vertical iteration variables:
            elif isinstance(stmt, With):
                remaining_stmts.append(stmt)
                self.vertical_loop(stmt)

            else:
                remaining_stmts.append(stmt)
                self.resolve_names(stmt)

        # TODO: reenable when symbol resolution properly moved to only this pass
        # body.clear()
        # body.extend(remaining_stmts)

    @grammar.transform(
        arg(
            arg=Capture(str).to("name"),
            annotation=Capture(expr).to("field_type"),
            type_comment=None,
        )
    )
    def api_field(self, name: str, field_type: expr):
        self.resolve_names(field_type)
        self.api_fields.try_add(name, field_type)

    @grammar.transform(
        AnnAssign(
            target=name(Capture(str).to("name"), ctx=Store),
            value=None,
            annotation=Capture(expr).to("field_type"),
            simple=1,
        ),
    )
    def temp_field(self, name: str, field_type: expr):
        self.resolve_names(field_type)
        self.temp_fields.try_add(name, field_type)

    @grammar.transform(
        With(
            items=FixedList(
                withitem(
                    context_expr=Capture(expr).to("domain"),
                    optional_vars=Optional(name(Capture(str).to("var"), ctx=Store)),
                ),
            ),
            body=Capture(list).to("body"),
            type_comment=None,
        ),
    )
    def vertical_loop(self, domain: expr, body: t.List, var: str = None):
        self.resolve_names(domain)

        # FIXME: should we add a context manager again?
        previous_scope = self._current_scope
        self._current_scope = DictScope(parent=previous_scope)

        if var is not None:
            self._current_scope.try_add(var, domain)

        for stmt in body:
            self.resolve_names(stmt)

        self._current_scope = previous_scope

    def resolve_names(self, node: AST):
        for child in walk(node):
            if not isinstance(child, Name):
                continue

            name = child.id

            if not self._current_scope.contains(name):
                raise errors.SemanticError(f"Undeclared variable '{name}'!", child)
            child.decl = self._current_scope.fetch(name)


T = t.TypeVar("T")


class DictScope(t.Generic[T]):

    symbols: t.Dict[str, T]
    can_add_symbols: bool
    # whether child scopes are allowed to shadow symbols from this scope
    allow_shadowing: bool
    parent: t.Optional[DictScope[T]]

    def __init__(
        self,
        symbols: t.Optional[t.Dict[str, T]] = None,
        can_add_symbols: bool = True,
        allow_shadowing: bool = False,
        parent: t.Optional[DictScope[T]] = None,
    ):
        if symbols is None:
            symbols = {}
        self.symbols = symbols
        self.allow_shadowing = allow_shadowing
        self.can_add_symbols = can_add_symbols
        self.parent = parent

    # this is only to check fetching!
    def contains(self, name: str) -> bool:
        if name in self.symbols:
            return True
        if self.parent is not None:
            return self.parent.contains(name)
        return False

    def fetch(self, name: str) -> T:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.fetch(name)
        raise KeyError(f"Couldn't find symbol '{name}' in scope!")

    def try_add(self, name: str, symbol: T) -> None:

        if not self.can_add_symbols:
            raise KeyError(
                f"This scope doesn't allow adding of symbols ('{name}', '{symbol}')!"
            )

        if name in self.symbols:
            raise KeyError(
                f"Symbol '{name}' already exists in this scope ('{symbol}')!"
            )

        parent = self.parent
        while parent is not None:

            if not parent.allow_shadowing and name in parent.symbols:
                raise KeyError(
                    f"Symbol '{name}' illegally shadows another symbol "
                    f"('{symbol}', '{parent.symbols[name]}')!"
                )

            parent = parent.parent

        self.symbols[name] = symbol

    def local_iter(self) -> t.Iterator[T]:
        return iter(self.symbols.values())
