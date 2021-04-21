from dusk.script import *
from dusk.test import stencil_test


dt = Global("dt")


@stencil_test()
def test_simple_global1(a: Field[Edge]):
    with domain.downward:
        a = dt


g = Global("some_global")


@stencil_test()
def test_simple_global2(a: Field[Edge], b: Field[Cell]):
    with domain.downward:
        a = sum_over(Edge > Cell, g * b)


one = Global("one")
two = Global("two")


@stencil_test()
def test_two_globals(a: Field[Edge]):
    with domain.downward:
        a = one + two


aliased = dt


@stencil_test()
def test_aliased_global(a: Field[Cell]):
    with domain.upward:
        a = aliased / (one - two)
