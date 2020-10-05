from dusk.script import *
from test_util import transpile


def test_vertical_index_fields():
    # FIXME: add validation again
    transpile(various_expression)
    transpile(index_fields_with_offsets)
    transpile(various_dimensions_mix)
    transpile(sparse_index_fields)


@stencil
def various_expression(
    edge_3d_field1: Field[Edge, K],
    edge_3d_field2: Field[Edge, K],
    sparse_3d_field1: Field[Edge > Cell > Vertex > Edge, K],
    sparse_3d_index_field1: IndexField[Edge > Cell > Vertex > Edge, K],
    sparse_3d_field2: Field[Edge > Cell > Vertex > Edge, K],
    sparse_3d_field3: Field[Edge > Vertex > Cell > Edge, K],
    sparse_3d_index_field3: IndexField[Edge > Vertex > Cell > Edge, K],
    edge_3d_index_field: IndexField[Edge, K],
):
    with levels_upward[30:-4] as k:
        edge_3d_field1 = min_over(
            Edge > Cell > Vertex > Edge,
            sin(sparse_3d_field1)
            * pow(
                edge_3d_field2[Edge > Cell > Vertex > Edge, edge_3d_index_field + 1]
                + 17,
                sparse_3d_field2[edge_3d_index_field - 1],
            )
            / 5,
        )

        edge_3d_field2 = sum_over(
            Edge > Vertex > Cell > Edge,
            tan(
                sparse_3d_field3[
                    Edge > Vertex > Cell > Edge, sparse_3d_index_field3 + 3,
                ]
            )
            / edge_3d_field1[Edge, edge_3d_index_field + 1]
            + reduce_over(
                Edge > Cell > Vertex > Edge,
                min(sparse_3d_field1[sparse_3d_index_field1 - 1], edge_3d_field1[Edge])
                - floor(
                    edge_3d_field1[Edge > Cell > Vertex > Edge, edge_3d_index_field]
                )
                + log(edge_3d_field1[Edge, edge_3d_index_field - 2]),
                mul,
                init=2,
            ),
            init=20,
        )

        with sparse[Edge > Cell > Vertex > Edge]:
            sparse_3d_field1 = edge_3d_field1[Edge, edge_3d_index_field + 2] - sum_over(
                Edge > Vertex > Cell > Edge,
                arcsin(sparse_3d_field3[sparse_3d_index_field3 - 1])
                ** sqrt(edge_3d_field2[Edge, edge_3d_index_field]),
            )


@stencil
def index_fields_with_offsets(
    sparse_3d_index_field1: IndexField[Edge > Cell > Vertex, K],
    sparse_3d_field1: Field[Edge > Cell > Vertex, K],
    sparse_3d_index_field2: IndexField[Edge > Cell > Edge, K],
    sparse_3d_field2: Field[Edge > Cell > Edge, K],
    sparse_3d_field3: Field[Edge > Cell > Edge, K],
    cell_3d_index_field: IndexField[Cell, K],
    cell_3d_field1: Field[Cell, K],
    cell_3d_field2: Field[Cell, K],
    edge_3d_field: Field[Edge, K],
    edge_3d_index_field: IndexField[Edge, K],
):

    with levels_downward as k:
        cell_3d_field1 = cell_3d_field2[cell_3d_index_field + 1]
        cell_3d_field1 = cell_3d_field2[cell_3d_index_field + 0]
        cell_3d_field1 = cell_3d_field2[cell_3d_index_field - 1]

        edge_3d_field = sum_over(
            Edge > Cell > Vertex, sparse_3d_field1[sparse_3d_index_field1 + 10]
        )

        with sparse[Edge > Cell > Vertex]:
            sparse_3d_field1 = edge_3d_field[sparse_3d_index_field1 - 0]

        edge_3d_field = sum_over(
            Edge > Cell > Vertex, sparse_3d_field1[sparse_3d_index_field1 - 10]
        )

        edge_3d_field = sum_over(
            Edge > Cell > Edge, sparse_3d_field2[edge_3d_index_field - 3]
        )

        with sparse[Edge > Cell > Edge]:
            sparse_3d_field2 = edge_3d_field[Edge, edge_3d_index_field + 1]

        with sparse[Edge > Cell > Edge]:
            sparse_3d_field2 = sparse_3d_field3[edge_3d_index_field - 1]

        edge_3d_field = sum_over(
            Edge > Cell > Edge,
            edge_3d_field[Edge > Cell > Edge, edge_3d_index_field + 2],
        )


