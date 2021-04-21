from typing import Type, Any, Iterable, Dict

import enum
import functools


@enum.unique
class NodeKind(enum.Enum):
    # This is where the AST traversal stops
    LEAF = enum.auto()
    # Should implement `get_struct_fields` so that each field is an attribute
    # Should implement `get_struct_field_types`
    STRUCT = enum.auto()
    # Should be a `Sequence`
    LIST = enum.auto()


# TODO: dispatching on type is good, but maybe these shouldn't depend
# on the instances?


@functools.singledispatch
def get_node_kind(node: Any) -> NodeKind:
    return NodeKind.LEAF


# requires `get_node_kind(node) == NodeKind.STRUCT`
@functools.singledispatch
def get_struct_fields(node: Any) -> Iterable[str]:
    raise NotImplementedError


def iter_children(node: Any) -> Iterable[Any]:
    node_kind = get_node_kind(node)
    if NodeKind.LEAF == node_kind:
        yield from ()
    elif NodeKind.LIST == node_kind:
        yield from node
    elif NodeKind.STRUCT == node_kind:
        for field in get_struct_fields(node):
            yield getattr(node, field)
    else:
        assert False


# requires `get_node_kind(node) == NodeKind.STRUCT`
@functools.singledispatch
def get_struct_field_types(node: Any) -> Dict[str, Type]:
    raise NotImplementedError
