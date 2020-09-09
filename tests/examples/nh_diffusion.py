from dusk.script import *


@stencil
def ICON_laplacian_diamond(
    inv_primal_edge_length: Field[Edge],
    inv_vert_vert_length: Field[Edge],
    temp_vert: Field[Vertex, K],
    vn: Field[Edge, K],
    nabla2: Field[Edge, K],
) -> None:
    with levels_upward:

        # compute nabla2 using the diamond reduction
        nabla2 = sum_over(
            Edge > Cell > Vertex,
            4.0 * temp_vert,
            weights=[
                inv_primal_edge_length ** 2,
                inv_primal_edge_length ** 2,
                inv_vert_vert_length ** 2,
                inv_vert_vert_length ** 2,
            ],
        )

        nabla2 = nabla2 - (
            (8.0 * vn * inv_primal_edge_length ** 2)
            + (8.0 * vn * inv_vert_vert_length ** 2)
        )
