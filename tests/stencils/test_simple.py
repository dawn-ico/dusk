from dusk.script import *
from dusk.test import stencil_test


@stencil_test()
def test_control_flow(
    a: Field[Edge, K], b: Field[Edge, K], c: Field[Edge, K], d: Field[Vertex, K]
):

    # full vertical region without iteration variable
    with levels_downward:
        a = b / c + 5

        # normal if/else
        if True:
            a = b + c
        else:
            b = c

    # interval with iteration variable
    with levels_downward[:30] as k:

        # only if
        if True and True and not False:
            b = 5 * c

        # pseudo only else
        if a < b or a > b:
            pass
        else:
            a = 15

        a = b if b > c else c

    # interval with iteration variable
    with levels_downward[5:] as k:

        a = b / c + 5

        # no else
        if False:
            a = b
        elif True:
            c = a + 1

    # interval without iteration variable
    with levels_downward[-10:-2] as k:

        # if, elif and else
        if False:
            a = b
        elif True:
            c = a + 1
        else:
            c = a - 1


@stencil_test()
def test_vertical_iteration_variable(a: Field[Edge, K], b: Field[Edge, K]):

    with levels_downward[5:-3] as extraordinary_vertical_iteration_variable_name:
        a = b + 1
        a = a[extraordinary_vertical_iteration_variable_name - 1] * b + 1
        a = b[extraordinary_vertical_iteration_variable_name + 1] + 1

    with levels_downward[5:10] as again_extraordinary:
        a = a[again_extraordinary - 2] / b[again_extraordinary + 2] + 1


@stencil_test()
def test_compound_assignment(a: Field[Edge], b: Field[Edge], c: Field[Edge]):
    with levels_upward:
        # Add
        a += b
        # Sub
        b -= c
        # Mult
        c *= a
        # Div
        a /= b
        # Mod
        b %= c
        # Pow
        c **= a
        # LShift
        a <<= b
        # RShift
        b >>= c
        # BitOr
        c |= a
        # BitXor
        a ^= b
        # BitAnd
        b &= c
        # FloorDiv
        # unsupported!
        # MatMult
        # unsupported!


@stencil_test()
def test_power_operator(
    a: Field[Edge], b: Field[Edge], c: Field[Edge], d: Field[Edge > Cell]
):
    with levels_downward:
        a = b ** c
        if a == pow(b, c):
            b = b ** c

        # TODO: uncomment when bug fixed in dawn
        # a = min_over(Edge > Cell, pow(d, 5), weights=[b ** 3, -1])
