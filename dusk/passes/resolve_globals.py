import ast

import dawn4py.serialization as ser
import dawn4py.serialization.SIR as sir

import dusk.script as script
from dusk.integration import StencilObject


def resolve_globals(stencil_object: StencilObject) -> None:

    # TODO: check preconditions & postconditions

    stencil_object.globals = sir.GlobalVariableMap()

    for node in ast.walk(stencil_object.pyast):
        if (
            isinstance(node, ast.Name)
            and hasattr(node, "decl")
            and isinstance(node.decl, script.Global)
        ):
            name = node.decl.name
            stencil_object.globals.map[name].double_value = 0
            node.sir = ser.make_var_access_expr(name, is_external=True)
