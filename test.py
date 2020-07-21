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
    sqrt,
    cos,
    min,
    max,
)

# TODO better way to import math funs?


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

    with levels_upward:

        # fill sparse dimension vn vert using the loop concept
        with sparse[Edge > Cell > Vertex]:
            vn_vert = u_vert * primal_normal_x + v_vert * primal_normal_y

        # dvt_tang for smagorinsky
        dvt_tang = reduce_over(
            Edge > Cell > Vertex,
            (u_vert * dual_normal_x) + (v_vert * dual_normal_y),
            sum,
            init=0.0,
            weights=[-1.0, 1.0, 0.0, 0.0],
        )

        dvt_tang = dvt_tang * tangent_orientation

        # dvt_norm for smagorinsky
        dvt_norm = reduce_over(
            Edge > Cell > Vertex,
            u_vert * dual_normal_x + v_vert * dual_normal_y,
            sum,
            weights=[0.0, 0.0, -1.0, 1.0],
        )

        # compute smagorinsky
        kh_smag_1 = sum_over(
            Edge > Cell > Vertex, vn_vert, weights=[-1.0, 1.0, 0.0, 0.0]
        )

        kh_smag_1 = (kh_smag_1 * tangent_orientation * inv_primal_edge_length) + (
            dvt_norm * inv_vert_vert_length
        )

        kh_smag_1 = kh_smag_1 * kh_smag_1

        kh_smag_2 = reduce_over(
            Edge > Cell > Vertex, vn_vert, sum, weights=[0.0, 0.0, -1.0, 1.0]
        )

        kh_smag_2 = (kh_smag_2 * inv_vert_vert_length) + (
            dvt_tang * inv_primal_edge_length
        )

        kh_smag_2 = kh_smag_2 * kh_smag_2

        # FIXME: `(kh_smag_1 + kh_smag_2)` should be in `sqrt`
        kh_smag = diff_multfac_smag * (kh_smag_1 + kh_smag_2)

        # compute nabla2 using the diamond reduction
        nabla2 = reduce_over(
            Edge > Cell > Vertex,
            4.0 * vn_vert,
            sum,
            weights=[
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
    with levels_downward[-5:] as k:
        # here we test basic expression
        a = b / c + 5

        # normal if/else
        if True:
            a = b + c
        else:
            b = c

        # only if
        if True and True and not False:
            b = 5 * c

        # pseudo only else
        if a < b or a > b:
            pass
        else:
            a = 15

        a = b if b > c else c
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
        c = reduce_over(Edge > Vertex, d * 3, sum, init=0.0,)


@stencil
def h_offsets(
    a: Field[Edge > Cell > Edge], b: Field[Edge], c: Field[Edge > Cell > Edge]
):
    with levels_upward:
        with sparse[Edge > Cell > Edge]:
            a = b[Edge] + c  # no offsets, defaults to True
            a = (
                b[Edge > Cell > Edge] + c[Edge > Cell > Edge]
            )  # verbose version of the above
            a = b[Edge] + c[Edge > Cell > Edge]  # center access for dense field


@stencil
def v_offsets(a: Field[Edge], b: Field[Edge], c: Field[Edge]):
    with levels_upward as k:
        # classic central gradient access with "shortcut" on lhs (omit k)
        a[k] = b[k] + c[k]
        a[k] = b[k] + c[k - 1]  # classic backward gradient access


@stencil
def hv_offsets(
    a: Field[Edge > Cell > Edge], b: Field[Edge], c: Field[Edge > Cell > Edge]
):
    with levels_upward as k:
        with sparse[Edge > Cell > Edge]:
            a = b[Edge, k] + c
            a = b[Edge > Cell > Edge, k + 1] + c[Edge > Cell > Edge, k]
            a = b[Edge, k] + b[Edge, k - 1] + c[Edge > Cell > Edge]


@stencil
def test_math(a: Field[Edge], b: Field[Edge], c: Field[Edge], d: Field[Edge]):
    with levels_upward:
        a = a + sqrt(b) + cos(c)
        a = max(min(b, c), d)


@stencil
def other_vertical_iteration_variable(a: Field[Edge], b: Field[Edge]):

    with levels_downward[5:-3] as extraordinary_vertical_iteration_variable_name:
        a = b + 1
        a[extraordinary_vertical_iteration_variable_name - 1] = b + 1
        a = b[extraordinary_vertical_iteration_variable_name + 1] + 1
    with levels_downward[5:10] as again_extraordinary:
        a[again_extraordinary - 2] = b[again_extraordinary + 2] + 1
