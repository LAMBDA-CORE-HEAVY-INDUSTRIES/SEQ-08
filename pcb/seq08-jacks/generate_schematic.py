#!/usr/bin/env python3

from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


PROJECT = "seq08-jacks"
ROOT_UUID = str(uuid5(NAMESPACE_URL, f"{PROJECT}/root"))
ROOT = Path(__file__).parent
SCHEMATIC_OUTPUT = ROOT / f"{PROJECT}.kicad_sch"
SYMBOL_LIBRARY_OUTPUT = ROOT / "seq08-jacks.kicad_sym"
PJ398SM_FOOTPRINT = "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"


def uid(*parts):
    return str(uuid5(NAMESPACE_URL, "/".join((PROJECT, *map(str, parts)))))


def effects(size=1.27, justify=None, hide=False, bold=False):
    justify_text = f"\n\t\t\t\t(justify {justify})" if justify else ""
    hide_text = "\n\t\t\t\t(hide yes)" if hide else ""
    bold_text = "\n\t\t\t\t(bold yes)" if bold else ""
    return f"""(effects
\t\t\t(font
\t\t\t\t(size {size} {size}){bold_text}
\t\t\t){justify_text}{hide_text}
\t\t)"""


symbols = {}
components = []
labels = []
no_connects = []
texts = []


def define_symbol(name, pins, width, height):
    left = [pin for pin in pins if pin[3] == "left"]
    right = [pin for pin in pins if pin[3] == "right"]
    placed_pins = []
    for side, side_pins in (("left", left), ("right", right)):
        start = -((len(side_pins) - 1) * 2.54) / 2
        for index, (number, pin_name, pin_type, _) in enumerate(side_pins):
            x = -width / 2 - 2.54 if side == "left" else width / 2 + 2.54
            y = start + index * 2.54
            rotation = 0 if side == "left" else 180
            placed_pins.append((number, pin_name, pin_type, side, x, y, rotation))
    symbols[name] = {"width": width, "height": height, "pins": placed_pins}


def symbol_definition(name, symbol, qualified=True):
    library_name = f"SEQ08_JACKS:{name}" if qualified else name
    pin_text = []
    for number, pin_name, pin_type, _, x, y, rotation in symbol["pins"]:
        pin_text.append(f"""\t\t\t(pin {pin_type} line
\t\t\t\t(at {x:.3f} {y:.3f} {rotation})
\t\t\t\t(length 2.54)
\t\t\t\t(name "{pin_name}" {effects(1.0)})
\t\t\t\t(number "{number}" {effects(1.0)})
\t\t\t)""")
    half_width = symbol["width"] / 2
    half_height = symbol["height"] / 2
    return f"""\t\t(symbol "{library_name}"
\t\t\t(pin_names (offset 1.0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "J" (at 0 {-half_height - 2.54:.3f} 0) {effects(1.27)})
\t\t\t(property "Value" "{name}" (at 0 {half_height + 2.54:.3f} 0) {effects(1.27)})
\t\t\t(property "Footprint" "" (at 0 0 0) {effects(1.0, hide=True)})
\t\t\t(property "Datasheet" "" (at 0 0 0) {effects(1.0, hide=True)})
\t\t\t(property "Description" "" (at 0 0 0) {effects(1.0, hide=True)})
\t\t\t(symbol "{name}_0_1"
\t\t\t\t(rectangle
\t\t\t\t\t(start {-half_width:.3f} {-half_height:.3f})
\t\t\t\t\t(end {half_width:.3f} {half_height:.3f})
\t\t\t\t\t(stroke (width 0.254) (type solid))
\t\t\t\t\t(fill (type background))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "{name}_1_1"
{chr(10).join(pin_text)}
\t\t\t)
\t\t\t(embedded_fonts no)
\t\t)"""


def add_label(net, x, y, side, key):
    rotation = 180 if side == "left" else 0
    justification = "right bottom" if side == "left" else "left bottom"
    labels.append(f"""\t(label "{net}"
\t\t(at {x:.3f} {y:.3f} {rotation})
\t\t{effects(1.0, justify=justification)}
\t\t(uuid "{uid('label', key, net)}")
\t)""")


def add_component(symbol_name, reference, value, x, y, pin_nets, footprint):
    x = round(x / 1.27) * 1.27
    y = round(y / 1.27) * 1.27
    symbol = symbols[symbol_name]
    pin_instances = []
    for number, _, _, side, pin_x, pin_y, _ in symbol["pins"]:
        absolute_x = x + pin_x
        absolute_y = y - pin_y
        net = pin_nets.get(number)
        pin_instances.append(f"\t\t(pin \"{number}\" (uuid \"{uid('pin', reference, number)}\"))")
        if net:
            add_label(net, absolute_x, absolute_y, side, f"{reference}-{number}")
        else:
            no_connects.append(f"""\t(no_connect
\t\t(at {absolute_x:.3f} {absolute_y:.3f})
\t\t(uuid "{uid('nc', reference, number)}")
\t)""")
    components.append(f"""\t(symbol
\t\t(lib_id "SEQ08_JACKS:{symbol_name}")
\t\t(at {x:.3f} {y:.3f} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid('component', reference)}")
\t\t(property "Reference" "{reference}" (at {x:.3f} {y - symbol['height'] / 2 - 2.54:.3f} 0) {effects(1.27)})
\t\t(property "Value" "{value}" (at {x:.3f} {y + symbol['height'] / 2 + 2.54:.3f} 0) {effects(1.27)})
\t\t(property "Footprint" "{footprint}" (at {x:.3f} {y:.3f} 0) {effects(1.0, hide=True)})
\t\t(property "Datasheet" "" (at {x:.3f} {y:.3f} 0) {effects(1.0, hide=True)})
\t\t(property "Description" "" (at {x:.3f} {y:.3f} 0) {effects(1.0, hide=True)})
{chr(10).join(pin_instances)}
\t\t(instances
\t\t\t(project "{PROJECT}"
\t\t\t\t(path "/{ROOT_UUID}" (reference "{reference}") (unit 1))
\t\t\t)
\t\t)
\t)""")


