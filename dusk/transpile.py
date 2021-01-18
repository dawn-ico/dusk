from typing import Optional, Callable, List
from inspect import getsource

from functools import reduce
from operator import add
import ast
from io import TextIOBase

from dusk.grammar import Grammar

from dawn4py import compile, CodeGenBackend, set_verbosity, LogLevel
from dawn4py.serialization import make_sir, to_json as sir_to_json
from dawn4py.serialization.SIR import GridType, SIR
from dawn4py._dawn4py import run_optimizer_sir


backend_map = {
    "ico-naive": CodeGenBackend.CXXNaiveIco,
    "ico-cuda": CodeGenBackend.CUDAIco,
}
default_backend = "ico-naive"


def str_to_pyast(source: str, filename: str = "<unknown>") -> List[ast.FunctionDef]:
    source_ast = ast.parse(source, filename=filename, type_comments=True)
    assert isinstance(source_ast, ast.Module)
    return [
        stencil_ast
        for stencil_ast in source_ast.body
        if isinstance(stencil_ast, ast.FunctionDef) and Grammar.is_stencil(stencil_ast)
    ]


def callable_to_pyast(
    stencil: Callable, filename: str = "<unknown>"
) -> List[ast.FunctionDef]:
    # TODO: this will give wrong line numbers, there should be a way to fix them
    source = getsource(stencil)
    stencil_ast = ast.parse(source, filename=filename, type_comments=True)
    assert isinstance(stencil_ast, ast.Module)
    assert len(stencil_ast.body) == 1
    assert Grammar.is_stencil(stencil_ast.body[0])
    return [stencil_ast.body[0]]


def callables_to_pyast(
    stencils: List[Callable], filename: str = "<unknown>"
) -> List[ast.FunctionDef]:
    return reduce(
        add, (callable_to_pyast(stencil, filename=filename) for stencil in stencils)
    )


def pyast_to_sir(stencils: List[ast.FunctionDef], filename: str = "<unknown>") -> SIR:

    grammar = Grammar()
    # TODO: should probably throw instead
    assert all(grammar.is_stencil(stencil) for stencil in stencils)

    # TODO: handle errors in different stencils separately
    stencils = [grammar.stencil(stencil) for stencil in stencils]

    if grammar.globals is not None:
        return make_sir(
            filename,
            GridType.Value("Unstructured"),
            stencils,
            global_variables=grammar.globals,
        )
    else:
        return make_sir(filename, GridType.Value("Unstructured"), stencils)


def sir_to_cpp(
    sir: SIR, verbose: bool = False, groups: List = [], backend=default_backend
) -> str:
    if verbose:
        set_verbosity(LogLevel.All)
    # TODO: default pass groups are bugged in Dawn, need to pass empty list of groups
    return compile(sir, groups=groups, backend=backend_map[backend])


def validate(sir: SIR) -> None:
    run_optimizer_sir(sir.SerializeToString())


def transpile(
    in_path: str,
    out_sir_file: Optional[TextIOBase],
    out_gencode_file: Optional[TextIOBase],
    backend: str = default_backend,
    verbose: bool = False,
) -> None:

    with open(in_path, "r") as in_file:
        in_str = in_file.read()

    pyast = str_to_pyast(in_str, filename=in_path)
    sir = pyast_to_sir(pyast, filename=in_path)

    if out_sir_file is not None:
        out_sir_file.write(sir_to_json(sir))
    if out_gencode_file is not None:
        out_gencode_file.write(sir_to_cpp(sir, backend=backend, verbose=verbose))
