from test_util import transpile_and_validate
from laplacian_fd import laplacian_fd
from laplacian_fvm import laplacian_fvm


def test_examples():
    transpile_and_validate(laplacian_fd)
    transpile_and_validate(laplacian_fvm)
