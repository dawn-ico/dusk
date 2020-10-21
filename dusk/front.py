#!/usr/bin/env python
from argparse import ArgumentParser
from dusk import transpile
from sys import stdout


def main() -> None:

    argparser = ArgumentParser(
        description="Transforms the Python embedded DSL to SIR.",
    )
    argparser.add_argument("in_file", type=str, help="Input file (dusk stencil)")
    argparser.add_argument("-o", type=str, dest="out_file",
                           help="Write SIR to file instead of standard output")
    
    args = argparser.parse_args()
    if args.out_file:
        sir_stream = open(args.out_file, "w")
    else:
        sir_stream = stdout

    transpile(args.in_file, sir_stream,
              None # don't need to codegenerate
             )
    sir_stream.close()


if __name__ == "__main__":
    # TODO: add a test that the cli is properly installed & working
    main()
