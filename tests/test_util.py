from typing import Callable

from inspect import getsource
import ast

from dusk.grammar import Grammar

from dawn4py.serialization import make_sir, SIR
from dawn4py.serialization.SIR import GridType
from dawn4py._dawn4py import run_optimizer_sir


def transpile(stencil: Callable) -> SIR:
    # TODO: this will give wrong line numbers, there should be a way to fix them
    stencil = ast.parse(getsource(stencil))

    assert isinstance(stencil, ast.Module)
    assert len(stencil.body) == 1
    stencil = stencil.body[0]
    assert Grammar.is_stencil(stencil)

    return make_sir(
        __file__, GridType.Value("Unstructured"), [Grammar().stencil(stencil)]
    )


def validate(sir: SIR) -> None:
    run_optimizer_sir(sir.SerializeToString())