def add_section(title, x, y):
    texts.append(f"""\t(text "{title}"
\t\t(exclude_from_sim no)
\t\t(at {x:.3f} {y:.3f} 0)
\t\t{effects(2.2, bold=True)}
\t\t(uuid "{uid('text', title)}")
\t)""")


define_symbol(
    "PJ398SM",
    [("T", "TIP", "passive", "left"), ("S", "SLEEVE", "passive", "left"), ("TN", "TIP_NORMAL", "passive", "right")],
    15.24,
    10.16,
)
define_symbol(
    "CONN_2X10",
    [(str(pin), f"PIN_{pin}", "passive", "left" if pin % 2 else "right") for pin in range(1, 21)],
    20.32,
    27.94,
)
define_symbol(
    "CONN_2X12",
    [(str(pin), f"PIN_{pin}", "passive", "left" if pin % 2 else "right") for pin in range(1, 25)],
    20.32,
    33.02,
)


add_section("EIGHT CV OUTPUT JACKS", 20, 18)
for channel in range(1, 9):
    x = 45 + (channel - 1) * 30
    add_component("PJ398SM", f"J{channel}", f"CV OUT {channel}", x, 50, {"T": f"CV_OUT{channel}", "S": "GND"}, PJ398SM_FOOTPRINT)

add_section("EIGHT GATE OUTPUT JACKS", 20, 90)
for channel in range(1, 9):
    x = 45 + (channel - 1) * 30
    add_component("PJ398SM", f"J{channel + 8}", f"GATE OUT {channel}", x, 122, {"T": f"GATE_OUT{channel}", "S": "GND"}, PJ398SM_FOOTPRINT)

add_section("CLOCK AND RESET JACKS", 20, 162)
add_component("PJ398SM", "J17", "CLOCK IN", 55, 194, {"T": "CLOCK_IN_JACK", "S": "GND", "TN": "GND"}, PJ398SM_FOOTPRINT)
add_component("PJ398SM", "J18", "CLOCK OUT", 105, 194, {"T": "CLOCK_OUT_JACK", "S": "GND"}, PJ398SM_FOOTPRINT)
add_component("PJ398SM", "J19", "RESET IN", 155, 194, {"T": "RESET_IN_JACK", "S": "GND", "TN": "GND"}, PJ398SM_FOOTPRINT)

add_section("MAIN BOARD INTERCONNECTS", 220, 162)
cv_panel_nets = {str(channel * 2 - 1): f"CV_OUT{channel}" for channel in range(1, 9)}
cv_panel_nets.update({str(pin): "GND" for pin in range(2, 21, 2)})
add_component("CONN_2X10", "J24", "CV MAIN BOARD", 260, 205, cv_panel_nets, "Connector_IDC:IDC-Header_2x10_P2.54mm_Vertical")

digital_panel_signals = [
    *(f"GATE_OUT{channel}" for channel in range(1, 9)),
    "CLOCK_OUT_JACK",
    "CLOCK_IN_JACK",
    "RESET_IN_JACK",
]
digital_panel_nets = {str(index * 2 - 1): net for index, net in enumerate(digital_panel_signals, 1)}
digital_panel_nets.update({str(pin): "GND" for pin in range(2, 25, 2)})
add_component("CONN_2X12", "J25", "DIGITAL MAIN BOARD", 330, 205, digital_panel_nets, "Connector_IDC:IDC-Header_2x12_P2.54mm_Vertical")


library = "\n".join(symbol_definition(name, symbol) for name, symbol in symbols.items())
external_library = "\n".join(symbol_definition(name, symbol, qualified=False) for name, symbol in symbols.items())
external_library = "\n".join(line[1:] if line.startswith("\t") else line for line in external_library.splitlines())
SYMBOL_LIBRARY_OUTPUT.write_text(f"""(kicad_symbol_lib
\t(version 20231120)
\t(generator "kicad_symbol_editor")
{external_library}
)\n""")
SCHEMATIC_OUTPUT.write_text(f"""(kicad_sch
\t(version 20260306)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "{ROOT_UUID}")
\t(paper "A3")
\t(title_block
\t\t(title "SEQ-08 Passive PJ398SM Jack Board")
\t\t(date "2026-07-17")
\t\t(rev "A")
\t\t(company "SEQ-08")
\t\t(comment 1 "Eight CV, eight gate, clock input/output, and reset input jacks")
\t\t(comment 2 "No active circuitry, connected to the main PCB with keyed IDC cables")
\t)
\t(lib_symbols
{library}
\t)
{chr(10).join(no_connects)}
{chr(10).join(labels)}
{chr(10).join(texts)}
{chr(10).join(components)}
\t(sheet_instances
\t\t(path "/" (page "1"))
\t)
)\n""")
