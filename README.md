# HDL Parser and Chip Testing Framework

Final project for Nand2Tetris. Parses `.hdl` chip files, builds a chip model out of them, simulates the chip's logic, and checks it against test vectors.

## How to run it

Run a single chip against a single test file:

```bash
python3 main.py chips/Xor.hdl tests/Xor.csv
```

This parses `Xor.hdl`, loads `Xor.csv`, runs every test case through the simulator, and prints PASS/FAIL per case plus a summary line at the end.

Run everything at once (every chip listed in CHIPS_TO_TEST inside run_all_tests.py, skipping any missing its .hdl/.csv pair):

```bash
python3 run_all_tests.py
```

This just loops over the chip names in `run_all_tests.py` and calls the same pipeline for each one, then prints a grand total across all of them.

## My approach

Three main pieces:

**Parsing (`hdl_parser.py`)** — I strip out comments first (`//` and `/* */`), then use a few regexes to pull out the chip name, the `IN` list, the `OUT` list, and every line inside `PARTS`. Each `PARTS` line becomes a `PartInstance` — basically just the chip name being instantiated plus a dict mapping its pin names to whatever wire name it's connected to in the parent. This step doesn't do any logic, it's purely turning text into a `ChipDef` object.

**Simulation (`simulator.py`)** — this is the actual engine. `Nand`, `Not`, `And`, `Or` are hardcoded as built-ins with their own Python functions, so they never get parsed as HDL files. Anything else gets loaded (and cached, via `ChipLoader`, so a chip used more than once isn't re-parsed from disk every time) and simulated recursively — `simulate()` calls itself on sub-chips until it bottoms out at a built-in. I keep a `wires` dict that starts out seeded with the input values, and as each part in `PARTS` gets evaluated, its output gets written back into `wires` under whatever name it's connected to. By the time I've walked through every part, the chip's declared `OUT` pins are sitting in that dict with their final values.

One thing I ran into: some of the real Nand2Tetris chips (like `DMux`) wire a pin straight to the built-in constants `true`/`false` instead of an actual wire. I added a small `_resolve()` helper that checks for those two names before falling back to a normal `wires` lookup, otherwise it'd throw a KeyError trying to look up `"false"` as if it were a wire.

**Testing (`test_runner.py`)** — reads the CSV-style test files, parses the header into input/output pin names, and parses each row into an `(inputs, expected_outputs)` pair. Then for every row it calls `simulate()`, compares actual vs expected, and prints PASS or FAIL with both values shown. At the end it prints how many passed out of the total.

I also wrote `run_all_tests.py` as a convenience script so I didn't have to run `main.py` by hand for every single chip — it just loops through a list of chip names and runs each one's `.hdl`/`.csv` pair through the same pipeline, then adds up a grand total.

## Example files

`chips/Xor.hdl` + `tests/Xor.csv` is a good small example — `Xor` is built entirely out of `And`/`Or`/`Not`, so it shows the parser and simulator working together on a non-builtin chip without much noise.

For something that actually shows off the recursion, `chips/FullAdder.hdl` + `tests/FullAdder.csv` is better — `FullAdder` is built out of two `HalfAdder` instances plus an `Or`, and each `HalfAdder` is itself built out of `Xor`/`And`. So running that one goes: `FullAdder` → `HalfAdder` → `Xor` → `And`/`Or`/`Not`, three levels deep before hitting built-ins.

## Test Vector Format

Test files are CSV-style, semicolon-separated between inputs and outputs:

<input pin names>; <output pin names>
<input values>; <expected output values>
...

For example, `tests/Xor.csv`:

a,b; out
0,0; 0
0,1; 1
1,0; 1
1,1; 0

## File structure

```
.
├── hdl_parser.py       # .hdl text -> ChipDef / PartInstance
├── simulator.py        # built-in gates + recursive chip evaluation
├── test_runner.py      # reads test CSVs, runs cases, prints results
├── main.py              # CLI: run one chip against one test file
├── run_all_tests.py     # runs every chip/test pair, prints grand total
├── chips/                # .hdl files
└── tests/                # matching .csv test vector files
```
