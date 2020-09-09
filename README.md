# dusk

A minimal and lightweight front-end for dawn.

Dusk translates a subset of Python code (a Python embedded domain specific language - eDSL) to SIR. Its purpose is to allow quick
prototyping of dawn's unstructured features for internal experiments.

Dusk is currently in an experimental state. Examples are available here: [tests/stencils](tests/stencils/)

# Requirements

  * Python 3.8 (support for other Python versions is planned)
  * dawn4py (see: https://github.com/MeteoSwiss-APN/dawn/tree/master/dawn/src/dawn4py )

# Installation

It is highly recommended to use a virtual env for development:

```bash
python -m venv virtual_env # create virtual env
source virtual_env/bin/activate # activate virtual env
```

Then dusk can be directly installed from github via pip (this will also install dawn4py):

```bash
pip install dusk@git+https://github.com/dawn-ico/dusk.git
```

# Usage

The package will install a `dusk` command-line tool which can be used to compile dusk stencils:

```bash
dusk --help
```

## Overview
- [tests/examples/](tests/examples/) - Examples of the dusk eDSL
- [dusk/script/\_\_init\_\_.py](dusk/script/__init__.py) - Contains definitions & mocks for dusk
- [dusk/cli.py](dusk/cli.py) - Implements a basic command line interface to compile dusk stencils
- [dusk/transpile.py](dusk/transpile.py) - Provides a programmatic interface to compile dusk stencils
- [dusk/grammar.py](dusk/grammar.py) - Implements most of the transformations for Python AST to SIR utilizing the matching framework
- [dusk/semantics.py](dusk/semantics.py) - Provides infrastructure to support dusk's semantics (used by the grammar)
- [dusk/match.py](dusk/match.py) - Implements a simple matching framework for ASTs
