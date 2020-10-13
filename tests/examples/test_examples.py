from test_util import transpile, validate

from laplacian_fd import laplacian_fd
from laplacian_fvm import laplacian_fvm


def test_examples():
    validate(transpile(laplacian_fd))
    validate(transpile(laplacian_fvm))
