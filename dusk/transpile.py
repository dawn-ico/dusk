from typing import Optional, List

import io

import dawn4py
import dawn4py.serialization as ser
import dawn4py.serialization.SIR as sir

import dusk.integration as integration
from dusk.passes.pipeline import stencil_object_to_sir

backend_map = {
    "ico-naive": dawn4py.CodeGenBackend.CXXNaiveIco,
    "ico-cuda": dawn4py.CodeGenBackend.CUDAIco,
}
default_backend = "ico-naive"


def merge_sirs(sirs: List[sir.SIR], filename: Optional[str] = None):

    if filename is None:
        if 0 < len(sirs):
            filename = sirs[0].filename
        else:
            filename = "<unknown>"

    stencils = [stencil for sir in sirs for stencil in sir.stencils]
    # FIXME: globals
    return ser.make_sir(filename, sir.GridType.Value("Unstructured"), stencils)


def sir_to_cpp(
    sir_node: sir.SIR, verbose: bool = False, groups: List = [], backend=default_backend
) -> str:
    if verbose:
        dawn4py.set_verbosity(dawn4py.LogLevel.All)
    # TODO: default pass groups are bugged in Dawn, need to pass empty list of groups
    return dawn4py.compile(sir_node, groups=groups, backend=backend_map[backend])


def validate(sir_node: sir.SIR) -> None:
    dawn4py._dawn4py.run_optimizer_sir(sir_node.SerializeToString())


def transpile(
    in_path: str,
    out_sir_file: Optional[io.TextIOBase] = None,
    out_gencode_file: Optional[io.TextIOBase] = None,
    backend: str = default_backend,
    verbose: bool = False,
) -> None:

    assert 0 == len(integration.stencil_collection)

    integration.import_stencil_file(in_path)

    sir_nodes = [
        stencil_object_to_sir(stencil_object)
        for stencil_object in integration.stencil_collection
    ]
    sir_node = merge_sirs(sir_nodes)

    if out_sir_file is not None:
        out_sir_file.write(ser.to_json(sir_node))
    if out_gencode_file is not None:
        out_gencode_file.write(sir_to_cpp(sir_node, backend=backend, verbose=verbose))
