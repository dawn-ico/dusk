import typing

from importlib.util import spec_from_file_location, module_from_spec
import ast

import dawn4py.serialization as dawn_ser

from dusk.passes import tree


class StencilObject:
    callable: typing.Callable
    filename: str
    stencil_scope: typing.Any
    tree_handle: typing.Optional[tree.TreeHandle]
    pyast: typing.Optional[ast.FunctionDef] = None
    globals: typing.Optional[dawn_ser.AST.GlobalVariableMap]
    sir_node: typing.Optional[dawn_ser.SIR.SIR] = None

    def __init__(self, callable: typing.Callable, filename: str = "<unknown>"):
        self.callable = callable
        self.filename = filename


stencil_collection: typing.List[StencilObject] = []


def import_stencil_file(path: str) -> None:
    spec = spec_from_file_location("__dusk_stencil__", path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
