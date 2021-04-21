from dusk.script import *


@stencil
def laplacian_fvm(
    vec: Field[Edge, K],
    div_vec: Field[Cell, K],
    rot_vec: Field[Vertex, K],
    nabla2_vec: Field[Edge, K],
    primal_edge_length: Field[Edge],
    dual_edge_length: Field[Edge],
    tangent_orientation: Field[Edge],
    geofac_rot: Field[Vertex > Edge],
    geofac_div: Field[Cell > Edge],
) -> None:

    nabla2t1_vec: Field[Edge, K]
    nabla2t2_vec: Field[Edge, K]

    with domain.upward:

        # compute curl (on vertices)
        rot_vec = sum_over(Vertex > Edge, vec * geofac_rot)

        # compute divergence (on cells)
        div_vec = sum_over(Cell > Edge, vec * geofac_div)

        # first term of of nabla2 (gradient of curl)
        nabla2t1_vec = sum_over(Edge > Vertex, rot_vec, weights=[-1.0, 1])
        nabla2t1_vec = tangent_orientation * nabla2t1_vec / primal_edge_length

        # second term of of nabla2 (gradient of divergence)
        nabla2t2_vec = sum_over(Edge > Cell, div_vec, weights=[-1.0, 1])
        nabla2t2_vec = tangent_orientation * nabla2t2_vec / dual_edge_length

        # finalize nabla2 (difference between the two gradients)
        nabla2_vec = nabla2t2_vec - nabla2t1_vec
