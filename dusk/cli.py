#!/usr/bin/env python
from argparse import ArgumentParser, FileType
from dusk import transpile, backend_map, default_backend


def main() -> None:

    argparser = ArgumentParser(
        description="Transforms the Python embedded DSL to SIR.",
    )
    argparser.add_argument("in_file", type=str)
    argparser.add_argument("-o", type=str, dest="out_file", default="out.cpp")
    argparser.add_argument(
        "-b",
        type=str,
        dest="backend",
        choices=set(backend_map.keys()),
        default=default_backend,
    )

    args = argparser.parse_args()
    transpile(args.in_file, args.out_file, backend=args.backend)


if __name__ == "__main__":
    main()
