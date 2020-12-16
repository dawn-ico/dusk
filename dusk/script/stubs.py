import dusk.script as script


LOCATION_TYPES = {script.Edge, script.Cell, script.Vertex, script.Origin}


UNARY_MATH_FUNCTIONS = {
    script.sqrt,
    script.exp,
    script.log,
    script.sin,
    script.cos,
    script.tan,
    script.arcsin,
    script.arccos,
    script.arctan,
    script.fabs,
    script.floor,
    script.ceil,
    script.isinf,
    script.isnan,
}


BINARY_MATH_FUNCTIONS = {
    script.max,
    script.min,
    script.pow,
}
