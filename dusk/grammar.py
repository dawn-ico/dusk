from __future__ import annotations
from typing import Any, Optional as _Optional, Callable, List as _List, Dict as _Dict
from ast import *

from dawn4py.serialization.SIR import (
    BuiltinType,
    Field,
    FieldDimensions,
    LocationType,
    VarDeclStmt,
    GlobalVariableValue,
    VerticalRegion,
    Interval,
    Expr as sir_Expr,
    FieldAccessExpr,
)
from dawn4py.serialization.utils import (
    make_stencil,
    make_field,
    make_field_dimensions_unstructured,
    make_ast,
    make_stmt,
    make_block_stmt,
    make_expr_stmt,
    make_assignment_stmt,
    make_if_stmt,
    make_vertical_region_decl_stmt,
    make_vertical_region,
    make_interval,
    make_loop_stmt,
    make_expr,
    make_literal_access_expr,
    make_var_access_expr,
    make_field_access_expr,
    make_unary_operator,
    make_binary_operator,
    make_reduction_over_neighbor_expr,
)

from dusk import (
    DuskSyntaxError,
    match,
    does_match,
    Ignore as _,
    Optional,
    OneOf,
    Capture,
    Repeat,
)
from dusk.script import stencil as stencil_decorator, __LOCATION_TYPES__


# Short cuts
EmptyList = Repeat(_, n=0)
AnyContext = OneOf(Load, Store, Del, AugLoad, AugStore, Param)


def name(id: str, ctx=Load) -> Name:
    return Name(id=id, ctx=ctx)


class Scope:
    def __init__(self, parent: _Optional[Scope] = None) -> None:
        self.symbols = {}
        self.parent = parent

    def has_symbol(self, name: str) -> bool:
        if name in self.symbols.keys():
            return True
        if self.parent is not None:
            return self.parent.has_symbol(name)
        return False

    def fetch(self, name: str):
        if name in self.symbols.keys():
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.fetch(name)
        raise KeyError

    def add(self, name: str, symbol) -> None:
        self.symbols[name] = symbol


class DuskInternalError(Exception):
    def __init__(self, message):
        self.message = message


def transform(matcher) -> Callable:
    def decorator(transformer: Callable) -> Callable:
        def transformer_with_matcher(self, node, *args, **kwargs):
            captures = {}
            match(matcher, node, capturer=captures)
            return transformer(self, *args, **captures, **kwargs)

        return transformer_with_matcher

    return decorator


