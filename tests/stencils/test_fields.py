from dusk.script import *
from test_util import transpile_and_validate


def test_field():
    transpile_and_validate(temp_field)
    transpile_and_validate(temp_field_demoted)
    transpile_and_validate(hv_field)
    transpile_and_validate(h_offsets)
    transpile_and_validate(v_offsets)
    transpile_and_validate(hv_offsets)


@stencil
def temp_field(a: Field[Edge, K], b: Field[Edge, K], out: Field[Edge, K]):
    x: Field[Edge]
    with levels_downward as k:
        x = 1  # stricly necessary in dawn
        if a > 5:
            x = a
        else:
            x = b
    with levels_downward as k:
        out = x


@stencil
def temp_field_demoted(a: Field[Edge, K], b: Field[Edge, K], out: Field[Edge, K]):
    x: Field[Edge]
    y: Field[Edge, K]
    with levels_downward:
        x = a + b
        y = 5
        if x > 3:
            out = x
        else:
            out = y


@stencil
def hv_field(
    out: Field[Edge, K],
    full: Field[Edge, K],
    horizontal: Field[Edge],
    horizontal_sparse: Field[Edge > Cell],
    vertical: Field[K],
):
    with levels_downward as k:
        out = full + horizontal + vertical
        out = reduce_over(Edge > Cell, horizontal_sparse, sum)
        out = sum_over(Edge > Cell, horizontal_sparse)


@stencil
def h_offsets(
    a: Field[Edge > Cell > Edge, K], b: Field[Edge, K], c: Field[Edge > Cell > Edge, K]
):
    with levels_upward:
        with sparse[Edge > Cell > Edge]:
            a = b[Edge > Cell > Edge] + c  # no offsets, defaults to Edge > Cell > Edge
            a = (
                b[Edge > Cell > Edge] + c[Edge > Cell > Edge]
            )  # verbose version of the above
            a = b[Edge] + c[Edge > Cell > Edge]  # center access for dense field


@stencil
def v_offsets(a: Field[Edge, K], b: Field[Edge, K], c: Field[Edge, K]):
    with levels_upward as k:
        # classic central gradient access with "shortcut" on lhs (omit k)
        a[k] = b[k] + c[k]
        a[k] = b[k] + c[k - 1]  # classic backward gradient access


@stencil
def hv_offsets(
    a: Field[Edge > Cell > Edge, K], b: Field[Edge, K], c: Field[Edge > Cell > Edge, K]
):
    with levels_upward as k:
        with sparse[Edge > Cell > Edge]:
            a = b[Edge, k] + c
            a = b[Edge > Cell > Edge, k + 1] + c[Edge > Cell > Edge, k]
            a = b[Edge, k] + b[Edge, k - 1] + c[Edge > Cell > Edge]
