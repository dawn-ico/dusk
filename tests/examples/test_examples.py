from dusk.transpile import callable_to_pyast, pyast_to_sir, validate

from laplacian_fd import laplacian_fd
from laplacian_fvm import laplacian_fvm


def test_examples():
    validate(pyast_to_sir(callable_to_pyast(laplacian_fd)))
    validate(pyast_to_sir(callable_to_pyast(laplacian_fvm)))
