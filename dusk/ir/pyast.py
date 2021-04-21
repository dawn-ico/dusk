from __future__ import annotations

import typing
import ast
import inspect


from dusk.ir import concept, type_checking, annotatable, loc, ast_list


class ASTBase(loc.LocationInfo, annotatable.Annotatable, type_checking.Typed):
    # here we can inject base classes
    pass


T = typing.TypeVar("T")


class ASTListBase(loc.LocationInfo, ast_list.ASTList[T], typing.Generic[T]):
    # here we can inject base classes
    pass


class AST(ASTBase, ast.AST):
    pass


class mod(AST, ast.mod):
    pass


class Module(mod, ast.Module):
    body: ASTListBase[stmt]
    type_ignores: ASTListBase[type_ignore]


class Interactive(mod, ast.Interactive):
    body: ASTListBase[stmt]


class Expression(mod, ast.Expression):
    body: expr


class FunctionType(mod, ast.FunctionType):
    argtypes: ASTListBase[expr]
    returns: expr


class Suite(mod, ast.Suite):
    body: ASTListBase[stmt]


class stmt(AST, ast.stmt):
    pass


class FunctionDef(stmt, ast.FunctionDef):
    name: str
    args: arguments
    body: ASTListBase[stmt]
    decorator_list: ASTListBase[expr]
    returns: typing.Optional[expr]
    type_comment: typing.Optional[str]


class AsyncFunctionDef(stmt, ast.AsyncFunctionDef):
    name: str
    args: arguments
    body: ASTListBase[stmt]
    decorator_list: ASTListBase[expr]
    returns: typing.Optional[expr]
    type_comment: typing.Optional[str]


class ClassDef(stmt, ast.ClassDef):
    name: str
    bases: ASTListBase[expr]
    keywords: ASTListBase[keyword]
    body: ASTListBase[stmt]
    decorator_list: ASTListBase[expr]


class Return(stmt, ast.Return):
    value: typing.Optional[expr]


class Delete(stmt, ast.Delete):
    targets: ASTListBase[expr]


class Assign(stmt, ast.Assign):
    targets: ASTListBase[expr]
    value: expr
    type_comment: typing.Optional[str]


class AugAssign(stmt, ast.AugAssign):
    target: expr
    op: operator
    value: expr


class AnnAssign(stmt, ast.AnnAssign):
    target: expr
    annotation: expr
    value: typing.Optional[expr]
    simple: int


class For(stmt, ast.For):
    target: expr
    iter: expr
    body: ASTListBase[stmt]
    orelse: ASTListBase[stmt]
    type_comment: typing.Optional[str]


class AsyncFor(stmt, ast.AsyncFor):
    target: expr
    iter: expr
    body: ASTListBase[stmt]
    orelse: ASTListBase[stmt]
    type_comment: typing.Optional[str]


class While(stmt, ast.While):
    test: expr
    body: ASTListBase[stmt]
    orelse: ASTListBase[stmt]


class If(stmt, ast.If):
    test: expr
    body: ASTListBase[stmt]
    orelse: ASTListBase[stmt]


class With(stmt, ast.With):
    items: ASTListBase[withitem]
    body: ASTListBase[stmt]
    type_comment: typing.Optional[str]


class AsyncWith(stmt, ast.AsyncWith):
    items: ASTListBase[withitem]
    body: ASTListBase[stmt]
    type_comment: typing.Optional[str]


class Raise(stmt, ast.Raise):
    exc: typing.Optional[expr]
    cause: typing.Optional[expr]


class Try(stmt, ast.Try):
    body: ASTListBase[stmt]
    handlers: ASTListBase[excepthandler]
    orelse: ASTListBase[stmt]
    finalbody: ASTListBase[stmt]


class Assert(stmt, ast.Assert):
    test: expr
    msg: typing.Optional[expr]


class Import(stmt, ast.Import):
    names: ASTListBase[alias]


class ImportFrom(stmt, ast.ImportFrom):
    module: typing.Optional[str]
    names: ASTListBase[alias]
    level: typing.Optional[int]


