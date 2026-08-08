"""
hdl_parser.py

Parses syntactically correct nand2tetris-style HDL files into an internal
representation: a ChipDef holding the chip's declared inputs, outputs, and
the list of PartInstance objects found in its PARTS section.

This module does NOT simulate anything -- it only turns text into structured
Python objects. Simulation lives in simulator.py.
"""

import re
from dataclasses import dataclass, field


@dataclass
class PartInstance:
    """One line inside a PARTS section, e.g. And(a=in1, b=w1, out=myOut);

    chip_name:   the name of the chip being instantiated, e.g. "And"
    connections: maps the *sub-chip's* local pin name -> the wire name used
                 in the parent chip's scope, e.g. {"a": "in1", "b": "w1", "out": "myOut"}
    """
    chip_name: str
    connections: dict[str, str] = field(default_factory=dict)


@dataclass
class ChipDef:
    """Internal representation of a parsed chip."""
    name: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    parts: list[PartInstance] = field(default_factory=list)


def _strip_comments(text: str) -> str:
    """Removes // line comments and /* ... */ block comments from HDL text."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*", "", text)
    return text


def _parse_pin_list(raw: str) -> list[str]:
    """Turns 'a, b, c' into ['a', 'b', 'c']. Ignores empty/whitespace-only entries."""
    return [name.strip() for name in raw.split(",") if name.strip()]


def _parse_connections(raw: str) -> dict[str, str]:
    """Turns 'a=in1, b=w1, out=myOut' into {'a': 'in1', 'b': 'w1', 'out': 'myOut'}."""
    connections = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        local_pin, wire_name = pair.split("=")
        connections[local_pin.strip()] = wire_name.strip()
    return connections


def parse_chip_text(text: str) -> ChipDef:
    """Parses the full text of an HDL file into a ChipDef.

    Assumes syntactically valid, single-bit (non-bus) HDL, per the project spec.
    """
    text = _strip_comments(text)

    name_match = re.search(r"CHIP\s+(\w+)\s*\{", text)
    assert name_match is not None, "HDL is guaranteed valid per project spec: missing CHIP declaration"
    chip_name = name_match.group(1)

    in_match = re.search(r"IN\s+([^;]+);", text)
    inputs = _parse_pin_list(in_match.group(1)) if in_match else []

    out_match = re.search(r"OUT\s+([^;]+);", text)
    outputs = _parse_pin_list(out_match.group(1)) if out_match else []

    parts_match = re.search(r"PARTS:\s*(.*?)\}", text, flags=re.DOTALL)
    parts: list[PartInstance] = []
    if parts_match:
        parts_text = parts_match.group(1)
        # Each part line looks like: ChipName(pin=wire, pin=wire);
        for part_match in re.finditer(r"(\w+)\s*\(([^)]*)\)\s*;", parts_text):
            part_chip_name = part_match.group(1)
            connections = _parse_connections(part_match.group(2))
            parts.append(PartInstance(chip_name=part_chip_name, connections=connections))

    return ChipDef(name=chip_name, inputs=inputs, outputs=outputs, parts=parts)


def parse_chip_file(filepath: str) -> ChipDef:
    """Reads an .hdl file from disk and parses it into a ChipDef."""
    with open(filepath, "r") as f:
        text = f.read()
    return parse_chip_text(text)