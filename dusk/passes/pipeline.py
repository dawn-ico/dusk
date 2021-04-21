import inspect
import ast as pyast
import types
import typing

import dawn4py.serialization as dawn_ser

from dusk import errors, integration, grammar
from dusk.passes import (
    tree,
    enrich_pyast,
    symbol_resolution,
    constant_folder,
    resolve_globals,
)


def stencil_object_to_sir(
    stencil_object: integration.StencilObject,
) -> dawn_ser.SIR.SIR:

    setup_tree(stencil_object)

    tree_handle = stencil_object.tree_handle
    assert tree_handle is not None
    assert isinstance(tree_handle.tree, pyast.AST)
    invariants = tree_handle.invariants

    invariants.add(HasCallable())
    invariants.add(HasFilename())

    enrich_pyast.ConvertToRichAST(tree_handle).transform()

    invariants.add(enrich_pyast.CorrectTypes())
    invariants.add(enrich_pyast.BaseClassesInjected())
    invariants.add(enrich_pyast.ValidLocationInfo())

    # FIXME: cleanup passes!

    symbol_resolution.SymbolResolver(tree_handle).transform()
    constant_folder.ConstantFolder(tree_handle).transform()
    resolve_globals.GlobalsResolver(tree_handle).transform()

    add_sir(stencil_object)

    assert stencil_object.sir_node is not None
    return stencil_object.sir_node


class HasCallable(tree.TreeValidator[typing.Any]):
    def validate(self, tree_handle: tree.TreeHandle[typing.Any]) -> None:
        if "callable" in tree_handle.annotations and isinstance(
            tree_handle.annotations.callable, types.FunctionType
        ):
            return
        raise errors.ValidationError


class HasFilename(tree.TreeValidator[typing.Any]):
    def validate(self, tree_handle: tree.TreeHandle[typing.Any]) -> None:
        if "filename" in tree_handle.annotations and isinstance(
            tree_handle.annotations.filename, str
        ):
            return
        raise errors.ValidationError


def setup_tree(stencil_object: integration.StencilObject) -> None:

    # FIXME: this will give wrong line numbers, there should be a way to fix them
    filename = inspect.getfile(stencil_object.callable)
    source = inspect.getsource(stencil_object.callable)

    stencil_ast = pyast.parse(
        source,
        filename=filename,
        type_comments=True,
        feature_version=(3, 8),
    )
    assert isinstance(stencil_ast, pyast.Module)
    assert len(stencil_ast.body) == 1
    assert isinstance(stencil_ast.body[0], pyast.FunctionDef)

    tree_handle: tree.TreeHandle[pyast.AST] = tree.TreeHandle(stencil_ast.body[0])
    tree_handle.annotations.callable = stencil_object.callable
    tree_handle.annotations.filename = filename

    stencil_object.tree_handle = tree_handle


def add_sir(stencil_object: integration.StencilObject) -> None:
    # FIXME: cleanup

    sir_stencil = grammar.Grammar().stencil(stencil_object.tree_handle.tree)
    stencil_object.sir_node = dawn_ser.make_sir(
        stencil_object.tree_handle.annotations.filename,
        dawn_ser.AST.GridType.Value("Unstructured"),
        [sir_stencil],
        global_variables=stencil_object.tree_handle.annotations.globals,
    )
