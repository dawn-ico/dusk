import typing
import ast as pyast

from dusk import errors


attributes: typing.List[str] = [
    "lineno",
    "col_offset",
    "end_lineno",
    "end_col_offset",
]


class LocationInfo:

    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int


Locatable = typing.Union[LocationInfo, pyast.stmt, pyast.expr]


def validate(node: Locatable) -> None:

    # TODO: what about python's location info semantics?
    # https://docs.python.org/3.8/library/ast.html#ast.AST.lineno

    for loc_attr in attributes:
        if not hasattr(node, loc_attr):
            raise errors.ValidationError(
                f"Node '{node}' doesn't have location attribute '{loc_attr}'!"
            )

        loc_info = getattr(node, loc_attr)

        if not isinstance(loc_info, int) or 0 > loc_info:
            raise errors.ValidationError(
                f"Node '{node}' doesn't have a valid location attribute "
                f"'{loc_attr}' ('{loc_info}')!"
            )

        # TODO: what about relational constraints like `lineno` <= `end_lineno`?


def copy(destination: Locatable, source: Locatable) -> None:
    for loc_attr in attributes:
        setattr(destination, loc_attr, getattr(source, loc_attr))
