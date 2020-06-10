from dusk.script import (
    stencil,
    Field,
    Edge,
    Cell,
    Vertex,
    forward,
    backward,
    neighbors,
    reduce,
)


@stencil
def ICON_laplacian_diamond(
    diff_multfac_smag: Field[Edge],
    tangent_orientation: Field[Edge],
    inv_primal_edge_length: Field[Edge],
    inv_vert_vert_length: Field[Edge],
    u_vert: Field[Vertex],
    v_vert: Field[Vertex],
    primal_normal_x: Field[Edge > Cell > Vertex],
    primal_normal_y: Field[Edge > Cell > Vertex],
    dual_normal_x: Field[Edge > Cell > Vertex],
    dual_normal_y: Field[Edge > Cell > Vertex],
    vn_vert: Field[Edge > Cell > Vertex],
    vn: Field[Edge],
    dvt_tang: Field[Edge],
    dvt_norm: Field[Edge],
    kh_smag_1: Field[Edge],
    kh_smag_2: Field[Edge],
    kh_smag: Field[Edge],
    nabla2: Field[Edge],
) -> None:

    for _ in forward:

        # fill sparse dimension vn vert using the loop concept
        for _ in neighbors[Edge > Cell > Vertex]:
            vn_vert = (
                u_vert[True] * primal_normal_x[True]
                + v_vert[True] * primal_normal_y[True]
            )

        # dvt_tang for smagorinsky
        dvt_tang = reduce(
            (u_vert[True] * dual_normal_x[True]) + (v_vert[True] * dual_normal_y[True]),
            "+",
            0.0,
            Edge > Cell > Vertex,
            [-1.0, 1.0, 0.0, 0.0],
        )

        dvt_tang = dvt_tang * tangent_orientation

        # dvt_norm for smagorinsky
        dvt_norm = reduce(
            u_vert[True] * dual_normal_x[True] + v_vert[True] * dual_normal_y[True],
            "+",
            0.0,
            Edge > Cell > Vertex,
            [0.0, 0.0, -1.0, 1.0],
        )

        # compute smagorinsky
        kh_smag_1 = reduce(
            vn_vert, "+", 0.0, Edge > Cell > Vertex, [-1.0, 1.0, 0.0, 0.0]
        )

        kh_smag_1 = (kh_smag_1 * tangent_orientation * inv_primal_edge_length) + (
            dvt_norm * inv_vert_vert_length
        )

        kh_smag_1 = kh_smag_1 * kh_smag_1

        kh_smag_2 = reduce(
            vn_vert, "+", 0.0, Edge > Cell > Vertex, [0.0, 0.0, -1.0, 1.0]
        )

        kh_smag_2 = (kh_smag_2 * inv_vert_vert_length) + (
            dvt_tang * inv_primal_edge_length
        )

        kh_smag_2 = kh_smag_2 * kh_smag_2

        # FIXME: `(kh_smag_1 + kh_smag_2)` should be in `sqrt`
        kh_smag = diff_multfac_smag * (kh_smag_1 + kh_smag_2)

        # compute nabla2 using the diamond reduction
        nabla2 = reduce(
            4.0 * vn_vert,
            "+",
            0.0,
            Edge > Cell > Vertex,
            [
                inv_primal_edge_length * inv_primal_edge_length,
                inv_primal_edge_length * inv_primal_edge_length,
                inv_vert_vert_length * inv_vert_vert_length,
                inv_vert_vert_length * inv_vert_vert_length,
            ],
        )

        nabla2 = nabla2 - (
            (8.0 * vn * inv_primal_edge_length * inv_primal_edge_length)
            + (8.0 * vn * inv_vert_vert_length * inv_vert_vert_length)
        )


@stencil
def test(a: Field[Edge], b: Field[Edge], c: Field[Edge], d: Field[Vertex]):
    # here we test vertical regions
    for k in backward[-5:]:
        # here we test basic expression
        a = b / c + 5

        # normal if/else
        if True:
            a = b + c
        else:
            b = c

        # only if
        if False:
            b = 5 * c

        # pseudo only else
        if False:
            pass
        else:
            a = 15

        # currently broken in dawn
        # elif no else
        # if False:
        #     a = b
        # elif True:
        #     c = a + 1

        # currently broken in dawn
        # elif as well
        # if False:
        #    a = b
        # elif True:
        #    c = a + 1
        # else:
        #    c = a - 1

        # reduction without weights
        c = reduce(d * 3, "+", 0.0, Edge > Vertex)
