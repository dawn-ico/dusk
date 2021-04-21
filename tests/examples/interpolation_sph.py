from dusk.script import *


@stencil
def interpolation_sph(
    xn: Field[Cell],
    yn: Field[Cell],
    xc: Field[Cell],
    yc: Field[Cell],
    fn: Field[Cell],
    f_intp: Field[Cell],
    h: Field[Cell],
    pi: Field[Cell],
):
    wij: Field[Cell > Edge > Cell]
    qij: Field[Cell > Edge > Cell]
    Wn: Field[Cell]
    with domain.upward:
        with sparse[Cell > Edge > Cell]:
            qij = (
                sqrt(
                    (xc[Cell > Edge > Cell] - xn[Cell > Edge > Cell])
                    * (xc[Cell > Edge > Cell] - xn[Cell > Edge > Cell])
                    + (yc[Cell > Edge > Cell] - yn[Cell > Edge > Cell])
                    * (yc[Cell > Edge > Cell] - yn[Cell > Edge > Cell])
                )
                / h[Cell > Edge > Cell]
            )
            wij = (
                1.0
                / (
                    pi[Cell > Edge > Cell]
                    * h[Cell > Edge > Cell]
                    * h[Cell > Edge > Cell]
                )
                * exp(-qij * qij)
            )

        Wn = sum_over(Cell > Edge > Cell, wij)
        f_intp = sum_over(
            Cell > Edge > Cell,
            1 / Wn[Cell > Edge > Cell] * wij * fn[Cell > Edge > Cell],
        )
