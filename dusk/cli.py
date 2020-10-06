#!/usr/bin/env python
from argparse import ArgumentParser
from dusk import transpile, backend_map, default_backend
from sys import stdout


def main() -> None:

    argparser = ArgumentParser(
        description="Transforms the Python embedded DSL to SIR.",
    )
    argparser.add_argument("in_file", type=str)
    argparser.add_argument("-o", type=str, dest="out_file",
                           help="Write output to file instead of standard output")
    argparser.add_argument(
        "-generate-code", dest="codegen", default=False, action="store_true", help="Generate code (through dawn) instead of SIR",
    )
    argparser.add_argument(
        "-b",
        type=str,
        dest="backend",
        choices=set(backend_map.keys()),
        default=default_backend,
        help="Backend to use to generate code (ignored if generating SIR)",
    )
    argparser.add_argument("-verbose", dest="verbose", default=False, action="store_true", help="Enables verbosity of dawn",)

    args = argparser.parse_args()
    if args.out_file:
        out_stream = open(args.out_file, "w")
    else:
        out_stream = stdout

    transpile(args.in_file, out_stream,
              backend=args.backend, write_sir=False if args.codegen else True, verbose=args.verbose)
    out_stream.close()


if __name__ == "__main__":
    main()
