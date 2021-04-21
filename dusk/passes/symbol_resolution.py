from __future__ import annotations

import typing

import builtins
from dusk.ir.pyast import *

# FIXME: move `grammar.transform` to a better place
from dusk import grammar, errors
from dusk.match import (
    Ignore as _,
    Optional,
    Capture,
    FixedList,
    EmptyList,
    name,
)
from dusk.ir import traversal
from dusk.passes import tree


class SymbolResolver(tree.TreeTransformer[AST]):

    # TODO: check preconditions?
    # TODO: check postconditions?

    externals: DictScope[typing.Any]
    api_fields: DictScope[typing.Any]
    temp_fields: DictScope[typing.Any]
    _current_scope: DictScope[typing.Any]

    def __init__(self, tree_handle: tree.TreeHandle[AST]):
        super().__init__(tree_handle)

        _builtins: DictScope[typing.Any] = DictScope(
            symbols=builtins.__dict__,
            can_add_symbols=False,
            allow_shadowing=True,
            parent=None,
        )
        globals: DictScope[typing.Any] = DictScope(
            symbols=tree_handle.annotations.callable.__globals__,
            can_add_symbols=False,
            allow_shadowing=True,
            parent=_builtins,
        )
        closure = {}
        if tree_handle.annotations.callable.__closure__ is not None:
            # FIXME: add a test for a proper closure
            closure = dict(
                zip(
                    tree_handle.annotations.callable.__code__.co_freevars,
                    (
                        c.cell_contents
                        for c in tree_handle.annotations.callable.__closure__
                    ),
                )
            )

        self.externals = DictScope(
            symbols=closure,
            can_add_symbols=False,
            allow_shadowing=True,
            parent=globals,
        )
        self.api_fields = DictScope(parent=self.externals)
        self.temp_fields = DictScope(parent=self.api_fields)
        self._current_scope = self.temp_fields

        tree_handle.annotations.stencil_scope = self.temp_fields

    def transform_bare(self):
        self.stencil(self.tree_handle.tree)

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
    def stencil(self, api_fields: typing.List[arg], body: typing.List[stmt]):
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
    def vertical_loop(self, domain: expr, body: typing.List, var: str = None):
        self.resolve_names(domain)

        # FIXME: should we add a context manager again?
        previous_scope = self._current_scope
        self._current_scope = DictScope(parent=previous_scope)

        if var is not None:
            self._current_scope.try_add(var, domain)

        self.resolve_names(body)

        self._current_scope = previous_scope

    def resolve_names(self, node: typing.Any):
        for child in traversal.post_order(node):
            if not isinstance(child, Name):
                # FIXME: should probably throw if there's other declarations here
                continue

            # FIXME: should probably throw if `not isinstance(node.ctx, pyast.Load)`

            name = child.id

            if not self._current_scope.contains(name):
                raise errors.SemanticError(f"Undeclared variable '{name}'!", child)
            child.decl = self._current_scope.fetch(name)


T = typing.TypeVar("T")


class DictScope(typing.Generic[T]):

    symbols: typing.Dict[str, T]
    can_add_symbols: bool
    # whether child scopes are allowed to shadow symbols from this scope
    allow_shadowing: bool
    parent: typing.Optional[DictScope[T]]

    def __init__(
        self,
        symbols: typing.Optional[typing.Dict[str, T]] = None,
        can_add_symbols: bool = True,
        allow_shadowing: bool = False,
        parent: typing.Optional[DictScope[T]] = None,
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
                f"This scope doesn't allow adding symbols ('{name}', '{symbol}')!"
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

    def local_iter(self) -> typing.Iterator[T]:
        return iter(self.symbols.values())