@stencil
def various_dimensions_mix(
    vertex_2d_field: Field[Vertex],
    vertex_3d_field1: Field[Vertex, K],
    vertex_3d_field2: Field[Vertex, K],
    edge_2d_field: Field[Edge],
    edge_3d_field1: Field[Edge, K],
    edge_3d_field2: Field[Edge, K],
    cell_2d_field: Field[Cell],
    cell_3d_field1: Field[Cell, K],
    cell_3d_field2: Field[Cell, K],
    vertex_2d_index_field: IndexField[Vertex],
    vertex_3d_index_field: IndexField[Vertex, K],
    edge_2d_index_field: IndexField[Edge],
    edge_3d_index_field: IndexField[Edge, K],
    cell_2d_index_field: IndexField[Cell],
    cell_3d_index_field: IndexField[Cell, K],
    any_1d_index_field: IndexField[K],
):
    with levels_upward:
        # 3d fields with 3d index fields
        vertex_3d_field2 = vertex_3d_field1[vertex_3d_index_field]
        edge_3d_field2 = edge_3d_field1[edge_3d_index_field]
        cell_3d_field2 = cell_3d_field1[cell_3d_index_field]

    with levels_downward[3:-5] as k:
        # 3d fields with 2d index fields
        vertex_3d_field2 = vertex_3d_field1[vertex_2d_index_field]
        edge_3d_field2 = edge_3d_field1[edge_2d_index_field]
        cell_3d_field2 = cell_3d_field1[cell_2d_index_field]

        # 3d fields with 1d index fields
        vertex_3d_field2 = vertex_3d_field1[any_1d_index_field]
        edge_3d_field2 = edge_3d_field1[any_1d_index_field]
        cell_3d_field2 = cell_3d_field1[any_1d_index_field]

        # 2d fields with 3d index fields
        vertex_2d_field = vertex_3d_field1[vertex_3d_index_field]
        edge_2d_field = edge_3d_field1[edge_3d_index_field]
        cell_2d_field = cell_3d_field1[cell_3d_index_field]

    with levels_downward[:20] as levels:
        # 2d fields with 2d index fields
        vertex_2d_field = vertex_3d_field1[vertex_2d_index_field]
        edge_2d_field = edge_3d_field1[edge_2d_index_field]
        cell_2d_field = cell_3d_field1[cell_2d_index_field]

        # 2d fields with 1d index fields
        vertex_2d_field = vertex_3d_field1[any_1d_index_field]
        edge_2d_field = edge_3d_field1[any_1d_index_field]
        cell_2d_field = cell_3d_field1[any_1d_index_field]


@stencil
def sparse_index_fields(
    sparse_3d_field1: Field[Edge > Cell > Vertex, K],
    sparse_3d_index_field1: IndexField[Edge > Cell > Vertex, K],
    sparse_2d_index_field1: IndexField[Edge > Cell > Vertex],
    sparse_3d_field2: Field[Cell > Vertex > Cell, K],
    sparse_3d_index_field2: IndexField[Cell > Vertex > Cell, K],
    sparse_2d_index_field2: IndexField[Cell > Vertex > Cell],
    edge_3d_field: Field[Edge, K],
    edge_2d_field: Field[Edge],
    cell_3d_field: Field[Cell, K],
    cell_2d_field: Field[Cell],
):
    with levels_downward[2:50] as levels:
        # 3d sparse field with 3d sparse index field
        edge_3d_field = sum_over(
            Edge > Cell > Vertex, sparse_3d_field1[sparse_3d_index_field1]
        )

        with sparse[Edge > Cell > Vertex]:
            sparse_3d_field1 = edge_3d_field[sparse_3d_index_field1]

        cell_3d_field = max_over(
            Cell > Vertex > Cell, sparse_3d_field2[sparse_3d_index_field2]
        )

        with sparse[Cell > Vertex > Cell]:
            sparse_3d_field2 = cell_3d_field[Cell, sparse_3d_index_field2]

        # 3d sparse field with 2d sparse index field
        edge_3d_field[levels] = min_over(
            Edge > Cell > Vertex, sparse_3d_field1[sparse_2d_index_field1]
        )

        with sparse[Edge > Cell > Vertex]:
            sparse_3d_field1 = edge_3d_field[sparse_2d_index_field1]

        cell_3d_field[levels] = reduce_over(
            Cell > Vertex > Cell, sparse_3d_field2[sparse_2d_index_field2], mul
        )

        with sparse[Cell > Vertex > Cell]:
            sparse_3d_field2 = cell_3d_field[
                Cell > Vertex > Cell, sparse_2d_index_field2
            ]

        # 2d sparse field with 3d sparse index field
        edge_2d_field = sum_over(
            Edge > Cell > Vertex,
            sparse_3d_field1[sparse_3d_index_field1],
            weights=[-1, -2, -3, -4],
        )

        with sparse[Edge > Cell > Vertex]:
            sparse_3d_field1 = edge_2d_field[sparse_3d_index_field1]

        cell_2d_field = sum_over(
            Cell > Vertex > Cell, sparse_3d_field2[sparse_3d_index_field2], init=-10,
        )

        with sparse[Cell > Vertex > Cell]:
            sparse_3d_field2 = cell_2d_field[Cell, sparse_3d_index_field2]

        # 2d sparse field with 2d sparse index field
        edge_2d_field = sum_over(
            Edge > Cell > Vertex,
            sparse_3d_field1[sparse_2d_index_field1],
            init=5,
            weights=[-1, -2, -3, -4],
        )

        with sparse[Edge > Cell > Vertex]:
            sparse_3d_field1 = edge_2d_field[sparse_2d_index_field1]

        cell_2d_field = max_over(
            Cell > Vertex > Cell, sparse_3d_field2[sparse_2d_index_field2]
        )

        with sparse[Cell > Vertex > Cell]:
            sparse_3d_field2 = cell_2d_field[
                Cell > Vertex > Cell, sparse_2d_index_field2
            ]
