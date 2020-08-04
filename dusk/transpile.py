from typing import Iterator, List
import ast
from dusk.grammar import Grammar
from dusk.errors import DuskSyntaxError

from dawn4py import compile, CodeGenBackend
from dawn4py.serialization import pprint, make_sir, to_json as sir_to_json
from dawn4py.serialization.SIR import GridType

import os

__all__ = ["transpile", "backend_map", "default_backend"]

backend_map = {
    "ico-naive": CodeGenBackend.CXXNaiveIco,
    "ico-cuda": CodeGenBackend.CUDAIco,
}
default_backend = "ico-naive"


def iter_stencils(module: ast.Module) -> Iterator[ast.AST]:
    for stmt in module.body:
        if isinstance(stmt, ast.FunctionDef) and Grammar.is_stencil(stmt):
            yield stmt


def transpile(
    in_path: str, out_path: str, backend: str = default_backend, dump_sir: bool = False
) -> None:

    with open(in_path, "r") as in_file:
        in_str = in_file.read()
        in_ast = ast.parse(in_str, filename=in_path, type_comments=True)

        grammar = Grammar()

        # TODO: handle errors in different stencils separately
        stencils = [grammar.stencil(node) for node in iter_stencils(in_ast)]

        sir = make_sir(in_path, GridType.Value("Unstructured"), stencils)

        if dump_sir:
            out_name = os.path.splitext(out_path)[0]
            with open(out_name + ".json", "w+") as f:
                f.write(sir_to_json(sir))

        out_code = compile(sir, backend=backend_map[backend])

        with open(out_path, "w") as out_file:
            out_file.write(out_code)
