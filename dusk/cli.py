#!/usr/bin/env python
from argparse import ArgumentParser, FileType
from dusk import transpile


def main() -> None:

    argparser = ArgumentParser(
        description="Transforms the Python embedded DSL to SIR.",
    )
    argparser.add_argument("in_file", type=str)
    argparser.add_argument("-o", type=str, dest="out_file", default="out.cpp")

    args = argparser.parse_args()
    transpile(args.in_file, args.out_file)


if __name__ == "__main__":
    main()
