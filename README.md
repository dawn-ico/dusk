# dusk

A minimal and lightweight front-end for dawn.

Dusk translates a subset of Python code (a Python embedded domain specific language - eDSL) to SIR. Its purpose is to allow quick
prototyping of dawn's unstructured features for internal experiments.

Dusk is currently in an experimental state. An example is available here: [test.py](test.py)

# Requirements

  * Python 3.8 (support for other Python versions is planned)
  * dawn4py (see: https://github.com/MeteoSwiss-APN/dawn/tree/master/dawn/src/dawn4py )
  
# Usage

Due to it's prototyping nature, `PYTHONPATH` has to be used for execution. For example:

```bash
PYTHONPATH=./:$PYTHONPATH ./dusk/cli.py ./test.py
```

Usage:

```bash
PYTHONPATH=./:$PYTHONPATH ./dusk/cli.py --help
usage: cli.py [-h] [-o OUT_FILE] [--dump-sir] [-b {ico-cuda,ico-naive}] in_file

Transforms the Python embedded DSL to SIR.

positional arguments:
  in_file

optional arguments:
  -h, --help            show this help message and exit
  -o OUT_FILE
  --dump-sir            dump sir to disk
  -b {ico-cuda,ico-naive}
```

# Development

Please use the [black](https://github.com/psf/black) formater for your python code.

## Overview
- [test.py](test.py) - An example of the dusk eDSL
- [dusk/script.py](dusk/script.py) - Contains definitions & mocks for the DSL
- [dusk/cli.py](dusk/cli.py) - Implements a basic command line interface to compile the dusk eDSL
- [dusk/transpile.py](dusk/transpile.py) - Provides a programmatic interface to compile the dusk eDSL
- [dusk/grammar.py](dusk/grammar.py) - Implements most of the transformations for Python AST to SIR utilizing the matching framework
- [dusk/semantics.py](dusk/semantics.py) - Provides infrastructure to support dusk's semantics (used by the grammar)
- [dusk/match.py](dusk/match.py) - Implements a simple matching framework for ASTs
