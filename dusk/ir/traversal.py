import typing

from dusk.ir import concept


def post_order(node: typing.Any) -> typing.Iterator[typing.Any]:
    node_kind = concept.get_node_kind(node)

    if node_kind == concept.NodeKind.LIST:
        for element in node:
            yield from post_order(element)

    elif node_kind == concept.NodeKind.STRUCT:
        for field in concept.get_struct_fields(node):
            yield from post_order(getattr(node, field))
        yield node

    else:
        assert node_kind == concept.NodeKind.LEAF