class Global(stmt, ast.Global):
    names: ASTListBase[str]


class Nonlocal(stmt, ast.Nonlocal):
    names: ASTListBase[str]


class Expr(stmt, ast.Expr):
    value: expr


class Pass(stmt, ast.Pass):
    pass


class Break(stmt, ast.Break):
    pass


class Continue(stmt, ast.Continue):
    pass


class expr(AST, ast.expr):
    pass


class BoolOp(expr, ast.BoolOp):
    op: boolop
    values: ASTListBase[expr]


class NamedExpr(expr, ast.NamedExpr):
    target: expr
    value: expr


class BinOp(expr, ast.BinOp):
    left: expr
    op: operator
    right: expr


class UnaryOp(expr, ast.UnaryOp):
    op: unaryop
    operand: expr


class Lambda(expr, ast.Lambda):
    args: arguments
    body: expr


class IfExp(expr, ast.IfExp):
    test: expr
    body: expr
    orelse: expr


class Dict(expr, ast.Dict):
    keys: ASTListBase[expr]
    values: ASTListBase[expr]


class Set(expr, ast.Set):
    elts: ASTListBase[expr]


class ListComp(expr, ast.ListComp):
    elt: expr
    generators: ASTListBase[comprehension]


class SetComp(expr, ast.SetComp):
    elt: expr
    generators: ASTListBase[comprehension]


class DictComp(expr, ast.DictComp):
    key: expr
    value: expr
    generators: ASTListBase[comprehension]


class GeneratorExp(expr, ast.GeneratorExp):
    elt: expr
    generators: ASTListBase[comprehension]


class Await(expr, ast.Await):
    value: expr


class Yield(expr, ast.Yield):
    value: typing.Optional[expr]


class YieldFrom(expr, ast.YieldFrom):
    value: expr


class Compare(expr, ast.Compare):
    left: expr
    ops: ASTListBase[cmpop]
    comparators: ASTListBase[expr]


class Call(expr, ast.Call):
    func: expr
    args: ASTListBase[expr]
    keywords: ASTListBase[keyword]


class FormattedValue(expr, ast.FormattedValue):
    value: expr
    conversion: typing.Optional[int]
    format_spec: typing.Optional[expr]


class JoinedStr(expr, ast.JoinedStr):
    values: ASTListBase[expr]


class Constant(expr, ast.Constant):
    value: typing.Any
    kind: typing.Optional[str]


class Attribute(expr, ast.Attribute):
    value: expr
    attr: str
    ctx: expr_context


class Subscript(expr, ast.Subscript):
    value: expr
    slice: slice
    ctx: expr_context


class Starred(expr, ast.Starred):
    value: expr
    ctx: expr_context


class Name(expr, ast.Name):
    id: str
    ctx: expr_context


class List(expr, ast.List):
    elts: ASTListBase[expr]
    ctx: expr_context


class Tuple(expr, ast.Tuple):
    elts: ASTListBase[expr]
    ctx: expr_context


class expr_context(AST, ast.expr_context):
    pass


class Load(expr_context, ast.Load):
    pass


class Store(expr_context, ast.Store):
    pass


class Del(expr_context, ast.Del):
    pass


class AugLoad(expr_context, ast.AugLoad):
    pass


class AugStore(expr_context, ast.AugStore):
    pass


class Param(expr_context, ast.Param):
    pass


class slice(AST, ast.slice):
    pass


class Slice(slice, ast.Slice):
    lower: typing.Optional[expr]
    upper: typing.Optional[expr]
    step: typing.Optional[expr]


class ExtSlice(slice, ast.ExtSlice):
    dims: ASTListBase[slice]


class Index(slice, ast.Index):
    value: expr


class boolop(AST, ast.boolop):
    pass


class And(boolop, ast.And):
    pass


class Or(boolop, ast.Or):
    pass


class operator(AST, ast.operator):
    pass


class Add(operator, ast.Add):
    pass


class Sub(operator, ast.Sub):
    pass


class Mult(operator, ast.Mult):
    pass


