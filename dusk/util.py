from dusk.ir import concept


# TODO: we should probably move this to `match.py`
def pprint(node, *args, **kwargs):
    print(matcher_to_str(node, *args, **kwargs))


def matcher_to_str(
    node, indent_nr: int = 0, indent: str = "  ", first_line_prefix=None
) -> str:
    ind = indent * indent_nr
    ind1 = indent * (indent_nr + 1)

    if first_line_prefix is None:
        first_line_prefix = ind

    node_kind = concept.get_node_kind(node)
    if node_kind == concept.NodeKind.LEAF:
        if isinstance(node, type):
            return first_line_prefix + node.__name__ + "\n"
        else:
            return first_line_prefix + repr(node) + "\n"
    elif node_kind == concept.NodeKind.STRUCT:

        fields = list(concept.get_struct_fields(node))
        if 0 == len(fields):
            return first_line_prefix + type(node).__name__ + "()\n"
        out = ""
        out += first_line_prefix + type(node).__name__ + "(\n"

        for field in fields:
            out += matcher_to_str(
                getattr(node, field),
                indent_nr=indent_nr + 1,
                indent=indent,
                first_line_prefix=ind1 + field + " = ",
            )

        out += ind + ")\n"

        return out
    else:
        assert node_kind == concept.NodeKind.LIST
        out = ""
        out += first_line_prefix + "[\n"
        for elem in node:
            out += matcher_to_str(elem, indent_nr=indent_nr + 1, indent=indent)
        out += ind + "]\n"

        return out


class DotDict(dict):
    # from https://stackoverflow.com/a/23689767/12958632
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
