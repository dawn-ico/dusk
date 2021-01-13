from laplacian_fd import laplacian_fd
from laplacian_fvm import laplacian_fvm
from interpolation_sph import interpolation_sph

from dusk.integration import StencilObject
from dusk.transpile import validate, stencil_object_to_sir

def test_examples():
    validate(stencil_object_to_sir(StencilObject(laplacian_fd)))
    validate(stencil_object_to_sir(StencilObject(laplacian_fvm)))
    validate(stencil_object_to_sir(StencilObject(interpolation_sph)))
