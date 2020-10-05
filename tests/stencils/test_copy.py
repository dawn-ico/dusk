from dusk.script import *
from test_util import transpile, validate


def test_copy():
    validate(transpile(copy_only_vertex))
    validate(transpile(copy_only_edge))
    validate(transpile(copy_only_cell))
    validate(transpile(copy_all_separate))
    validate(transpile(copy_all_together))


@stencil
def copy_only_vertex(input: Field[Vertex], output: Field[Vertex]):
    with levels_upward:
        output = input


@stencil
def copy_only_edge(input: Field[Edge], output: Field[Edge]):
    with levels_upward:
        output = input


@stencil
def copy_only_cell(input: Field[Cell], output: Field[Cell]):
    with levels_upward:
        output = input


@stencil
def copy_all_separate(
    input_vertex: Field[Vertex],
    output_vertex: Field[Vertex],
    input_edge: Field[Edge],
    output_edge: Field[Edge],
    input_cell: Field[Cell],
    output_cell: Field[Cell],
):
    with levels_upward:
        output_vertex = input_vertex

    with levels_upward:
        output_edge = input_edge

    with levels_upward:
        output_cell = input_cell


@stencil
def copy_all_together(
    input_vertex: Field[Vertex],
    output_vertex: Field[Vertex],
    input_edge: Field[Edge],
    output_edge: Field[Edge],
    input_cell: Field[Cell],
    output_cell: Field[Cell],
):
    with levels_upward:
        output_vertex = input_vertex
        output_edge = input_edge
        output_cell = input_cell
