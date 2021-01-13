from dusk.script import *
from dusk.test import stencil_test


lb, nudging, interior, halo = HorizontalDomains(1, 2, 3, 4)


@stencil_test()
def test_simple_horizontal_domains(a: Field[Edge], b: Field[Edge], c: Field[Edge]):

    with domain.upward[7:-7].accross[interior:halo]:
        a = c

    with domain.accross[interior - 1 : halo].downward:
        a = b
