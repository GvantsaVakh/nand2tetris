"""
simulator.py

Simulates chip behavior. Built-in gates (Nand, Not, And, Or) are evaluated
directly with Python functions. Any other chip is loaded from its .hdl file
(via ChipLoader) and simulated recursively, bottoming out at built-ins.
"""

import os
from collections.abc import Callable

from hdl_parser import ChipDef, parse_chip_file

# For each built-in gate: (input pin names, output pin names, function)
# The function takes inputs positionally in the same order as its input pin list
# and returns a dict mapping output pin name -> value.
BUILTIN_SPECS: dict[str, tuple[list[str], list[str]]] = {
    "Nand": (["a", "b"], ["out"]),
    "Not":  (["in"], ["out"]),
    "And":  (["a", "b"], ["out"]),
    "Or":   (["a", "b"], ["out"]),
}

BUILTIN_FUNCS: dict[str, Callable[..., dict[str, int]]] = {
    "Nand": lambda a, b: {"out": 1 - (a & b)},
    "Not":  lambda in_: {"out": 1 - in_},
    "And":  lambda a, b: {"out": a & b},
    "Or":   lambda a, b: {"out": a | b},
}


class ChipLoader:
    """Loads and caches ChipDefs by name so a chip referenced multiple times
    (directly or across the recursion tree) is only parsed from disk once."""

    def __init__(self, chips_dir: str):
        self.chips_dir = chips_dir
        self._cache: dict[str, ChipDef] = {}

    def load(self, chip_name: str) -> ChipDef:
        if chip_name not in self._cache:
            filepath = os.path.join(self.chips_dir, f"{chip_name}.hdl")
            self._cache[chip_name] = parse_chip_file(filepath)
        return self._cache[chip_name]


def _resolve(wires: dict[str, int], wire_name: str) -> int:
    """Resolves a wire name to its 0/1 value. HDL allows connecting a pin
    directly to the constants 'true' or 'false' instead of an actual wire
    (e.g. Nand(a=in, b=false, out=out)) -- handle those before falling back
    to a normal wires-dict lookup."""
    if wire_name == "true":
        return 1
    if wire_name == "false":
        return 0
    return wires[wire_name]


def simulate(chip_def: ChipDef, input_values: dict[str, int], loader: ChipLoader) -> dict[str, int]:
    """Simulates chip_def given a dict of input pin values, returning a dict
    of output pin values.

    Walks chip_def.parts in order (HDL files list parts in a valid dependency
    order, and this project has no sequential/feedback logic). For each part:
      1. look up the values feeding its input pins via the wires dict
         (or resolve 'true'/'false' constants)
      2. evaluate it -- either a built-in function, or a recursive simulate()
         call if it's a composed chip
      3. write its output pin values back into the wires dict under their
         connected wire names
    """
    wires: dict[str, int] = dict(input_values)

    for part in chip_def.parts:
        if part.chip_name in BUILTIN_SPECS:
            input_pins, output_pins = BUILTIN_SPECS[part.chip_name]
            args = [_resolve(wires, part.connections[pin]) for pin in input_pins]
            results = BUILTIN_FUNCS[part.chip_name](*args)
        else:
            sub_def = loader.load(part.chip_name)
            sub_inputs = {pin: _resolve(wires, part.connections[pin]) for pin in sub_def.inputs}
            results = simulate(sub_def, sub_inputs, loader)
            output_pins = sub_def.outputs

        for pin in output_pins:
            wire_name = part.connections[pin]
            wires[wire_name] = results[pin]

    return {name: wires[name] for name in chip_def.outputs}