import inspect
import ast

import dawn4py.serialization as dawn_ser

from dusk.integration import StencilObject
from dusk.grammar import Grammar
from dusk.passes.symbol_resolution import resolve_symbols
from dusk.passes.resolve_globals import resolve_globals
from dusk.passes.constant_folder import constant_fold


def stencil_object_to_sir(stencil_object: StencilObject) -> dawn_ser.SIR.Stencil:

    add_filename(stencil_object)
    add_pyast(stencil_object)
    resolve_symbols(stencil_object)
    constant_fold(stencil_object)
    resolve_globals(stencil_object)
    add_sir(stencil_object)

    return stencil_object.sir_node


def add_filename(stencil_object: StencilObject) -> None:
    stencil_object.filename = inspect.getfile(stencil_object.callable)


def add_pyast(stencil_object: StencilObject) -> None:
    # TODO: this will give wrong line numbers, there should be a way to fix them
    source = inspect.getsource(stencil_object.callable)
    stencil_ast = ast.parse(
        source,
        filename=stencil_object.filename,
        type_comments=True,
        feature_version=(3, 8),
    )
    assert isinstance(stencil_ast, ast.Module)
    assert len(stencil_ast.body) == 1
    assert isinstance(stencil_ast.body[0], ast.FunctionDef)
    stencil_object.pyast = stencil_ast.body[0]


def add_sir(stencil_object: StencilObject) -> None:
    assert stencil_object.pyast is not None

    sir_stencil = Grammar().stencil(stencil_object.pyast)
    stencil_object.sir_node = dawn_ser.make_sir(
        stencil_object.filename,
        dawn_ser.AST.GridType.Value("Unstructured"),
        [sir_stencil],
        global_variables=stencil_object.globals,
    )
