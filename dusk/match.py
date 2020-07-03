from __future__ import annotations

from abc import ABC, abstractmethod
from ast import AST, stmt, expr

from dusk.errors import DuskSyntaxError
from dusk.util import pprint_matcher as pprint


__all__ = [
    "match",
    "does_match",
    "Ignore",
    "Repeat",
    "OneOf",
    "Optional",
    "Capture",
    "FixedList",
    "BreakPoint",
    "DuskSyntaxError",
]


class Matcher(ABC):
    @abstractmethod
    def match(self, ast, **kwargs) -> None:
        raise NotImplementedError


class MatcherError(Exception):
    def __init__(self, text: str) -> None:
        self.text = text


class FixedList(Matcher):
    _fields = ("matchers",)

    def __init__(self, *matchers):
        self.matchers = list(matchers)

    def match(self, nodes, **kwargs):

        if not isinstance(nodes, list):
            raise DuskSyntaxError(f"Expected a list, but got '{type(nodes)}'!", nodes)

        if len(nodes) != len(self.matchers):
            raise DuskSyntaxError(
                f"Expected a list of length {len(self.matchers)}'!", nodes
            )

        for matcher, node in zip(self.matchers, nodes):
            match(matcher, node, **kwargs)


class Repeat(Matcher):
    _fields = ("matcher", "n")

    def __init__(self, matcher, n="*"):
        assert isinstance(n, int) or n == "*"
        self.matcher = matcher
        self.n = n

    def match(self, nodes, **kwargs) -> None:

        if not isinstance(nodes, list):
            raise DuskSyntaxError(f"Expected a list, but got '{type(nodes)}'!", nodes)

        elif isinstance(self.n, int):
            if len(nodes) != self.n:
                raise DuskSyntaxError(
                    f"Expected a list of length {self.n}, but got list of length {len(nodes)}!",
                    nodes,
                )
            elif self.n == 0:
                return

        for node in nodes:
            match(self.matcher, node, **kwargs)


class _Ignore(Matcher):
    _fields = ()

    def match(self, node, **kwargs) -> None:
        pass


Ignore = _Ignore()


class OneOf(Matcher):
    _fields = ("matchers",)

    def __init__(self, *matchers) -> None:
        self.matchers = list(matchers)

    def match(self, node, **kwargs):
        matched = False
        for matcher in self.matchers:
            try:
                match(matcher, node, **kwargs)
                matched = True
                break
            except DuskSyntaxError:
                pass

        if not matched:
            raise DuskSyntaxError("Encountered unrecognized node '{node}'!", node)


def Optional(matcher) -> Matcher:
    return OneOf(matcher, None)


class Capture(Matcher):
    # TODO: could create a proper design & implementation for `is_list` functionality
    _fields = ("matcher", "name", "is_list")

    def __init__(self, matcher, name: str = None, is_list: bool = False) -> None:
        self.matcher = matcher
        self.name = name
        self.is_list = is_list

    def match(self, node, capturer=None, **kwargs) -> None:

        match(self.matcher, node, capturer=capturer, **kwargs)

        if capturer is not None and self.name is not None:
            if not self.is_list:
                # TODO: throw if value already exists once side-effects are handled
                capturer[self.name] = node
            else:
                capturer.setdefault(self.name, []).append(node)

    def to(self, name: str) -> Capture:
        self.name = name
        self.is_list = False
        return self

    def append(self, name: str) -> Capture:
        self.name = name
        self.is_list = True
        return self


class BreakPoint(Matcher):
    _fields = ("matcher", "active")

    def __init__(self, matcher, active=True):
        self.matcher = matcher
        self.active = active

    def match(self, node, **kwargs):
        if self.active:
            from dusk.util import pprint_matcher as pprint

            breakpoint()

        match(self.matcher, node, **kwargs)


def match(matcher, node, **kwargs) -> None:
    # this should be probably more flexible than hardcoding all possibilities
    if isinstance(matcher, Matcher):
        matcher.match(node, **kwargs)
    elif isinstance(matcher, AST):
        match_ast(matcher, node, **kwargs)
    elif isinstance(matcher, type):
        match_type(matcher, node, **kwargs)
    elif isinstance(matcher, PRIMITIVES):
        match_primitives(matcher, node, **kwargs)
    else:
        raise MatcherError(f"Invalid matcher '{matcher}'!")


def does_match(matcher, node, **kwargs) -> bool:
    try:
        match(matcher, node, **kwargs)
        return True
    except DuskSyntaxError:
        return False


def match_ast(matcher: AST, node, **kwargs):
    if not isinstance(node, type(matcher)):
        raise DuskSyntaxError(
            f"Expected node type '{type(matcher)}', but got '{type(node)}'!", node
        )

    for field in matcher._fields:
        try:
            match(getattr(matcher, field), getattr(node, field), **kwargs)
        except DuskSyntaxError as e:
            if e.loc is None and isinstance(node, (stmt, expr)):
                # add location info if possible
                e.loc_from_node(node)
            raise e


def match_type(matcher: type, node, **kwargs):
    if not isinstance(node, matcher):
        raise DuskSyntaxError(
            f"Expected type '{matcher}', but got '{type(node)}'", node
        )


PRIMITIVES = (str, int, type(None))


def match_primitives(matcher, node, **kwargs):
    if matcher != node:
        raise DuskSyntaxError(f"Expected '{matcher}', but got '{node}'!", node)
