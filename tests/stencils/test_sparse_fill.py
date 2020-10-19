from dusk.script import *
from test_util import transpile, validate


def test_sparse_fill():
    validate(transpile(sparse_order_2_fill))
    validate(transpile(longer_fills))
    validate(transpile(fill_with_reduction))
    validate(transpile(ambiguous_fill))


@stencil
def sparse_order_2_fill(
    vertex: Field[Vertex],
    edge: Field[Edge, K],
    cell: Field[Cell],
    ve1: Field[Vertex > Edge, K],
    ve2: Field[Vertex > Edge, K],
    vc: Field[Vertex > Cell, K],
    ev1: Field[Edge > Vertex, K],
    ev2: Field[Edge > Vertex, K],
    ec: Field[Edge > Cell, K],
    cv1: Field[Cell > Vertex, K],
    cv2: Field[Cell > Vertex, K],
    ce: Field[Cell > Edge, K],
):

    with levels_upward:

        with sparse[Vertex > Edge]:
            ve1 = edge + 5 * ve2 + log(vertex)
        with sparse[Vertex > Cell]:
            vc = cell - 6
        with sparse[Edge > Vertex]:
            ev1 = vertex * 7 + ev2
        with sparse[Edge > Cell]:
            ec = cell / 8 / sin(edge)
        with sparse[Cell > Vertex]:
            cv1 = max(max(vertex ** 9, cv2), cell)
        with sparse[Cell > Edge]:
            ce = sqrt(edge ** 2 + cell ** 2)


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
    sparse2: Field[Edge > Cell > Vertex, K],
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
            sparse1 = sum_over(Edge > Vertex, vertex[Edge > Vertex])
            sparse2 = sum_over(Edge > Cell, cell)

    with levels_upward:
        with sparse[Edge > Cell > Vertex]:
            sparse1 = sum_over(Vertex > Cell > Vertex, vertex[Vertex])
            sparse2 = min_over(Vertex > Edge > Vertex, vertex[Vertex > Edge > Vertex])


@stencil
def ambiguous_fill(
    sparse1: Field[Edge > Cell > Edge, K],
    sparse2: Field[Edge > Vertex > Edge, K],
    edge1: Field[Edge, K],
    edge2: Field[Edge, K],
):
    with levels_downward:
        with sparse[Edge > Cell > Edge]:
            sparse1 = edge1[Edge] + 2 * edge2[Edge > Cell > Edge]

    with levels_downward:
        with sparse[Edge > Vertex > Edge]:
            sparse2 = edge2[Edge] - 4 * edge1[Edge > Vertex > Edge]
