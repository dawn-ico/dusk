import typing as t


from ast import AST, expr, stmt


class DuskInternalError(Exception):
    def __init__(self, message):
        self.message = message


class LocationInfo:
    def __init__(
        self, lineno: int, col_offset: int, end_lineno: int, end_col_offset: int
    ) -> None:
        self.lineno = lineno
        self.col_offset = col_offset
        self.end_lineno = end_lineno
        self.end_col_offset = end_col_offset

    @classmethod
    def from_node(cls, node: AST):
        return cls(node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)


class DuskSyntaxError(Exception):
    # maybe need more fine grained error hierarchy for, e.g., semantic errors
    # TODO: we should probably have matcher errors vs dusk syntax errors
    def __init__(
        self,
        text: str,
        node: t.Optional[AST] = None,
        loc: t.Optional[LocationInfo] = None,
    ) -> None:
        self.text = text
        self.node = node
        self.loc = loc
        if loc is None and isinstance(node, (stmt, expr)):
            self.loc_from_node(node)

    def loc_from_node(self, node):
        assert isinstance(node, (stmt, expr))
        if self.loc is None:
            self.loc = LocationInfo.from_node(node)

