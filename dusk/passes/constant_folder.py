from typing import Any, Union, Tuple, Optional, Callable, Iterator

import ast

from dusk import integration, errors
from dusk.script import internal


DUSK_CONSTANT_KIND = "__dusk_constant_kind__"


def constant_fold(stencil_object: integration.StencilObject) -> None:

    inline_compiletime_constants(stencil_object)
    constant_fold_expr(stencil_object)


def inline_compiletime_constants(stencil_object: integration.StencilObject) -> None:

    for node, setter in post_order_mut_iter(stencil_object.pyast.body):
        # FIXME: is this in invariant after symbol resolution?
        # or should we do `hasattr(node, "decl")` instead?
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and isinstance(node.decl, internal.CompileTimeConstant)
        ):
            constant = ast.Constant(value=node.decl, kind=DUSK_CONSTANT_KIND)
            ast.copy_location(constant, node)
            setter(constant)


def constant_fold_expr(stencil_object: integration.StencilObject) -> None:
    for node, setter in post_order_mut_iter(stencil_object.pyast.body):
        if expr_is_constant_foldable(node):
            setter(evaluate_constant_foldable(node))


def expr_is_constant_foldable(node: ast.AST):
    # This deliberately doesn't work for nested expressions

    if not isinstance(node, ast.expr):
        return False

    if isinstance(node, (ast.Constant, ast.Name)):
        return False

    for field in node._fields:
        child = getattr(node, field)

        if isinstance(child, ast.AST):
            if not is_constant_or_childless(child):
                return False

        if isinstance(child, list) and not all(
            is_constant_or_childless(subchild) for subchild in child
        ):
            return False

    return True


def is_constant_or_childless(node: ast.AST):
    return 0 == len(node._fields) or isinstance(node, ast.Constant)


def evaluate_constant_foldable(node: ast.AST) -> Any:
    # TODO: replace `ast.Constant(value=$value, kind="dusk")` with
    # `ast.Name(id=$name, ctx=ast.Load())` and add
    # `$name: $value` to the locals dict ($name is a fresh variable name)
    # should probably try to clone the expression?

    var_counter = 0

    def make_fresh_name():
        nonlocal var_counter
        var_counter += 1
        return f"var{var_counter}"

    locals = {}

    def make_local_var_node(node: ast.Constant):
        fresh_name = make_fresh_name()
        assert fresh_name not in locals
        locals[fresh_name] = node.value
        var = ast.Name(id=fresh_name, ctx=ast.Load())
        ast.copy_location(var, node)
        return var

    copy = type(node)()
    ast.copy_location(copy, node)

    for field in node._fields:
        child = getattr(node, field)

        if is_dusk_constant(child):
            child_copy = make_local_var_node(child)

        elif isinstance(child, list):
            child_copy = [
                subchild
                if not is_dusk_constant(subchild)
                else make_local_var_node(subchild)
                for subchild in child
            ]

        else:
            child_copy = child

        setattr(copy, field, child_copy)

    copy = ast.Expression(body=copy)

    # TODO: filename & location info?
    # TODO: handle exceptions?
    value = eval(compile(copy, mode="eval", filename="<unknown>"), {}, locals)
    constant_node = ast.Constant(value=value, kind=DUSK_CONSTANT_KIND)
    ast.copy_location(constant_node, node)

    return constant_node


def is_dusk_constant(node: ast.AST):
    return isinstance(node, ast.Constant) and node.kind == DUSK_CONSTANT_KIND


# possible strategy:
# replace `CompileTimeConstant` `ast.Name` with `ast.Constant`
# If a node only has `ast.Constant` children -> constant fold
# for `ast.Constant` that have python objects, replace with `ast.Name`
#     and put the value in the locals dict

# TODO: how to do execution of `ast.Constant(..., kind="dusk")`?
# -> adding local closures


def post_order_mut_iter(
    node: Union[ast.AST, list],
    slot: Optional[Union[Tuple[ast.AST, str], Tuple[list, int]]] = None,
) -> Iterator[Tuple[ast.AST, Any]]:

    if isinstance(node, ast.AST):
        for field in node._fields:
            yield from post_order_mut_iter(getattr(node, field), (node, field))

        if slot is not None:
            yield node, make_setter(slot)

    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from post_order_mut_iter(child, (node, index))


def make_setter(
    slot: Union[Tuple[ast.AST, str], Tuple[list, int]]
) -> Callable[[ast.AST], None]:
    parent, entry = slot

    def ast_setter(node: ast.AST) -> None:
        setattr(parent, entry, node)

    def list_setter(node: ast.AST) -> None:
        parent[entry] = node

    return ast_setter if isinstance(parent, ast.AST) else list_setter
