import pathlib
import subprocess

import pytest

base_path = pathlib.Path(__file__).parent.absolute()

# TODO: more test files?
# FIXME: add `tests/stencils/test_globals.py`
# (there was a bug with this test case and the cli!)
test_files = [
    base_path / "examples" / "laplacian_fd.py",
    base_path / "examples" / "laplacian_fvm.py",
]


# TODO: test flags & validate output


@pytest.mark.parametrize("dusk_file", test_files)
def test_dusk_cli(dusk_file):
    subprocess.run(["dusk", dusk_file], check=True)


@pytest.mark.parametrize("dusk_file", test_files)
def test_dusk_front_cli(dusk_file):
    subprocess.run(["dusk-front", dusk_file], check=True)
