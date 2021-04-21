import inspect
import typing

from dusk import errors
from dusk.ir import concept


class Typed:
    _child_types: typing.ClassVar[typing.Dict[str, typing.Type]]


@concept.get_struct_field_types.register
def get_typed_field_types(node: Typed) -> typing.Dict[str, typing.Type]:
    return node._child_types


def type_check(instance: typing.Any, type_hint: typing.Type) -> None:
    # we only cover the few cases we need here
    # would be nice if we could off-load this to a library
    origin = typing.get_origin(type_hint)
    args = typing.get_args(type_hint)

    if origin is None:
        if type_hint is typing.Any:
            return
        if not isinstance(instance, type_hint):
            raise errors.ValidationError(
                f"Type '{type(instance)}' is no subtype of '{type_hint}' ('{instance}')!"
            )

    # maybe we should find a better way to dispatch the various cases

    elif origin is typing.Union:
        # this also covers `typing.Optional`
        if not any(does_type_check(instance, option) for option in args):
            raise errors.ValidationError(
                f"Type '{type(instance)}' is no subtype of any of '{args}' ('{instance}')!"
            )

    elif inspect.isclass(origin) and issubclass(origin, list):
        if not isinstance(instance, origin):
            raise errors.ValidationError(
                f"Type '{type(instance)}' is no subtype of '{origin}' ('{instance}')!"
            )
        assert 1 == len(args)
        for element in instance:
            type_check(element, args[0])

    else:
        raise NotImplementedError


def does_type_check(instance: typing.Any, type_hint: typing.Type) -> bool:
    try:
        type_check(instance, type_hint)
        return True
    except errors.ValidationError:
        return False


def type_check_struct_node(node: typing.Any) -> None:
    assert concept.get_node_kind(node) == concept.NodeKind.STRUCT

    type_hints = concept.get_struct_field_types(node)

    for field in concept.get_struct_fields(node):
        type_check(getattr(node, field), type_hints[field])
