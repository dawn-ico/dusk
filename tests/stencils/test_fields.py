from dusk.script import *
from dusk.test import stencil_test


@stencil_test()
def test_temp_field(a: Field[Edge, K], b: Field[Edge, K], out: Field[Edge, K]):
    x: Field[Edge, K]
    with levels_downward as k:
        x = 1  # stricly necessary in dawn
        if a > 5:
            x = a
        else:
            x = b
    with levels_downward as k:
        out = x


@stencil_test()
def test_temp_field_demoted(a: Field[Edge, K], b: Field[Edge, K], out: Field[Edge, K]):
    x: Field[Edge, K]
    y: Field[Edge, K]
    with levels_downward:
        x = a + b
        y = 5
        if x > 3:
            out = x
        else:
            out = y


@stencil_test()
def test_hv_field(
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


@stencil_test()
def test_h_offsets(
    a: Field[Edge > Cell > Edge, K], b: Field[Edge, K], c: Field[Edge > Cell > Edge, K]
):
    with levels_upward:
        with sparse[Edge > Cell > Edge]:
            a = b[Edge > Cell > Edge] + c
            a = b[Edge] + c


@stencil_test()
def test_v_offsets(a: Field[Edge, K], b: Field[Edge, K], c: Field[Edge, K]):
    with levels_upward as k:
        # classic central gradient access with "shortcut" on lhs (omit k)
        a[k] = b[k] + c[k]
        a[k] = b[k] + c[k - 1]  # classic backward gradient access


@stencil_test()
def test_hv_offsets(
    a: Field[Edge > Cell > Edge, K], b: Field[Edge, K], c: Field[Edge > Cell > Edge, K]
):
    with levels_upward as k:
        with sparse[Edge > Cell > Edge]:
            a = b[Edge, k] + c
            a = b[Edge > Cell > Edge, k + 1] + c[k]
            a = b[Edge, k] + b[Edge, k - 1] + c


@stencil_test()
def test_redundant_vertical_index_in_2d_field(
    edge_2d_field1: Field[Edge],
    edge_2d_field2: Field[Edge],
    cell_2d_field1: Field[Cell],
    cell_2d_field2: Field[Cell],
    vertex_2d_field1: Field[Vertex],
    vertex_2d_field2: Field[Vertex],
):

    # TODO: should we change this?
    with levels_upward as k:
        # it doesn't make sense to specify the vertical offset for 2d fields
        edge_2d_field2 = edge_2d_field1[k]
