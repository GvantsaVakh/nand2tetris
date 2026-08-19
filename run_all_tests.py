"""
run_all_tests.py

Convenience script: runs every chip in chips/ that has a matching test file
in tests/ (same base name, e.g. chips/Xor.hdl + tests/Xor.csv), and prints
a per-chip pass/fail count plus a grand total.

Only include chips here whose .hdl uses single-bit pins (no [n] bus syntax) --
this parser doesn't support multi-bit buses (And16, Mux16, ALU, etc. are
skipped; multi-bit support is explicitly a non-requirement of this project).

Usage:
    python run_all_tests.py
"""

import os

from hdl_parser import parse_chip_file
from simulator import ChipLoader
from test_runner import parse_test_file, run_tests

CHIPS_DIR = "chips"
TESTS_DIR = "tests"

CHIPS_TO_TEST = [
    "Nand",
    "And",
    "Or",
    "Not",
    "Xor",
    "Mux",
    "DMux",
    "HalfAdder",
    "FullAdder",
]


def main() -> None:
    loader = ChipLoader(CHIPS_DIR)
    grand_passed = 0
    grand_total = 0

    for chip_name in CHIPS_TO_TEST:
        test_path = os.path.join(TESTS_DIR, f"{chip_name}.csv")

        if not os.path.exists(test_path):
            print(f"== {chip_name}: SKIPPED (missing .csv) ==\n")
            continue

        print(f"== {chip_name} ==")

        if chip_name in {"Nand", "Not", "And", "Or"}:
            chip_def = None
        else:
            hdl_path = os.path.join(CHIPS_DIR, f"{chip_name}.hdl")

            if not os.path.exists(hdl_path):
                print(f"== {chip_name}: SKIPPED (missing .hdl) ==\n")
                continue

            chip_def = parse_chip_file(hdl_path)

        output_names, rows = parse_test_file(test_path)

        passed, total = run_tests(
            chip_def,
            loader,
            output_names,
            rows,
            chip_name=chip_name,
        )

        grand_passed += passed
        grand_total += total

        print()

    print(
        f"=== TOTAL: {grand_passed}/{grand_total} tests passed across {len(CHIPS_TO_TEST)} chips ==="
    )


if __name__ == "__main__":
    main()