class MatMult(operator, ast.MatMult):
    pass


class Div(operator, ast.Div):
    pass


class Mod(operator, ast.Mod):
    pass


class Pow(operator, ast.Pow):
    pass


class LShift(operator, ast.LShift):
    pass


class RShift(operator, ast.RShift):
    pass


class BitOr(operator, ast.BitOr):
    pass


class BitXor(operator, ast.BitXor):
    pass


class BitAnd(operator, ast.BitAnd):
    pass


class FloorDiv(operator, ast.FloorDiv):
    pass


class unaryop(AST, ast.unaryop):
    pass


class Invert(unaryop, ast.Invert):
    pass


class Not(unaryop, ast.Not):
    pass


class UAdd(unaryop, ast.UAdd):
    pass


class USub(unaryop, ast.USub):
    pass


class cmpop(AST, ast.cmpop):
    pass


class Eq(cmpop, ast.Eq):
    pass


class NotEq(cmpop, ast.NotEq):
    pass


class Lt(cmpop, ast.Lt):
    pass


class LtE(cmpop, ast.LtE):
    pass


class Gt(cmpop, ast.Gt):
    pass


class GtE(cmpop, ast.GtE):
    pass


class Is(cmpop, ast.Is):
    pass


class IsNot(cmpop, ast.IsNot):
    pass


class In(cmpop, ast.In):
    pass


class NotIn(cmpop, ast.NotIn):
    pass


class excepthandler(AST, ast.excepthandler):
    pass


class ExceptHandler(excepthandler, ast.ExceptHandler):
    type: typing.Optional[expr]
    name: typing.Optional[str]
    body: ASTListBase[stmt]


class type_ignore(AST, ast.type_ignore):
    pass


class TypeIgnore(type_ignore, ast.TypeIgnore):
    lineno: int
    tag: str


class comprehension(AST, ast.comprehension):
    target: expr
    iter: expr
    ifs: ASTListBase[expr]
    is_async: int


class arguments(AST, ast.arguments):
    posonlyargs: ASTListBase[arg]
    args: ASTListBase[arg]
    vararg: typing.Optional[arg]
    kwonlyargs: ASTListBase[arg]
    kw_defaults: ASTListBase[expr]
    kwarg: typing.Optional[arg]
    defaults: ASTListBase[expr]


class arg(AST, ast.arg):
    arg: str
    annotation: typing.Optional[expr]
    type_comment: typing.Optional[str]


class keyword(AST, ast.keyword):
    arg: typing.Optional[str]
    value: expr


class alias(AST, ast.alias):
    name: str
    asname: typing.Optional[str]


class withitem(AST, ast.withitem):
    context_expr: expr
    optional_vars: typing.Optional[expr]


node_map: typing.Dict[typing.Type, typing.Type] = {}


def boostrap_and_check_types():

    for node_type in globals().values():
        if not inspect.isclass(node_type):
            continue
        if not issubclass(node_type, AST):
            continue

        assert node_type.__name__ in ast.__dict__
        original_node_type = ast.__dict__[node_type.__name__]
        assert issubclass(node_type, original_node_type)
        node_map[original_node_type] = node_type

        type_hints = typing.get_type_hints(node_type)
        child_types: typing.Dict[str, typing.Type] = {}

        assert hasattr(node_type, "_fields")
        for field in node_type._fields:

            assert field in type_hints
            child_types[field] = type_hints[field]

        node_type._child_types = child_types


boostrap_and_check_types()


@concept.get_node_kind.register
def get_pyast_kind(node: ast.AST) -> concept.NodeKind:
    return concept.NodeKind.STRUCT


@concept.get_node_kind.register
def get_ast_list_kind(node: ASTListBase) -> concept.NodeKind:
    return concept.NodeKind.LIST


@concept.get_struct_fields.register
def get_pyast_fields(node: ast.AST) -> typing.Iterable[str]:
    return node._fields


@concept.get_struct_field_types.register
def get_pyast_field_types(node: ast.AST) -> typing.Dict[str, typing.Type]:
    return node_map[type(node)]._child_types
