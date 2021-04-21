from dusk.script import *
from dusk.test import stencil_test


lb, nudging, interior, halo, end = HorizontalDomains(0, 100, 200, 300, 400)


# FIXME: more & better tests


# FIXME: enable validation
@stencil_test(validate=False)
def test_simple_horizontal_domains(
    a: Field[Edge, K],
    b: Field[Edge, K],
    c: Field[Edge, K],
    d: Field[Edge > Cell],
    e: Field[Cell],
):

    with domain.upward[7:-7].across[interior:halo]:
        a = b

    with domain.across[interior - 1 : halo + 3].downward as k:
        c = a[k + 1]

        with sparse[Edge > Cell]:
            d = 2 * e + 1

    with domain.upward.across[lb - 1 : end + 3]:
        b = c

    with domain.across[nudging + 5 : interior].downward[5] as almost_k:
        a = (
            max_over(
                Edge > Cell > Edge,
                b[Edge > Cell > Edge, almost_k - 1]
                + b[Edge > Cell > Edge, almost_k + 1],
            )
            / 2
        )

    with domain.downward[:5].across[nudging : halo - 5]:
        c = a


@stencil_test(validate=False)
def test_invalid_interval_bug(a: Field[Cell], b: Field[Cell]):
    with domain.downward.across[lb : end - 5]:
        a = b
