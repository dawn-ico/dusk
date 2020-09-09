from test_util import transpile_and_validate
from nh_diffusion import ICON_laplacian_diamond
from nh_diffusion_fvm import ICON_laplacian_fvm


def test_examples():
    transpile_and_validate(ICON_laplacian_diamond)
    transpile_and_validate(ICON_laplacian_fvm)
