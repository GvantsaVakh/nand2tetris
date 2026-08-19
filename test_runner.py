"""
test_runner.py

Reads CSV-style test vector files (see README for format) and runs each
test case through the simulator, printing per-case pass/fail and a final
summary count.
"""

from hdl_parser import ChipDef
from simulator import ChipLoader, simulate, BUILTIN_SPECS


def parse_test_file(filepath: str) -> tuple[list[str], list[tuple[dict, dict]]]:
    """Parses a test vector file.

    Format:
        a,b; out
        0,0; 0
        0,1; 0
        1,0; 0
        1,1; 1

    Returns (output_pin_names, rows) where rows is a list of
    (input_values, expected_output_values) dict pairs.
    """
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    header_inputs, header_outputs = lines[0].split(";")
    input_names = [name.strip() for name in header_inputs.split(",")]
    output_names = [name.strip() for name in header_outputs.split(",")]

    rows = []
    for line in lines[1:]:
        in_part, out_part = line.split(";")
        in_values = [int(v.strip()) for v in in_part.split(",")]
        out_values = [int(v.strip()) for v in out_part.split(",")]
        inputs = dict(zip(input_names, in_values))
        expected = dict(zip(output_names, out_values))
        rows.append((inputs, expected))

    return output_names, rows


def run_tests(
    chip_def: ChipDef | None,
    loader: ChipLoader,
    output_names: list[str],
    rows: list[tuple[dict, dict]],
    chip_name: str | None = None,
) -> tuple[int, int]:
    """Runs every test case against a chip, printing pass/fail per case
    plus a final summary. Supports both HDL-defined and built-in chips.
    """
    passed = 0
    total = len(rows)

    for i, (inputs, expected) in enumerate(rows, start=1):
        if chip_name in BUILTIN_SPECS:
            input_pins, _ = BUILTIN_SPECS[chip_name]
            args = [inputs[pin] for pin in input_pins]

            from simulator import BUILTIN_FUNCS

            actual = BUILTIN_FUNCS[chip_name](*args)
        else:
            assert chip_def is not None, (
                f"chip_def is required for non-builtin chip {chip_name!r}"
            )
            actual = simulate(chip_def, inputs, loader)

        actual_relevant = {name: actual[name] for name in output_names}
        ok = actual_relevant == expected

        status = "PASS" if ok else "FAIL"

        if ok:
            passed += 1

        print(
            f"Test {i}: {status} | "
            f"inputs={inputs} expected={expected} actual={actual_relevant}"
        )

    print(f"\n{passed}/{total} tests passed")
    return passed, total
