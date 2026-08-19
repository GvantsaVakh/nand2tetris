"""
main.py

CLI entry point. Usage:

    python main.py chips/Xor.hdl tests/Xor.csv

Parses the given chip's .hdl file, loads the given test vector file, runs
the tests, and prints a pass/fail report with a summary count.
"""

import os
import sys

from hdl_parser import parse_chip_file
from simulator import ChipLoader
from test_runner import parse_test_file, run_tests


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python main.py <chip.hdl> <tests.csv>")
        sys.exit(1)

    hdl_path = sys.argv[1]
    test_path = sys.argv[2]

    chips_dir = os.path.dirname(hdl_path) or "."
    loader = ChipLoader(chips_dir)

    chip_def = parse_chip_file(hdl_path)
    output_names, rows = parse_test_file(test_path)

    run_tests(chip_def, loader, output_names, rows)


if __name__ == "__main__":
    main()
