import dawn4py.serialization as dawn_ser

from dusk import script
from dusk.ir import pyast, traversal
from dusk.passes import tree


class GlobalsResolver(tree.TreeTransformer[pyast.AST]):

    # FIXME: preconditions + postconditions
    def transform_bare(self) -> None:
        resolve_globals(self.tree_handle)


def resolve_globals(tree_handle: tree.TreeHandle[pyast.AST]) -> None:

    tree_handle.annotations.globals = dawn_ser.AST.GlobalVariableMap()

    for node in traversal.post_order(tree_handle.tree):
        if (
            isinstance(node, pyast.Name)
            and hasattr(node, "decl")
            and isinstance(node.decl, script.Global)
        ):
            name = node.decl.name
            tree_handle.annotations.globals.map[name].double_value = 0
            node.sir = dawn_ser.make_var_access_expr(name, is_external=True)
