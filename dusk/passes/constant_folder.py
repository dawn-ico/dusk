from typing import Any, Union, Tuple, Optional, Callable, Iterator

import ast

from dusk.script import internal
from dusk.ir import pyast, concept
from dusk.passes import tree


DUSK_CONSTANT_KIND = "__dusk_constant_kind__"


class ConstantFolder(tree.TreeTransformer[pyast.AST]):
    def transform_bare(self) -> None:

        inline_compiletime_constants(self.tree_handle)
        constant_fold_expr(self.tree_handle)


def inline_compiletime_constants(
    tree_handle: tree.TreeHandle[pyast.AST],
) -> None:

    for node, setter in post_order_mut_iter(tree_handle.tree.body):
        # FIXME: is this in invariant after symbol resolution?
        # or should we do `hasattr(node, "decl")` instead?
        if (
            isinstance(node, pyast.Name)
            and isinstance(node.ctx, pyast.Load)
            and isinstance(node.decl, internal.CompileTimeConstant)
        ):
            constant = pyast.Constant(value=node.decl, kind=DUSK_CONSTANT_KIND)
            ast.copy_location(constant, node)
            setter(constant)


def constant_fold_expr(tree_handle: tree.TreeHandle[pyast.AST]) -> None:
    for node, setter in post_order_mut_iter(tree_handle.tree.body):
        if isinstance(node, pyast.expr) and is_expr_constant_foldable(node):
            setter(evaluate_constant_foldable(node))


def is_expr_constant_foldable(node: pyast.AST) -> bool:
    # This deliberately doesn't work for nested expressions

    assert isinstance(node, pyast.expr)

    if isinstance(node, (pyast.Constant, pyast.Name)):
        return False

    for field in concept.get_struct_fields(node):
        child = getattr(node, field)

        # `pyast.Slice` isn't a subclass of `pyast.slice` in python 3.9
        if isinstance(child, (pyast.Slice, pyast.slice, pyast.comprehension)):
            if not is_slice_or_comprehension_constant_foldable(child):
                return False
            continue

        if isinstance(child, pyast.AST):
            if not is_constant_or_childless(child):
                return False

        if isinstance(child, list) and not all(
            is_constant_or_childless(subchild) for subchild in child
        ):
            return False

    return True


def is_slice_or_comprehension_constant_foldable(
    # `pyast.Slice` isn't a subclass of `pyast.slice` in python 3.9
    node: Union[pyast.Slice, pyast.slice, pyast.comprehension]
) -> bool:

    if isinstance(node, pyast.comprehension):
        return all(
            is_constant_or_childless(child)
            for child in (node.target, node.iter, *node.ifs)
        )

    if isinstance(node, pyast.Slice):
        return all(
            child is None or is_constant_or_childless(child)
            for child in (node.lower, node.upper, node.step)
        )

    if isinstance(node, pyast.Index):
        return is_constant_or_childless(node.value)

    if isinstance(node, pyast.ExtSlice):
        return all(
            is_slice_or_comprehension_constant_foldable(slice) for slice in node.dims
        )

    return False


def is_constant_or_childless(node: pyast.AST):
    return 0 == len(list(concept.get_struct_fields(node))) or isinstance(
        node, pyast.Constant
    )


def evaluate_constant_foldable(node: pyast.expr) -> Any:

    var_counter = 0

    def make_fresh_name():
        nonlocal var_counter
        var_counter += 1
        return f"var{var_counter}"

    locals = {}

    def make_local_var_node(node: pyast.Constant):
        fresh_name = make_fresh_name()
        assert fresh_name not in locals
        locals[fresh_name] = node.value
        var = pyast.Name(id=fresh_name, ctx=pyast.Load())
        ast.copy_location(var, node)
        return var

    copy = ast_copy(node)
    for child, setter in post_order_mut_iter(copy):
        if is_dusk_constant(child):
            setter(make_local_var_node(child))

    copy = pyast.Expression(body=copy)

    # TODO: filename & location info?
    # TODO: handle exceptions?
    value = eval(compile(copy, mode="eval", filename="<unknown>"), {}, locals)
    constant_node = pyast.Constant(value=value, kind=DUSK_CONSTANT_KIND)
    ast.copy_location(constant_node, node)

    return constant_node


def is_dusk_constant(node: pyast.AST):
    return isinstance(node, pyast.Constant) and node.kind == DUSK_CONSTANT_KIND


def ast_copy(node: Any):

    if isinstance(node, pyast.AST):
        copy = type(node)(
            **{
                field: ast_copy(getattr(node, field))
                for field in concept.get_struct_fields(node)
            }
        )
        ast.copy_location(copy, node)
        return copy

    if isinstance(node, list):
        return [ast_copy(child) for child in node]

    return node


def post_order_mut_iter(
    node: Union[pyast.AST, list],
    slot: Optional[Union[Tuple[pyast.AST, str], Tuple[list, int]]] = None,
) -> Iterator[Tuple[pyast.AST, Any]]:
    # FIXME: `Any` above is unnecessarily impresice!

    # FIXME: move into `dusk.ir.traversal`

    if isinstance(node, pyast.AST):
        for field in concept.get_struct_fields(node):
            yield from post_order_mut_iter(getattr(node, field), (node, field))

        if slot is not None:
            yield node, make_setter(slot)

    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from post_order_mut_iter(child, (node, index))


def make_setter(
    slot: Union[Tuple[pyast.AST, str], Tuple[list, int]]
) -> Callable[[pyast.AST], None]:
    parent, entry = slot

    def ast_setter(node: pyast.AST) -> None:
        setattr(parent, entry, node)

    def list_setter(node: pyast.AST) -> None:
        parent[entry] = node

    return ast_setter if isinstance(parent, pyast.AST) else list_setter
