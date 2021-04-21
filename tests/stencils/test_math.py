from dusk.script import *
from dusk.test import stencil_test


@stencil_test()
def test_math_stencil(a: Field[Cell], b: Field[Cell], c: Field[Cell], d: Field[Cell]):

    with domain.upward:

        a = sqrt(b)
        b = exp(c)
        c = log(a)
        a = sin(b)
        b = cos(c)
        c = tan(a)
        a = arcsin(b)
        b = arccos(c)
        c = arctan(a)
        a = abs(b)
        b = floor(c)
        c = ceil(a)
        a = isinf(b)
        b = isnan(c)

        a = max(b, c)
        d = min(a, b)
        c = pow(d, a)

        a = a + sqrt(b) + cos(c)
        a = max(min(b, c), d)
