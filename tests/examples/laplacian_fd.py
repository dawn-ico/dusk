from dusk.script import *


@stencil
def laplacian_fd(
    inv_primal_edge_length: Field[Edge],
    inv_vert_vert_length: Field[Edge],
    temp_vert: Field[Vertex, K],
    nabla2: Field[Edge, K],
) -> None:

    temp_edge: Field[Edge, K]

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

        # interpolate temperature from vertices to edges via simple average
        temp_edge = sum_over(Edge > Vertex, temp_vert) / 2

        nabla2 = nabla2 - (
            (8.0 * temp_edge * inv_primal_edge_length ** 2)
            + (8.0 * temp_edge * inv_vert_vert_length ** 2)
        )
