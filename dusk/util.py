def pprint_matcher(node):
    print(matcher_to_str(node))


def matcher_to_str(
    node, indent_nr: int = 0, indent: str = "  ", first_line_prefix=None
) -> str:
    ind = indent * indent_nr
    ind1 = indent * (indent_nr + 1)

    if first_line_prefix is None:
        first_line_prefix = ind

    if isinstance(node, type):
        return first_line_prefix + node.__name__ + "\n"
    elif hasattr(node, "_fields"):

        if 0 == len(node._fields):
            return first_line_prefix + type(node).__name__ + "()\n"
        out = ""
        out += first_line_prefix + type(node).__name__ + "(\n"

        for field in node._fields:
            out += matcher_to_str(
                getattr(node, field),
                indent_nr=indent_nr + 1,
                indent=indent,
                first_line_prefix=ind1 + field + " = ",
            )

        out += ind + ")\n"

        return out
    if isinstance(node, list):
        out = ""
        out += first_line_prefix + "[\n"
        for elem in node:
            out += matcher_to_str(elem, indent_nr=indent_nr + 1, indent=indent)
        out += ind + "]\n"

        return out
    else:
        return first_line_prefix + repr(node) + "\n"
