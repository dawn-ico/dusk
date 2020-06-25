from __future__ import annotations
import typing as t
from ast import *
from dusk.util import pprint_matcher as pprint

import dawn4py.serialization.SIR as sir
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
    make_ternary_operator,
    make_reduction_over_neighbor_expr,
    make_fun_call_expr,
)

from dusk.match import (
    match,
    does_match,
    Ignore as _,
    Optional,
    OneOf,
    Capture,
    Repeat,
    FixedList,
    BreakPoint,
)
from dusk.semantics import (
    Symbol,
    SymbolKind,
    Field as DuskField,
    VerticalIterationVariable,
    ScopeHelper,
)
from dusk.script import (
    stencil as stencil_decorator,
    __LOCATION_TYPES__,
    __UNARY_MATH_FUNCTIONS__,
    __BINARY_MATH_FUNCTIONS__,
)
from dusk.errors import DuskInternalError, DuskSyntaxError
from dusk.util import pprint_matcher as pprint


# Short cuts
EmptyList = Repeat(_, n=0)
AnyContext = OneOf(Load, Store, Del, AugLoad, AugStore, Param)


def name(id, ctx=Load) -> Name:
    return Name(id=id, ctx=ctx)


def transform(matcher) -> t.Callable:
    def decorator(transformer: t.Callable) -> t.Callable:
        def transformer_with_matcher(self, node, *args, **kwargs):
            captures = {}
            match(matcher, node, capturer=captures)
            return transformer(self, *args, **captures, **kwargs)

        return transformer_with_matcher

    return decorator


