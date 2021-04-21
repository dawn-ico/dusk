import typing
import ast as pyast

from dusk import errors
from dusk.ir import (
    pyast as dusk_pyast,
    concept,
    traversal,
    type_checking,
    loc,
)
from dusk.passes import tree


# FIXME: test invariants?


class CorrectTypes(tree.TreeValidator[dusk_pyast.AST]):
    def validate(self, tree_handle: tree.TreeHandle[dusk_pyast.AST]) -> None:
        for node in traversal.post_order(tree_handle.tree):
            type_checking.type_check_struct_node(node)


class BaseClassesInjected(tree.TreeValidator[dusk_pyast.AST]):
    def validate(self, tree_handle: tree.TreeHandle[dusk_pyast.AST]) -> None:
        for node in traversal.post_order(tree_handle.tree):
            if not isinstance(node, dusk_pyast.ASTBase):
                raise errors.ValidationError(
                    f"Base class '{dusk_pyast.ASTBase}' not present in node "
                    f"'{node}' ('{type(node)}'!"
                )


class ValidLocationInfo(tree.TreeValidator[dusk_pyast.AST]):
    def validate(self, tree_handle: tree.TreeHandle[dusk_pyast.AST]) -> None:
        for node in traversal.post_order(tree_handle.tree):
            if not isinstance(node, loc.LocationInfo):
                raise errors.ValidationError(
                    f"Node '{node}' isn't an instance of '{loc.LocationInfo}' ('{type(node)}')!"
                )

            loc.validate(node)


class RootNodeHasLocationInfo(tree.TreeValidator[dusk_pyast.AST]):
    def validate(self, tree_handle: tree.TreeHandle[dusk_pyast.AST]) -> None:
        loc.validate(tree_handle.tree)


class ConvertToRichAST(tree.TreeTransformer[typing.Union[pyast.AST, dusk_pyast.AST]]):

    preconditions = tree.TreeInvariants(RootNodeHasLocationInfo())
    postconditions = tree.TreeInvariants(
        CorrectTypes(), BaseClassesInjected(), ValidLocationInfo()
    )

    def transform_bare(self) -> None:

        assert isinstance(self.tree_handle.tree, pyast.AST)
        self.tree_handle.tree = convert_to_dusk_pyast(self.tree_handle.tree)

        assert isinstance(self.tree_handle.tree, dusk_pyast.AST)
        for child in concept.iter_children(self.tree_handle.tree):
            fix_location_info(child, self.tree_handle.tree)


def convert_to_dusk_pyast(node: typing.Any) -> typing.Any:
    if isinstance(node, pyast.AST):

        cls = dusk_pyast.node_map[type(node)]
        copy = cls()

        type_annotations = concept.get_struct_field_types(copy)

        for field in concept.get_struct_fields(copy):

            if typing.get_origin(type_annotations[field]) is dusk_pyast.ASTListBase:
                children = dusk_pyast.ASTListBase(
                    convert_to_dusk_pyast(child) for child in getattr(node, field)
                )
                setattr(copy, field, children)
            else:
                setattr(copy, field, convert_to_dusk_pyast(getattr(node, field)))

        if isinstance(node, (pyast.stmt, pyast.expr)):
            loc.copy(copy, node)

        return copy

    return node


def fix_location_info(node: typing.Any, parent: loc.LocationInfo) -> None:

    if not isinstance(node, loc.LocationInfo):
        return

    try:
        loc.validate(node)
    except errors.ValidationError:
        loc.copy(node, parent)

    for child in concept.iter_children(node):
        fix_location_info(child, node)
