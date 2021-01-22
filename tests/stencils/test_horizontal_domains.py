from dusk.script import *
from dusk.test import stencil_test


lb, nudging, interior, halo, end = HorizontalDomains(0, 1, 2, 3, 4)


# FIXME: more & better tests


@stencil_test()
def test_simple_horizontal_domains(a: Field[Edge], b: Field[Edge], c: Field[Edge]):

    with domain.upward[7:-7].across[interior:halo]:
        a = c

    with domain.across[interior - 1 : halo + 3].downward:
        a = b
