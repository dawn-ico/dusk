import typing as t


from ast import AST, expr, stmt


class InternalError(Exception):
    def __init__(self, message=""):
        self.message = message


class ValidationError(InternalError):
    pass


# FIXME: remove `errors.LocationInfo`
class LocationInfo:
    def __init__(
        self, lineno: int, col_offset: int, end_lineno: int, end_col_offset: int
    ) -> None:
        # TODO: filename?
        self.lineno = lineno
        self.col_offset = col_offset
        self.end_lineno = end_lineno
        self.end_col_offset = end_col_offset

    @classmethod
    def from_node(cls, node: AST):
        return cls(node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)

    def __str__(self):
        return f"Line: {self.lineno} - {self.end_lineno}; Col: {self.col_offset} - {self.end_col_offset}"


class ASTError(Exception):
    def __init__(
        self,
        message: str,
        node: t.Optional[AST] = None,
        loc: t.Optional[LocationInfo] = None,
    ) -> None:
        self.message = message
        self.node = node
        self.loc = loc
        if loc is None and isinstance(node, (stmt, expr)):
            self.loc_from_node(node)

    def loc_from_node(self, node):
        assert isinstance(node, (stmt, expr))
        if self.loc is None:
            self.loc = LocationInfo.from_node(node)

    def __str__(self):
        return f"{type(self).__name__}: {self.message}\nat {self.loc}\n({self.node})"


class SyntaxError(ASTError):
    # marker class
    pass


class SemanticError(ASTError):
    # marker class
    pass
