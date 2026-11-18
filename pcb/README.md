# PCB projects

Revision A uses two KiCad 10 projects:

- `seq08-io`: four-layer active main board
- `seq08-jacks`: two-layer passive board for nineteen PJ398SM jacks

See [`../doc/hw.md`](../doc/hw.md) for the electrical design and [`../doc/bom.md`](../doc/bom.md) for parts.

The display, DC jack, power switch, jacks, and buttons connect to the main board by cable. J24 and J25 connect the main board to the jack board.

## Regeneration

Edit the Python sources, then regenerate the KiCad schematics:

```sh
python3 pcb/seq08-io/generate_schematic.py
python3 pcb/seq08-jacks/generate_schematic.py
kicad-cli sch erc --exit-code-violations pcb/seq08-io/seq08-io.kicad_sch
kicad-cli sch erc --exit-code-violations pcb/seq08-jacks/seq08-jacks.kicad_sch
```

`populate_boards.py` creates the initial placement. It refuses to replace populated boards without `--replace`.

```sh
python3 pcb/populate_boards.py --replace seq08-io
python3 pcb/populate_boards.py --replace seq08-jacks
```

`--replace` discards PCB edits. Pass one project name to avoid replacing both boards.

## Current state

- Main board: 180 x 104 mm, 157 schematic footprints, four M3 mounting holes
- Jack board: 160 x 100 mm, 21 schematic footprints, four M3 mounting holes
- Schematics: ERC clean
- Placement: DRC clean
- Copper routing: not started

The display uses a keyed 2x20, 2.54 mm IDC header, 4-wire SPI, and 5 V power. Verify the physical module header before ordering a PCB.
