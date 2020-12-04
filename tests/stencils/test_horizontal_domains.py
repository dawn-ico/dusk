from dusk.script import *
from dusk.transpile import callable_to_pyast, pyast_to_sir, validate


def test_horizontal_domains():
    validate(pyast_to_sir(callable_to_pyast(simple_horizontal_domains)))


lb, nudging, interior, halo = HorizontalDomains(1, 2, 3, 4)


@stencil
def simple_horizontal_domains(a: Field[Edge], b: Field[Edge], c: Field[Edge]):

    with domain.upward[7:-7].accross[interior:halo]:
        a = c

    with domain.accross[interior - 1 : halo].downward:
        a = b
