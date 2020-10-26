#!/usr/bin/env python
from argparse import ArgumentParser
from dusk import transpile
from sys import stdout


def main() -> None:

    argparser = ArgumentParser(
        description="Transforms the Python embedded DSL to SIR.",
    )
    argparser.add_argument("in_file", type=str, help="Input file (dusk stencil)")

    args = argparser.parse_args()

    transpile(args.in_file, stdout, None)  # don't need to codegenerate


if __name__ == "__main__":
    # TODO: add a test that the cli is properly installed & working
    main()
