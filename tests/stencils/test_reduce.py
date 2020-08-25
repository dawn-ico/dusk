from dusk.script import *
from test_util import transpile_and_validate


def test_reduce():
    transpile_and_validate(kw_args)


# TODO: Add tests for the following cases
# different expressions
# different location chains
# nested reductions
# expressions in weights (& init)


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
