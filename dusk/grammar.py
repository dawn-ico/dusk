from __future__ import annotations
import typing as t
from ast import *

import dawn4py.serialization.SIR as sir
from dawn4py.serialization.utils import (
    make_stencil,
    make_field,
    make_field_dimensions_unstructured,
    make_field_dimensions_vertical,
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
    make_unstructured_field_access_expr,
    make_unstructured_offset,
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
    IndexField as DuskIndexField,
    VerticalIterationVariable,
    DuskContextHelper,
)
from dusk.script import stencil as stencil_decorator
from dusk.script.stubs import (
    LOCATION_TYPES,
    UNARY_MATH_FUNCTIONS,
    BINARY_MATH_FUNCTIONS,
)
from dusk.errors import DuskInternalError, DuskSyntaxError
from dusk.util import pprint_matcher as pprint


# Short cuts
EmptyList = FixedList()
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
                decorator_list=FixedList(name(stencil_decorator.__name__)),
                returns=_,
                type_comment=_,
            ),
            node,
        )

    def __init__(self):
        self.ctx = DuskContextHelper()

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
            decorator_list=FixedList(name(stencil_decorator.__name__)),
            returns=Optional(Constant(value=None, kind=None)),
            type_comment=None,
        )
    )
    def stencil(self, name: str, body: t.List, fields: t.List):
        with self.ctx.scope.new_scope():
            for field in fields:
                self.field_declaration(field)
            body = make_ast(self.statements(body, in_stencil_root_scope=True))
            fields = [
                symbol.sir
                for symbol in self.ctx.scope.current_scope
                if isinstance(symbol, (DuskField, DuskIndexField))
            ]
        return make_stencil(name, body, fields)

    @transform(
        arg(
            arg=Capture(str).to("name"),
            annotation=Capture(expr).to("field_type"),
            type_comment=None,
        )
    )
    def field_declaration(self, name: str, field_type: expr):
        self.add_field_declaration(name, field_type)

    @transform(
        AnnAssign(
            target=name(Capture(str).to("name"), ctx=Store),
            value=None,
            annotation=Capture(expr).to("field_type"),
            simple=1,
        ),
    )
    def temporary_field_declaration(self, name: str, field_type: expr):
        self.add_field_declaration(name, field_type, is_temporary=True)

    def add_field_declaration(
        self, name: str, field_type: expr, is_temporary: bool = False
    ):
        field_type, hindex, vindex = self.field_type(field_type)

        assert field_type in {"Field", "IndexField"}
        DuskFieldType = DuskField if field_type == "Field" else DuskIndexField

        if hindex is not None:
            dimensions = make_field_dimensions_unstructured(hindex, vindex)
        else:
            dimensions = make_field_dimensions_vertical()

        self.ctx.scope.current_scope.add(
            name, DuskFieldType(make_field(name, dimensions, is_temporary))
        )

    @transform(
        Subscript(
            # TODO: hardcoded string
            value=name(Capture(OneOf("Field", "IndexField")).to("field_type")),
            slice=Index(
                value=OneOf(
                    Tuple(
                        elts=FixedList(
                            Capture(_).to("hindex"), name(Capture("K").to("vindex")),
                        ),
                        ctx=Load,
                    ),
                    name(Capture("K").to("vindex")),
                    Capture(_).to("hindex"),
                ),
            ),
            ctx=Load,
        )
    )
    def field_type(self, field_type: str, hindex: expr = None, vindex: str = None):
        return (
            field_type,
            self.location_chain(hindex) if hindex is not None else None,
            1 if vindex is not None else 0,
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
        location_names = {l.__name__ for l in LOCATION_TYPES}

        if name not in location_names:
            raise DuskSyntaxError(f"Invalid location type '{name}'!", name)
        return sir.LocationType.Value(name)

    @transform(Capture(list).to("py_stmts"))
    def statements(self, py_stmts: t.List, in_stencil_root_scope: bool = False):
        sir_stmts = []
        for stmt in py_stmts:
            if in_stencil_root_scope and isinstance(stmt, AnnAssign):
                self.temporary_field_declaration(stmt)
                continue

            # TODO: bad hardcoded strings
            stmt = dispatch(
                {
                    OneOf(Assign, AugAssign): self.assign,
                    If: self.if_stmt,
                    With(
                        items=FixedList(
                            withitem(
                                context_expr=Subscript(
                                    value=name("sparse"), slice=_, ctx=_
                                ),
                                optional_vars=_,
                            )
                        ),
                        body=_,
                        type_comment=_,
                    ): self.loop_stmt,
                    # assume a vertical region by default
                    With: self.vertical_loop,
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
                targets=FixedList(Capture(expr).to("lhs")),
                value=Capture(expr).to("rhs"),
                type_comment=None,
            ),
            AugAssign(
                target=Capture(expr).to("lhs"),
                op=Capture(operator).to("op"),
                value=Capture(expr).to("rhs"),
            ),
        ),
    )
    def assign(self, lhs: expr, rhs: expr, op: t.Optional[operator] = None):

        py_assign_op_to_sir_assign_op = {
            Add: "+=",
            Sub: "-=",
            Mult: "*=",
            Div: "/=",
            Mod: "%=",
            LShift: "<<=",
            RShift: ">>=",
            BitOr: "|=",
            BitXor: "^=",
            BitAnd: "&=",
        }

        if op is None:
            op = "="

        elif isinstance(op, Pow):
            op = "="
            rhs = make_fun_call_expr(
                "gridtools::dawn::math::pow",
                [self.expression(lhs), self.expression(rhs)],
            )
            return make_assignment_stmt(self.expression(lhs), rhs, op)

        elif type(op) in py_assign_op_to_sir_assign_op.keys():
            op = py_assign_op_to_sir_assign_op[type(op)]

        else:
            raise DuskSyntaxError(f"Unsupported assignment operator '{op}'!", op)

        return make_assignment_stmt(self.expression(lhs), self.expression(rhs), op)

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
        With(
            items=FixedList(
                # TODO: hardcoded strings
                withitem(
                    context_expr=OneOf(
                        name(
                            Capture(OneOf("levels_upward", "levels_downward")).to(
                                "order"
                            ),
                        ),
                        Subscript(
                            value=name(
                                id=Capture(
                                    OneOf("levels_upward", "levels_downward")
                                ).to("order")
                            ),
                            slice=Slice(
                                lower=Capture(_).to("lower"),
                                upper=Capture(_).to("upper"),
                                step=None,
                            ),
                            ctx=Load,
                        ),
                    ),
                    optional_vars=Optional(name(Capture(str).to("var"), ctx=Store)),
                ),
            ),
            body=Capture(_).to("body"),
            type_comment=None,
        ),
    )
    def vertical_loop(self, order, body, upper=None, lower=None, var: str = None):

        if lower is None:
            lower_level, lower_offset = sir.Interval.Start, 0
        else:
            lower_level, lower_offset = self.vertical_interval_bound(lower)

        if upper is None:
            upper_level, upper_offset = sir.Interval.End, 0
        else:
            upper_level, upper_offset = self.vertical_interval_bound(upper)

        order_mapper = {
            "levels_upward": sir.VerticalRegion.Forward,
            "levels_downward": sir.VerticalRegion.Backward,
        }
        with self.ctx.vertical_region(var):
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
            return sir.Interval.End, -bound.operand.value
        else:
            raise DuskSyntaxError(
                f"Unrecognized vertical intervals bound '{bound}'!", bound
            )

    @transform(
        With(
            items=FixedList(
                # TODO: bad hardcoded string `neighbors`
                withitem(
                    context_expr=Subscript(
                        value=name(id="sparse"),
                        slice=Index(value=Capture(_).to("neighborhood")),
                        ctx=Load,
                    ),
                    optional_vars=None,
                )
            ),
            body=Capture(_).to("body"),
            type_comment=None,
        )
    )
    def loop_stmt(self, neighborhood, body: t.List):
        neighborhood = self.location_chain(neighborhood)

        with self.ctx.location.loop_stmt(neighborhood):
            body = self.statements(body)

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
    def var(self, name: str, index: expr = None):

        if not self.ctx.scope.current_scope.contains(name):
            raise DuskSyntaxError(f"Undeclared variable '{name}'!", name)

        symbol = self.ctx.scope.current_scope.fetch(name)
        if isinstance(symbol, DuskField):
            return self.field_access_expr(symbol, index)
        else:
            raise DuskInternalError(
                f"Encountered unknown symbol type '{symbol}' ('{name}')!"
            )

    @transform(
        Subscript(
            value=Capture(Name).to("var"),
            slice=Index(value=Capture(expr).to("index")),
            ctx=AnyContext,
        )
    )
    def subscript(self, var: expr, index: expr):
        return self.var(var, index=index)

    def field_access_expr(self, field: DuskField, index: expr = None):
        if not self.ctx.location.in_vertical_region:
            raise DuskSyntaxError(
                f"Invalid field access {name} outside of a vertical region!"
            )
        return make_unstructured_field_access_expr(
            field.sir.name, *self.field_index(index, field=field)
        )

    @transform(
        OneOf(
            Tuple(
                elts=FixedList(
                    Capture(OneOf(Compare, Name)).to("hindex"),
                    Capture(expr).to("vindex"),
                ),
                ctx=Load,
            ),
            # FIXME: ensure built-ins (like `Edge`) aren't _shadowed_ by variables
            # TODO: hardcoded string
            Capture(OneOf(Compare, name(OneOf("Edge", "Cell", "Vertex")))).to("hindex"),
            Capture(expr).to("vindex"),
            None,
        )
    )
    def field_index(self, field: DuskField, vindex=None, hindex=None):

        voffset, vbase = (
            self.relative_vertical_offset(vindex) if vindex is not None else (0, None)
        )
        hindex = self.location_chain(hindex) if hindex is not None else None

        if not self.ctx.location.in_neighbor_iteration:
            if hindex is not None:
                raise DuskSyntaxError(
                    f"Invalid horizontal index for field '{field.sir.name}' "
                    "outside of neighbor iteration!"
                )
            return make_unstructured_offset(False), voffset, vbase

        neighbor_iteration = self.ctx.location.current_neighbor_iteration
        field_dimension = self.ctx.location.get_field_dimension(field.sir)

        # TODO: `vindex` is _non-sensical_ if the field is 2d

        # TODO: we should check that `field_dimension` is valid for
        #       the current neighbor iteration(s?)

        if hindex is None:
            if self.ctx.location.is_dense(field_dimension):
                if self.ctx.location.is_ambiguous(neighbor_iteration):
                    raise DuskSyntaxError(
                        f"Field '{field.sir.name}' requires a horizontal index "
                        "inside of ambiguous neighbor iteration!"
                    )

                return (
                    make_unstructured_offset(
                        field_dimension[0] == neighbor_iteration[-1]
                    ),
                    voffset,
                    vbase,
                )
            if self.ctx.location.is_dense(field_dimension):
                return make_unstructured_offset(True), voffset, vbase
            else:
                return make_unstructured_offset(False), voffset, vbase

        # TODO: check if `hindex` is valid for this field's location type

        if len(hindex) == 1:
            if neighbor_iteration[0] != hindex[0]:
                raise DuskSyntaxError(
                    f"Invalid horizontal offset for field '{field.sir.name}'!"
                )
            return make_unstructured_offset(False), voffset, vbase

        if hindex != neighbor_iteration:
            raise DuskSyntaxError(
                f"Invalid horizontal offset for field '{field.sir.name}'!"
            )

        if not self.ctx.location.is_dense(field_dimension):
            raise DuskSyntaxError(
                f"Invalid horizontal offset for field '{field.sir.name}'!"
                "sparse fields do not take an offset (only non-offset read makes sense)"
            )
        
        return make_unstructured_offset(True), voffset, vbase        

    @transform(
        OneOf(
            BinOp(
                left=name(Capture(str).to("base")),
                op=Capture(OneOf(Add, Sub)).to("vop"),
                right=Constant(value=Capture(int).to("shift"), kind=None),
            ),
            name(Capture(str).to("base")),
        ),
    )
    def relative_vertical_offset(self, base: str, shift: int = 0, vop=Add()):
        base = self.ctx.scope.current_scope.fetch(base)

        if not isinstance(base, (VerticalIterationVariable, DuskIndexField)):
            raise DuskSyntaxError(
                f"'{base}' isn't a vertical iteration variable or index field!", base
            )
        if isinstance(base, DuskIndexField):
            # TODO: check that `base` is valid in this context
            #       * compatible neighbor iteration
            #       * _correct_ usage (not clear what this entails)
            base = base.sir.name
            if (
                self.ctx.location.in_neighbor_iteration
                and self.ctx.location.is_ambiguous(
                    self.ctx.location.current_neighbor_iteration
                )
            ):
                raise DuskSyntaxError(
                    f"Index field {base} used in ambiguous neighbor iteration!"
                )
        elif isinstance(base, VerticalIterationVariable):
            base = None
        else:
            assert False

        return (-shift if isinstance(vop, Sub) else shift), base

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
            op=Capture(operator).to("op"),
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

        if type(op) in py_binops_to_sir_binops.keys():
            op = py_binops_to_sir_binops[type(op)]
            return make_binary_operator(
                self.expression(left), op, self.expression(right)
            )

        elif isinstance(op, Pow):
            return make_fun_call_expr(
                "gridtools::dawn::math::pow",
                [self.expression(left), self.expression(right)],
            )

        else:
            raise DuskSyntaxError(f"Unsupported binary operator '{op}'!", op)

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
            ops=FixedList(Capture(_).to("op")),
            comparators=FixedList(Capture(expr).to("right")),
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
            raise DuskSyntaxError(f"Unsupported comparison operator '{op}'!", op)
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
        if name == "reduce_over":
            return self.reduce_over(node)

        if name in {"sum_over", "min_over", "max_over"}:
            return self.short_reduce_over(node)

        if name in self.unary_math_functions or name in self.binary_math_functions:
            return self.math_function(node)

        raise DuskSyntaxError(f"Unrecognized function call '{name}'!", node)

    unary_math_functions = {f.__name__ for f in UNARY_MATH_FUNCTIONS}
    binary_math_functions = {f.__name__ for f in BINARY_MATH_FUNCTIONS}

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
                raise DuskSyntaxError(f"Function '{name}' takes exactly one argument!")

            if name == "abs":
                name = "fabs"

            return make_fun_call_expr(
                f"gridtools::dawn::math::{name}", [self.expression(args[0])]
            )

        if name in self.binary_math_functions:
            if len(args) != 2:
                raise DuskSyntaxError(f"Function '{name}' takes exactly two arguments!")
            return make_fun_call_expr(
                f"gridtools::dawn::math::{name}",
                [self.expression(arg) for arg in args],
            )

        raise DuskSyntaxError(f"Unrecognized function call '{name}'!")

    @transform(
        Call(
            # TODO: bad hardcoded string
            func=name("reduce_over"),
            args=FixedList(
                Capture(expr).to("neighborhood"),
                Capture(expr).to("expr"),
                name(Capture(str).to("op")),
            ),
            keywords=Repeat(
                keyword(
                    arg=Capture(str).append("kwargs_keys"),
                    value=Capture(expr).append("kwargs_values"),
                )
            ),
        ),
    )
    def reduce_over(
        self,
        expr: expr,
        neighborhood: expr,
        op: str,
        kwargs_keys: t.List[str] = [],
        kwargs_values: t.List[expr] = [],
    ):
        return self.reduction(expr, neighborhood, op, kwargs_keys, kwargs_values)

    @transform(
        Call(
            func=name(
                # TODO: bad hardcoded string
                Capture(OneOf("sum_over", "min_over", "max_over")).to("short_cut_name")
            ),
            args=FixedList(Capture(expr).to("neighborhood"), Capture(expr).to("expr"),),
            keywords=Repeat(
                keyword(
                    arg=Capture(str).append("kwargs_keys"),
                    value=Capture(expr).append("kwargs_values"),
                )
            ),
        ),
    )
    def short_reduce_over(
        self,
        expr: expr,
        neighborhood: expr,
        short_cut_name: str,
        kwargs_keys: t.List[str] = [],
        kwargs_values: t.List[expr] = [],
    ):
        short_cut_to_op_map = {"sum_over": "sum", "min_over": "min", "max_over": "max"}
        op = short_cut_to_op_map[short_cut_name]

        return self.reduction(expr, neighborhood, op, kwargs_keys, kwargs_values)

    def reduction(
        self,
        expr: expr,
        neighborhood: expr,
        op: str,
        kwargs_keys: t.List[str],
        kwargs_values: t.List[expr],
    ):
        kwargs = dict(zip(kwargs_keys, kwargs_values))
        assert len(kwargs) == len(kwargs_keys) == len(kwargs_values)

        # TODO: what about these hard coded strings?
        wrong_kwargs = kwargs.keys() - {"init", "weights"}
        if 0 < len(wrong_kwargs):
            raise DuskSyntaxError(f"Unsupported kwargs '{wrong_kwargs}' in reduction!")

        neighborhood = self.location_chain(neighborhood)
        with self.ctx.location.reduction(neighborhood):
            expr = self.expression(expr)

        op_map = {"sum": "+", "mul": "*", "min": "min", "max": "max"}
        if not op in op_map:
            raise DuskSyntaxError(f"Invalid operator '{op}' for reduction!")

        if "init" in kwargs:
            init = self.expression(kwargs["init"])
        else:
            # TODO: "min" and "max" are still kinda stupid
            # we should use something like this:
            # https://en.cppreference.com/w/cpp/types/numeric_limits/max
            # the current solution is:
            #   - appropriate for doubles
            #   - okish for floats (may trip floating point exceptions but correct outcome)
            #   - breaks for int (undefined behavior!)
            init_map = {
                "sum": "0",
                "mul": "1",
                "min": "1.79769313486231571e+308",
                "max": "-1.79769313486231571e+308",
            }
            init = make_literal_access_expr(
                init_map[op], sir.BuiltinType.TypeID.Value("Double")
            )

        op = op_map[op]

        weights = None
        if "weights" in kwargs:
            # TODO: check for `kwargs["weight"].ctx == Load`?
            weights = [self.expression(weight) for weight in kwargs["weights"].elts]

        return make_reduction_over_neighbor_expr(op, expr, init, neighborhood, weights,)
