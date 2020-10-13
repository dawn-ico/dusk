#!/usr/bin/env python
from argparse import ArgumentParser
from dusk import transpile, backend_map, default_backend


def main() -> None:

    argparser = ArgumentParser(
        description="Transforms the Python embedded DSL to SIR.",
    )
    argparser.add_argument("in_file", type=str)
    argparser.add_argument("-o", type=str, dest="out_file", default="out.cpp")
    argparser.add_argument(
        "--dump-sir", default=False, action="store_true", help="dump sir to disk",
    )
    argparser.add_argument(
        "-b",
        type=str,
        dest="backend",
        choices=set(backend_map.keys()),
        default=default_backend,
    )

    args = argparser.parse_args()
    transpile(args.in_file, args.out_file, backend=args.backend, dump_sir=args.dump_sir)


if __name__ == "__main__":
    # TODO: add a test that the cli is properly installed & working
    main()
