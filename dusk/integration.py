from typing import Any, Optional, Callable, List

from importlib.util import spec_from_file_location, module_from_spec
import ast

import dawn4py.serialization.SIR as sir


class StencilObject:
    callable: Callable
    filename: str
    stencil_scope: Any
    pyast: Optional[ast.FunctionDef] = None
    globals: Optional[sir.GlobalVariableMap]
    sir_node: Optional[sir.SIR] = None

    def __init__(self, callable: Callable, filename: str = "<unknown>"):
        self.callable = callable
        self.filename = filename


stencil_collection: List[StencilObject] = []


def import_stencil_file(path: str) -> None:
    spec = spec_from_file_location("__dusk_stencil__", path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
