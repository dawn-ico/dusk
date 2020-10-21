#!/usr/bin/env python
from argparse import ArgumentParser
from dusk import transpile, backend_map, default_backend
from os import path


def main() -> None:

    argparser = ArgumentParser(
        description="Transforms the Python embedded DSL to generated code through Dawn.",
    )
    argparser.add_argument("in_file", type=str, help="Input file (dusk stencil)")
    argparser.add_argument("out_file", type=str,
                           help="Output file (generated code)")
    argparser.add_argument(
        "-b",
        type=str,
        dest="backend",
        choices=set(backend_map.keys()),
        default=default_backend,
        help="Backend to use to generate code",
    )
    argparser.add_argument("-dump-sir", default=False, action="store_true", help="Dumps (also) sir to <base_out_file>.json")
    argparser.add_argument("-verbose", dest="verbose", default=False, action="store_true", help="Enables verbosity of dawn",)

    args = argparser.parse_args()
    out_stream = open(args.out_file, "w")
    
    if args.dump_sir:
        sir_stream = open(path.splitext(args.out_file)[0] + ".json", "w")

    transpile(args.in_file, 
              sir_stream if args.dump_sir else None,
              out_stream,
              backend=args.backend, verbose=args.verbose)
    out_stream.close()


if __name__ == "__main__":
    # TODO: add a test that the cli is properly installed & working
    main()
