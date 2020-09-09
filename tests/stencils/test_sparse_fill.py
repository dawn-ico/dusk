from dusk.script import *
from test_util import transpile_and_validate


def test_sparse_fill():
    transpile_and_validate(sparse_order_2_fill)
    transpile_and_validate(longer_fills)
    transpile_and_validate(fill_with_reduction)


@stencil
def sparse_order_2_fill(
    vertex: Field[Vertex],
    edge: Field[Edge, K],
    cell: Field[Cell],
    ve: Field[Vertex > Edge, K],
    vc: Field[Vertex > Cell, K],
    ev: Field[Edge > Vertex, K],
    ec: Field[Edge > Cell, K],
    cv: Field[Cell > Vertex, K],
    ce: Field[Cell > Edge, K],
):

    with levels_upward:

        with sparse[Vertex > Edge]:
            ve = edge + 5
        with sparse[Vertex > Cell]:
            vc = cell - 6
        with sparse[Edge > Vertex]:
            ev = vertex * 7
        with sparse[Edge > Cell]:
            ec = cell / 8
        with sparse[Cell > Vertex]:
            cv = vertex ** 9
        with sparse[Cell > Edge]:
            ce = sqrt(edge)


@stencil
def longer_fills(
    sparse1: Field[Vertex > Edge > Cell > Vertex > Edge > Cell],
    sparse2: Field[Cell > Edge > Cell > Edge > Cell > Edge],
    sparse3: Field[Edge > Cell > Vertex > Edge > Vertex > Edge],
):
    with levels_upward:
        with sparse[Vertex > Edge > Cell > Vertex > Edge > Cell]:
            sparse1 = 50

    with levels_upward:
        with sparse[Cell > Edge > Cell > Edge > Cell > Edge]:
            sparse2 = 50

    with levels_upward:
        with sparse[Edge > Cell > Vertex > Edge > Vertex > Edge]:
            sparse3 = 50


@stencil
def fill_with_reduction(
    sparse1: Field[Edge > Cell > Vertex],
    sparse2: Field[Edge > Cell > Vertex],
    vertex: Field[Vertex],
    edge: Field[Edge, K],
    cell: Field[Cell],
):
    with levels_upward:
        with sparse[Edge > Cell > Vertex]:
            sparse1 = sum_over(Vertex > Cell, cell)
            sparse2 = min_over(Vertex > Edge, edge)

    with levels_upward:
        with sparse[Edge > Cell > Vertex]:
            sparse1 = sum_over(Vertex > Cell > Vertex, vertex[Vertex])
            sparse2 = min_over(Vertex > Edge > Vertex, vertex[Vertex > Edge > Vertex])
