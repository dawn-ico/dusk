__all__ = [
    "max",
    "min",
    "pow",
    "sqrt",
    "exp",
    "log",
    "sin",
    "cos",
    "tan",
    "arcsin",
    "arccos",
    "arctan",
    "abs",
    "floor",
    "ceil",
    "isinf",
    "isnan",
]


# (a: float, b: float) -> float
max = max  # we reassing, because `min` is a built-in


# (a: float, b: float) -> float:
min = min  # we reassing, because `max` is a built-in


# (base: float, exp: float) -> float:
pow = pow  # we reassing, because `pow` is a built-in


# (x: float) -> float
abs = abs  # we reassing, because `abs` is a built-in


def sqrt(arg: float) -> float:
    raise NotImplementedError


def exp(exp: float) -> float:
    raise NotImplementedError


def log(arg: float) -> float:
    raise NotImplementedError


def sin(arg: float) -> float:
    raise NotImplementedError


def cos(arg: float) -> float:
    raise NotImplementedError


def tan(arg: float) -> float:
    raise NotImplementedError


def arcsin(arg: float) -> float:
    raise NotImplementedError


def arccos(arg: float) -> float:
    raise NotImplementedError


def arctan(arg: float) -> float:
    raise NotImplementedError


def floor(arg: float) -> float:
    raise NotImplementedError


def ceil(arg: float) -> float:
    raise NotImplementedError


def isinf(arg: float) -> float:
    raise NotImplementedError


def isnan(arg: float) -> float:
    raise NotImplementedError