def dispatch(rules: t.Dict[t.Any, t.Callable], node):
    for recognizer, rule in rules.items():
        if does_match(recognizer, node):
            return rule(node)
    raise DuskSyntaxError(f"Unrecognized node: '{node}'!", node)


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
        self.scope_helper = ScopeHelper()
        self.neighbor_iterations = []

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
    def stencil(self, name: str, body: t.List, fields: t.List):
        with self.scope_helper.new_scope():
            for field in fields:
                self.field_declaration(field)
            body = make_ast(self.statements(body))
            fields = [
                symbol.sir
                for symbol in self.scope_helper.current_scope
                if isinstance(symbol, DuskField)
            ]
        return make_stencil(name, body, fields)

    @transform(
        arg(
            arg=Capture(str).to("name"),
            annotation=Capture(expr).to("type"),
            type_comment=None,
        )
    )
    def field_declaration(self, name: str, type: expr):
        self.scope_helper.current_scope.add(
            name, DuskField(make_field(name, self.field_type(type)))
        )

    def type(self, node):
        return dispatch({Subscript: self.field_type}, node)

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
    def location_chain(self, locations: t.List):
        return [self.location_type(location) for location in locations]

    @transform(Capture(str).to("name"))
    def location_type(self, name: str):
        location_names = {l.__name__ for l in __LOCATION_TYPES__}

        if name not in location_names:
            raise DuskSyntaxError(f"Invalid location type '{name}'!", name)
        return sir.LocationType.Value(name)

    @transform(Capture(list).to("py_stmts"))
    def statements(self, py_stmts: t.List):
        sir_stmts = []
        for stmt in py_stmts:
            # TODO: bad hardcoded strings
            stmt = dispatch(
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
                    Pass: lambda pass_node: None,
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
    def if_stmt(self, condition: expr, body: t.List, orelse: t.List):

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
            lower_level, lower_offset = sir.Interval.Start, 0
        else:
            lower_level, lower_offset = self.vertical_interval_bound(lower)

        if upper is None:
            upper_level, upper_offset = sir.Interval.End, 0
        else:
            upper_level, upper_offset = self.vertical_interval_bound(upper)

        order_mapper = {
            "forward": sir.VerticalRegion.Forward,
            "backward": sir.VerticalRegion.Backward,
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
            return sir.Interval.Start, bound.value
        elif does_match(
            UnaryOp(op=USub, operand=Constant(value=int, kind=None)), bound
        ):
            # FIXME: is this an 'off by one' error?
            return sir.Interval.End, -bound.operand.value
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
    def loop_stmt(self, neighborhood, body: t.List):
        neighborhood = self.location_chain(neighborhood)

        self.neighbor_iterations.append(neighborhood)
        body = self.statements(body)
        self.neighbor_iterations.pop()

        return make_loop_stmt(body, neighborhood)

    @transform(Capture(expr).to("expr"))
    def expression(self, expr: expr):
        return make_expr(
            dispatch(
                {
                    Constant: self.constant,
                    Name: self.var,
                    Subscript: self.subscript,
                    UnaryOp: self.unop,
                    BinOp: self.binop,
                    BoolOp: self.boolop,
                    Compare: self.compare,
                    IfExp: self.ifexp,
                    Call: self.funcall,
                },
                expr,
            )
        )

    @transform(Constant(value=Capture(_).to("value"), kind=None))
    def constant(self, value):
        # TODO: properly distinguish between float and double
        built_in_type_map = {bool: "Boolean", int: "Integer", float: "Double"}

        if type(value) not in built_in_type_map.keys():
            raise DuskSyntaxError(
                f"Unsupported constant '{value}' of type '{type(value)}'!", value
            )

        _type = sir.BuiltinType.TypeID.Value(built_in_type_map[type(value)])

        if isinstance(value, bool):
            value = "true" if value else "false"
        else:
            # TODO: does `str` really work here? (what about NaNs, precision, 1e11 notation, etc)
            value = str(value)

        return make_literal_access_expr(value, _type,)

    @transform(Name(id=Capture(str).to("name"), ctx=AnyContext))
    def var(self, name: str):

        if not self.scope_helper.current_scope.contains(name):
            raise DuskSyntaxError(f"Undeclared variable '{name}'!", name)

        symbol = self.scope_helper.current_scope.fetch(name)
        if isinstance(symbol, DuskField):
            if len(self.neighbor_iterations) > 0:
                # Inside of neighbor iterations, we use offsets
                # FIXME: add ambiguity check
                # FIXME: implement _smart default_ for horizontal offsets
                return make_field_access_expr(name, [True, 0])
            return make_field_access_expr(name, [False, 0])
        else:
            raise DuskInternalError(
                f"Encountered unknown symbol type '{symbol}' ('{name}')!"
            )

    @transform(
        Subscript(
            value=Capture(expr).to("expr"),
            slice=Index(
                value=OneOf(
                    Tuple(
                        elts=FixedList(
                            Capture(OneOf(Compare, Name)).to("hindex"),
                            Capture(expr).to("vindex"),
                        ),
                        ctx=Load,
                    ),
                    Capture(BinOp).to("vindex"),
                    Capture(name("k")).to("vindex"),
                    Capture(Compare).to("hindex"),
                    Capture(Name).to("hindex"),
                )
            ),
            ctx=AnyContext,
        )
    )
    def subscript(self, expr: expr, hindex: expr = None, vindex: expr = None):
        expr = self.expression(expr)

        if (
            not isinstance(expr, sir.Expr)
            or expr.WhichOneof("expr") != "field_access_expr"
        ):
            raise NotImplementedError(
                f"Indexing is currently only supported for fields (got '{expr}')!"
            )

        vindex = self.relative_vertical_offset(vindex) if vindex is not None else 0

        # detect illegal code, if we are not in an interation space there shouldn't be an h offset
        if len(self.neighbor_iterations) == 0:
            if hindex is not None:
                raise DuskSyntaxError(
                    f"neighbor chain subscripts only allowed inside of an iteration"
                )
            # if we are not in an interation space, h defaults to false and we're done here
            return make_field_access_expr(expr.field_access_expr.name, [False, vindex])

        # possible cases
        # no hor. index is given => default is assumed, i.e. True
        # a chain is given:
        #   - the chain matches the iteration space on top of the stack => True
        #   - the chain does not match the iteartion space on top of the stack:
        #       => check if the situation is ambigous, if not, the code is illegal
        #       otherwise, check if the chain is equal to the first element of the
        #       iteration space on the stack, if so, the offset is set to False,
        #       otherwise, the code is illegal

        neighbor_iteration = self.neighbor_iterations[-1]

        if hindex is None:
            if neighbor_iteration[0] == neighbor_iteration[-1]:  # ambigous case
                raise DuskSyntaxError(
                    f"ambigous case, neighbor chain subscript needs to be given"
                )
            # FIXME: we should check location type of field to get _smart default_
            return make_field_access_expr(expr.field_access_expr.name, [True, vindex])

        # I believe if it's non-ambiguous, hindex can still be given optionally
        hindex = self.location_chain(hindex)
        # FIXME: check if `hindex` is valid for this field's location type

        if len(hindex) == 1:
            if neighbor_iteration[0] != hindex[0]:
                raise DuskSyntaxError(
                    f"neighbor chain subscript does not match start of chain"
                )
            return make_field_access_expr(expr.field_access_expr.name, [False, vindex])

        if hindex != neighbor_iteration:
            raise DuskSyntaxError(f"neighbor chain subscript does not match chain")

        return make_field_access_expr(expr.field_access_expr.name, [True, vindex])

    @transform(
        OneOf(
            BinOp(
                # FIXME: support flexible vertical iteration variables
                left=name("k"),
                op=Capture(OneOf(Add, Sub)).to("vop"),
                right=Constant(value=Capture(int).to("vindex"), kind=None),
            ),
            name("k"),
        ),
    )
    def relative_vertical_offset(self, vindex: int = 0, vop=Add()):
        return -vindex if isinstance(vop, Sub) else vindex

    @transform(
        UnaryOp(
            operand=Capture(expr).to("expr"),
            op=Capture(OneOf(UAdd, USub, Not)).to("op"),
        )
    )
    def unop(self, expr: expr, op):
        py_unop_to_sir_unop = {UAdd: "+", USub: "-", Not: "!"}
        return make_unary_operator(py_unop_to_sir_unop[type(op)], self.expression(expr))

    @transform(
        BinOp(
            left=Capture(expr).to("left"),
            op=Capture(_).to("op"),
            right=Capture(expr).to("right"),
        )
    )
    def binop(self, left: expr, op: t.Any, right: expr):
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
        BoolOp(
            op=Capture(OneOf(And, Or)).to("op"),
            values=Capture(Repeat(expr)).to("values"),
        )
    )
    def boolop(self, op, values: t.List):
        py_boolops_to_sir_boolops = {And: "&&", Or: "||"}
        op = py_boolops_to_sir_boolops[type(op)]

        *remainder, last = values
        binop = self.expression(last)

        for value in reversed(remainder):
            binop = make_binary_operator(self.expression(value), op, binop)

        return binop

    @transform(
        Compare(
            left=Capture(expr).to("left"),
            # currently we only support two operands
            ops=Repeat(Capture(_).to("op"), n=1),
            comparators=Repeat(Capture(expr).to("right"), n=1),
        ),
    )
    def compare(self, left: expr, op, right: expr):
        # FIXME: we should probably have a better answer when we need such mappings
        py_compare_to_sir_compare = {
            Eq: "==",
            NotEq: "!=",
            Lt: "<",
            LtE: "<=",
            Gt: ">",
            GtE: ">=",
        }
        if type(op) not in py_compare_to_sir_compare.keys():
            raise DuskSyntaxError(f"Unsupported comparison operator '{op}'", op)
        op = py_compare_to_sir_compare[type(op)]
        return make_binary_operator(self.expression(left), op, self.expression(right))

    @transform(
        IfExp(
            test=Capture(expr).to("condition"),
            body=Capture(expr).to("body"),
            orelse=Capture(expr).to("orelse"),
        )
    )
    def ifexp(self, condition: expr, body: expr, orelse: expr):

        condition = self.expression(condition)
        body = self.expression(body)
        orelse = self.expression(orelse)

        return make_ternary_operator(condition, body, orelse)

    @transform(
        Capture(Call(func=name(Capture(str).to("name")), args=_, keywords=_,)).to(
            "node"
        )
    )
    def funcall(self, name: str, node: Call):
        # TODO: bad hardcoded string
        if name == "reduce":
            return self.reduction(node)

        if name in self.unary_math_functions or name in self.binary_math_functions:
            return self.math_function(node)

        raise DuskSyntaxError(f"unrecognized function call '{name}'", node)

    unary_math_functions = {f.__name__ for f in __UNARY_MATH_FUNCTIONS__}
    binary_math_functions = {f.__name__ for f in __BINARY_MATH_FUNCTIONS__}

    @transform(
        Call(
            func=name(Capture(str).to("name")),
            args=Capture(list).to("args"),
            keywords=EmptyList,
        )
    )
    def math_function(self, name: str, args: t.List):

        if name in self.unary_math_functions:
            if len(args) != 1:
                raise DuskSyntaxError(f"function '{name}' takes exactly one argument")
            return make_fun_call_expr(
                f"gridtools::dawn::math::{name}", [self.expression(args[0])]
            )

        if name in self.binary_math_functions:
            if len(args) != 2:
                raise DuskSyntaxError(f"function '{name}' takes exactly two arguments")
            return make_fun_call_expr(
                f"gridtools::dawn::math::{name}",
                [self.expression(arg) for arg in args],
            )

        raise DuskSyntaxError(f"unrecognized function call")

    # TODO: bad hardcoded string
    @transform(
        Call(func=name("reduce"), args=Capture(list).to("args"), keywords=EmptyList)
    )
    def reduction(self, args: t.List):
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

        location_chain = self.location_chain(chain)

        self.neighbor_iterations.append(location_chain)
        expr = self.expression(expr)
        self.neighbor_iterations.pop()

        return make_reduction_over_neighbor_expr(
            op.value, expr, self.expression(init), location_chain, weights,
        )
