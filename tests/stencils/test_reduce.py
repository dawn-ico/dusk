from dusk.script import *
from test_util import transpile, validate


def test_reduce():
    validate(transpile(various_reductions))
    validate(transpile(kw_args))


@stencil
def various_reductions(
    vertex: Field[Vertex],
    edge: Field[Edge, K],
    cell: Field[Cell, K],
    ve: Field[Vertex > Edge, K],
    vc: Field[Vertex > Cell, K],
    ev: Field[Edge > Vertex, K],
    ec: Field[Edge > Cell, K],
    cv: Field[Cell > Vertex, K],
    ce: Field[Cell > Edge, K],
    sparse1: Field[Vertex > Edge > Cell > Vertex > Edge > Cell],
    sparse2: Field[Cell > Edge > Cell > Edge > Cell > Edge],
    sparse3: Field[Cell > Vertex > Cell > Vertex > Cell > Edge],
):
    with levels_upward:
        edge = sum_over(Edge > Cell, cell * ec)

        cell = max_over(Cell > Vertex, pow(vertex, cv / cell))

        vertex = reduce_over(
            Vertex > Edge,
            log(ve)
            / max_over(
                Edge > Cell > Vertex > Edge,
                sin(edge[Edge]) / exp(edge[Edge > Cell > Vertex > Edge]) ** 5
                - sum_over(
                    Edge > Cell,
                    sqrt(cell),
                    weights=[edge[Edge], arcsin(edge[Edge] * 100),],
                ),
            ),
            mul,
            init=sin(vertex) * floor(vertex / 8.765),
        )

        cell = reduce_over(
            Cell > Vertex > Cell > Vertex > Cell > Edge,
            sparse3 + sin(edge),
            min,
            init=-1,
        )


@stencil
def kw_args(
    a: Field[Edge], b: Field[Edge], c: Field[Edge > Cell], d: Field[Edge > Cell]
):
    with levels_downward:

        # reductions without weights
        a = reduce_over(Edge > Cell, c * 3, sum, init=0.0)
        b = reduce_over(Edge > Cell, c * 3, mul, init=0.0)
        a = sum_over(Edge > Cell, d * 3, init=0.0)
        b = min_over(Edge > Cell, d * 3, init=0.0)
        a = max_over(Edge > Cell, c * 3, init=0.0)

        # reductions without init
        b = reduce_over(Edge > Cell, c * 3, sum, weights=[-1, 1])
        a = reduce_over(Edge > Cell, d * 3, mul, weights=[-1, 1])
        b = sum_over(Edge > Cell, d * 3, weights=[-1, 1])
        a = min_over(Edge > Cell, c * 3, weights=[-1, 1])
        b = max_over(Edge > Cell, c * 3, weights=[-1, 1])

        # reductions with both
        a = reduce_over(Edge > Cell, d * 3, sum, init=0.0, weights=[-1, 1])
        b = reduce_over(Edge > Cell, d * 3, mul, weights=[-1, 1], init=1.0)
        a = sum_over(Edge > Cell, c * 3, init=10.0, weights=[-1, 1])
        b = min_over(Edge > Cell, c * 3, weights=[-1, 1], init=-100)
        a = max_over(Edge > Cell, d * 3, init=723, weights=[-1, 1])
