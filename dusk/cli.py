#!/usr/bin/env python
from argparse import ArgumentParser
from dusk.transpile import transpile, backend_map, default_backend
from os import path


def main() -> None:

    argparser = ArgumentParser(
        description="Transforms the Python embedded DSL to generated code through Dawn.",
    )
    argparser.add_argument("in_file", type=str, help="Input file (dusk stencil)")
    argparser.add_argument(
        "-o",
        type=str,
        dest="out_file",
        help="Output file (generated code), default: <base_in_file>_<backend>.cpp",
    )
    argparser.add_argument(
        "-b",
        type=str,
        dest="backend",
        choices=set(backend_map.keys()),
        default=default_backend,
        help="Backend to use to generate code",
    )
    argparser.add_argument(
        "--dump-sir",
        default=False,
        action="store_true",
        help="Dumps (also) sir to <base_in_file>.json",
    )
    argparser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        default=False,
        action="store_true",
        help="Enables verbosity of dawn",
    )

    args = argparser.parse_args()

    in_filename = path.splitext(path.basename(args.in_file))[0]

    if args.out_file is None:
        args.out_file = in_filename + "_" + args.backend + ".cpp"
    out_stream = open(args.out_file, "w")

    sir_stream = None
    if args.dump_sir:
        sir_stream = open(in_filename + ".json", "w")

    transpile(
        args.in_file,
        sir_stream,
        out_stream,
        backend=args.backend,
        verbose=args.verbose,
    )

    out_stream.close()
    if sir_stream is not None:
        sir_stream.close()


if __name__ == "__main__":
    # TODO: add a test that the cli is properly installed & working
    main()
