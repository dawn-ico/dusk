from dusk.script import *
from test_util import transpile, validate


def test_math():
    validate(transpile(math_stencil))


@stencil
def math_stencil(a: Field[Cell], b: Field[Cell], c: Field[Cell], d: Field[Cell]):

    with levels_upward:

        a = sqrt(b)
        b = exp(c)
        c = log(a)
        a = sin(b)
        b = cos(c)
        c = tan(a)
        a = arcsin(b)
        b = arccos(c)
        c = arctan(a)
        a = fabs(b)
        b = floor(c)
        c = ceil(a)
        a = isinf(b)
        b = isnan(c)

        a = max(b, c)
        d = min(a, b)
        c = pow(d, a)

        a = a + sqrt(b) + cos(c)
        a = max(min(b, c), d)