class Grammar:
    @staticmethod
    def is_stencil(node) -> bool:
        return does_match(
            FunctionDef(
                name=_,
                args=_,
                body=_,
                decorator_list=Repeat(name(stencil_decorator.__name__), n=1),
                returns=_,
                type_comment=_,
            ),
            node,
        )

    def __init__(self):
        # FIXME: scopes & symbols are currently poorly designed
        self.globals = Scope()  # str -> GlobalVariableValue
        self.fields = Scope(self.globals)  # str -> Field
        self.variables = Scope(self.fields)
        self.scope = self.variables

    def add_symbol(self, name, type) -> None:
        if self.scope.has_symbol(name):
            raise DuskSyntaxError(f"Symbol '{name}' delcared twice!", name)
        if isinstance(type, Field):
            self.fields.add(name, type)
        # TODO: global & local variables
        else:
            raise DuskInternalError(
                f"Encountered unknown symbol type '{type}' ('{name}')!"
            )

    def dispatch(self, rules: _Dict[Any, Callable], node):
        for recognizer, rule in rules.items():
            if does_match(recognizer, node):
                return rule(node)
        raise DuskSyntaxError(f"Unrecognized node: '{node}'!", node)

    @transform(
        FunctionDef(
            name=Capture(str).to("name"),
            args=arguments(
                posonlyargs=EmptyList,
                args=Capture(Repeat(arg)).to("fields"),
                vararg=None,
                kwonlyargs=EmptyList,
                kw_defaults=EmptyList,
                kwarg=None,
                defaults=EmptyList,
            ),
            body=Capture(_).to("body"),
            decorator_list=Repeat(name(stencil_decorator.__name__), n=1),
            returns=Optional(Constant(value=None, kind=None)),
            type_comment=None,
        )
    )
    def stencil(self, name: str, body: _List, fields: _List):
        self.fields.symbols.clear()
        self.variables.symbols.clear()
        for field in fields:
            self.field_declaration(field)
        body = make_ast(self.statements(body))
        return make_stencil(name, body, self.fields.symbols.values())

    @transform(
        arg(
            arg=Capture(str).to("name"),
            annotation=Capture(expr).to("type"),
            type_comment=None,
        )
    )
    def field_declaration(self, name: str, type: expr):
        self.add_symbol(name, make_field(name, self.field_type(type)))

    def type(self, node):
        # TODO: built-in types for local variables
        return self.dispatch({Subscript: self.field_type}, node)

    @transform(
        Subscript(
            value=name("Field"),
            slice=Index(value=Capture(_).to("location_chain")),
            ctx=Load,
        )
    )
    def field_type(self, location_chain: Index):
        # TODO: do we need z-masks (last argument below)?
        return make_field_dimensions_unstructured(
            self.location_chain(location_chain), 1
        )

    @transform(
        OneOf(
            name(Capture(str).append("locations")),
            Compare(
                left=name(Capture(str).append("locations")),
                ops=Repeat(Gt),
                comparators=Repeat(name(Capture(str).append("locations"))),
            ),
        )
    )
    def location_chain(self, locations: _List):
        return [self.location_type(location) for location in locations]

    @transform(Capture(str).to("name"))
    def location_type(self, name: str):
        location_names = {l.__name__ for l in __LOCATION_TYPES__}

        if name not in location_names:
            raise DuskSyntaxError(f"Invalid location type '{name}'!", name)
        return LocationType.Value(name)

    @transform(Capture(list).to("py_stmts"))
    def statements(self, py_stmts: _List):
        sir_stmts = []
        for stmt in py_stmts:
            # TODO: bad hardcoded strings
            stmt = self.dispatch(
                {
                    OneOf(Assign, AugAssign, AnnAssign): self.assign,
                    If: self.if_stmt,
                    For(
                        target=_,
                        iter=Subscript(value=name(id="neighbors"), slice=_, ctx=_),
                        body=_,
                        orelse=_,
                        type_comment=_,
                    ): self.loop_stmt,
                    # assume it's a vertical region by default
                    For: self.vertical_loop,
                },
                stmt,
            )
            if stmt is not None:
                sir_stmts.append(stmt)
        return sir_stmts

    @transform(
        OneOf(
            Assign(
                targets=Repeat(Capture(expr).to("lhs"), n=1),
                value=Capture(expr).to("rhs"),
                type_comment=None,
            ),
            AnnAssign(
                target=Capture(expr).to("lhs"),
                value=Capture(Optional(expr)).to("rhs"),
                annotation=Capture(expr).to("decl_type"),
                simple=1,
            ),
        )
    )
    def assign(self, lhs: expr, rhs: expr, decl_type: expr = None):
        if decl_type is not None:
            # TODO: implement locals and temporary fields
            raise NotImplementedError(
                "Variable declarations currently not implemented in stencil bodies!"
            )
            # decl_type = self.type(decl_type)
        if rhs is not None:
            return make_assignment_stmt(self.expression(lhs), self.expression(rhs))

    @transform(
        If(
            test=Capture(expr).to("condition"),
            body=Capture(list).to("body"),
            orelse=Capture(list).to("orelse"),
        )
    )
    def if_stmt(self, condition: expr, body: _List, orelse: _List):

        condition = make_expr_stmt(self.expression(condition))
        body = make_block_stmt(self.statements(body))
        orelse = make_block_stmt(self.statements(orelse))

        return make_if_stmt(condition, body, orelse)

    @transform(
        For(
            target=Name(id=OneOf("k", "_"), ctx=Store),
            # TODO: bad hardcoded strings 'forward' & and 'backward'
            iter=OneOf(
                name(id=Capture(OneOf("forward", "backward")).to("order")),
                Subscript(
                    value=name(id=Capture(OneOf("forward", "backward")).to("order")),
                    slice=Slice(
                        lower=Capture(_).to("lower"),
                        upper=Capture(_).to("upper"),
                        step=None,
                    ),
                    ctx=Load,
                ),
            ),
            body=Capture(_).to("body"),
            orelse=EmptyList,
            type_comment=None,
        )
    )
    def vertical_loop(self, order, body, upper=None, lower=None):

        if lower is None:
            lower_level, lower_offset = Interval.Start, 0
        else:
            lower_level, lower_offset = self.vertical_interval_bound(lower)

        if upper is None:
            upper_level, upper_offset = Interval.End, 0
        else:
            upper_level, upper_offset = self.vertical_interval_bound(upper)

        order_mapper = {
            "forward": VerticalRegion.Forward,
            "backward": VerticalRegion.Backward,
        }
        return make_vertical_region_decl_stmt(
            make_ast(self.statements(body)),
            make_interval(lower_level, upper_level, lower_offset, upper_offset),
            order_mapper[order],
        )

    # TODO: richer vertical interval bounds
    @transform(Capture(OneOf(Constant, UnaryOp)).to("bound"))
    def vertical_interval_bound(self, bound):
        if does_match(Constant(value=int, kind=None), bound):
            return Interval.Start, bound.value
        elif does_match(
            UnaryOp(op=USub, operand=Constant(value=int, kind=None)), bound
        ):
            # FIXME: is this an 'off by one' error?
            return Interval.End, -bound.operand.value
        else:
            raise DuskSyntaxError(
                f"Unrecognized vertical intervals bound '{bound}'!", bound
            )

    @transform(
        For(
            # TODO: bad hardcoded string `neighbors`
            target=Name(id="_", ctx=Store),
            iter=Subscript(
                value=name(id="neighbors"),
                slice=Index(value=Capture(_).to("neighborhood")),
                ctx=Load,
            ),
            body=Capture(_).to("body"),
            orelse=EmptyList,
            type_comment=None,
        )
    )
    def loop_stmt(self, neighborhood, body: _List):
        return make_loop_stmt(self.statements(body), self.location_chain(neighborhood))

    @transform(Capture(expr).to("expr"))
    def expression(self, expr: expr):
        return make_expr(
            self.dispatch(
                {
                    Constant: self.constant,
                    Name: self.var,
                    BinOp: self.binop,
                    UnaryOp: self.unop,
                    Subscript: self.subscript,
                    # TODO: hardcoded string
                    Call(func=name("reduce"), args=_, keywords=_): self.reduction,
                },
                expr,
            )
        )

    @transform(Constant(value=Capture(_).to("value"), kind=None))
    def constant(self, value):
        # TODO: properly distinguish between float and double
        built_in_type_map = {bool: "Boolean", int: "Integer", float: "Double"}

        if type(value) in built_in_type_map.keys():
            return make_literal_access_expr(
                # TODO: does `str` really work here? (what about NaNs, precision, 1e11 notation, etc)
                str(value),
                BuiltinType.TypeID.Value(built_in_type_map[type(value)]),
            )

        raise DuskSyntaxError(
            f"Unsupported constant '{value}' of type '{type(value)}'!", value
        )

    @transform(Name(id=Capture(str).to("name"), ctx=AnyContext))
    def var(self, name: str):

        if not self.scope.has_symbol(name):
            raise DuskSyntaxError(f"Undeclared variable '{name}'!", name)

        type = self.scope.fetch(name)
        # FIXME: what types do we store in the respective scopes?
        if isinstance(type, VarDeclStmt):
            return make_var_access_expr(name)
        elif isinstance(type, GlobalVariableValue):
            return make_var_access_expr(name, is_external=True)
        elif isinstance(type, Field):
            return make_field_access_expr(name)
        else:
            raise DuskInternalError(
                f"Encountered unknown symbol type '{type}' ('{name}')!"
            )

    @transform(
        Subscript(
            value=Capture(expr).to("expr"),
            slice=Index(value=Constant(value=Capture(bool).to("index"), kind=None)),
            ctx=_,
        )
    )
    def subscript(self, expr: expr, index):
        expr = self.expression(expr)

        # TODO: more/better subscript expressions
        if (
            isinstance(expr, sir_Expr)
            and expr.WhichOneof("expr") == "field_access_expr"
        ):
            # TODO: vertical offset
            return make_field_access_expr(expr.field_access_expr.name, [index, 0])
        else:
            raise NotImplementedError(
                f"Indexing is currently only supported for fields (got '{expr}')!"
            )

    @transform(
        UnaryOp(
            operand=Capture(expr).to("expr"), op=Capture(OneOf(UAdd, USub)).to("op")
        )
    )
    def unop(self, expr: expr, op):
        py_unop_to_sir_unop = {UAdd: "+", USub: "-"}
        return make_unary_operator(py_unop_to_sir_unop[type(op)], self.expression(expr))

    @transform(
        BinOp(
            left=Capture(expr).to("left"),
            op=Capture(_).to("op"),
            right=Capture(expr).to("right"),
        )
    )
    def binop(self, left: expr, op: Any, right: expr):
        # TODO: boolean operators
        py_binops_to_sir_binops = {
            Add: "+",
            Sub: "-",
            Mult: "*",
            Div: "/",
            LShift: "<<",
            RShift: ">>",
            BitOr: "|",
            BitXor: "^",
            BitAnd: "&",
        }
        if type(op) not in py_binops_to_sir_binops.keys():
            raise DuskSyntaxError(f"Unsupported binary operator '{op}'!", op)
        op = py_binops_to_sir_binops[type(op)]
        return make_binary_operator(self.expression(left), op, self.expression(right))

    @transform(
        Call(
            func=name("reduce"),
            args=Repeat(Capture(expr).append("args")),
            keywords=EmptyList,
        )
    )
    def reduction(self, args: _List):
        # FIXME: enrich matcher framework, so we can simplify this
        if not 4 <= len(args) <= 5:
            raise DuskSyntaxError(
                f"Reduction takes 4 or 5 arguments, got {len(args)}!", args
            )

        expr, op, init, chain, *weights = args

        if not does_match(Constant(value=str, kind=None), op):
            raise DuskSyntaxError(f"Invalid operator for reduction '{op}'!", op)

        if len(weights) == 1:
            # TODO: `weights.ctx`` should be `Load`
            weights = [self.expression(weight) for weight in weights[0].elts]

        return make_reduction_over_neighbor_expr(
            op.value,
            self.expression(expr),
            self.expression(init),
            self.location_chain(chain),
            weights,
        )
