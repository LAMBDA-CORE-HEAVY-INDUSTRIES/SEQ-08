#!/usr/bin/env python3

from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


PROJECT = "seq08-io"
ROOT_UUID = str(uuid5(NAMESPACE_URL, f"{PROJECT}/root"))
SCHEMATIC_OUTPUT = Path(__file__).with_name("seq08-io.kicad_sch")
SYMBOL_LIBRARY_OUTPUT = Path(__file__).with_name("seq08.kicad_sym")


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
reference_counters = {"R": 0, "C": 0, "D": 0, "TP": 0}


def define_symbol(name, pins, width=20.32, height=None, in_bom=True, on_board=True):
    left = [pin for pin in pins if pin[3] == "left"]
    right = [pin for pin in pins if pin[3] == "right"]
    pin_rows = max(len(left), len(right), 1)
    height = height or max(10.16, (pin_rows - 1) * 2.54 + 5.08)
    placed_pins = []

    for side, side_pins in (("left", left), ("right", right)):
        start = -((len(side_pins) - 1) * 2.54) / 2
        for index, (number, pin_name, pin_type, _) in enumerate(side_pins):
            x = -width / 2 - 2.54 if side == "left" else width / 2 + 2.54
            y = start + index * 2.54
            rotation = 0 if side == "left" else 180
            placed_pins.append((number, pin_name, pin_type, side, x, y, rotation))

    symbols[name] = {
        "width": width,
        "height": height,
        "pins": placed_pins,
        "in_bom": in_bom,
        "on_board": on_board,
    }


def symbol_definition(name, symbol, qualified=True):
    library_name = f"SEQ08:{name}" if qualified else name
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
\t\t\t(in_bom {"yes" if symbol["in_bom"] else "no"})
\t\t\t(on_board {"yes" if symbol["on_board"] else "no"})
\t\t\t(property "Reference" "U" (at 0 {-half_height - 2.54:.3f} 0) {effects(1.27)})
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


def add_component(symbol_name, reference, value, x, y, pin_nets, footprint="", datasheet=""):
    x = round(x / 1.27) * 1.27
    y = round(y / 1.27) * 1.27
    symbol = symbols[symbol_name]
    component_id = uid("component", reference)
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
\t\t(lib_id "SEQ08:{symbol_name}")
\t\t(at {x:.3f} {y:.3f} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom {"yes" if symbol["in_bom"] else "no"})
\t\t(on_board {"yes" if symbol["on_board"] else "no"})
\t\t(dnp no)
\t\t(uuid "{component_id}")
\t\t(property "Reference" "{reference}" (at {x:.3f} {y - symbol['height'] / 2 - 2.54:.3f} 0) {effects(1.27)})
\t\t(property "Value" "{value}" (at {x:.3f} {y + symbol['height'] / 2 + 2.54:.3f} 0) {effects(1.27)})
\t\t(property "Footprint" "{footprint}" (at {x:.3f} {y:.3f} 0) {effects(1.0, hide=True)})
\t\t(property "Datasheet" "{datasheet}" (at {x:.3f} {y:.3f} 0) {effects(1.0, hide=True)})
\t\t(property "Description" "" (at {x:.3f} {y:.3f} 0) {effects(1.0, hide=True)})
{chr(10).join(pin_instances)}
\t\t(instances
\t\t\t(project "{PROJECT}"
\t\t\t\t(path "/{ROOT_UUID}" (reference "{reference}") (unit 1))
\t\t\t)
\t\t)
\t)""")


def next_reference(prefix):
    reference_counters[prefix] += 1
    return f"{prefix}{reference_counters[prefix]}"


def add_two_pin(symbol_name, prefix, value, x, y, net_a, net_b, footprint):
    reference = next_reference(prefix)
    add_component(symbol_name, reference, value, x, y, {"1": net_a, "2": net_b}, footprint)


def add_section(title, x, y):
    texts.append(f"""\t(text "{title}"
\t\t(exclude_from_sim no)
\t\t(at {x:.3f} {y:.3f} 0)
\t\t{effects(2.2, bold=True)}
\t\t(uuid "{uid('text', title)}")
\t)""")


define_symbol("R", [("1", "1", "passive", "left"), ("2", "2", "passive", "right")], 7.62, 5.08)
define_symbol("C", [("1", "+", "passive", "left"), ("2", "-", "passive", "right")], 7.62, 5.08)
define_symbol("D", [("1", "A", "passive", "left"), ("2", "K", "passive", "right")], 7.62, 5.08)
define_symbol("SWITCH", [("1", "IN", "passive", "left"), ("2", "OUT", "passive", "right")], 10.16, 5.08)
define_symbol("TESTPOINT", [("1", "TP", "passive", "left")], 5.08, 5.08)
define_symbol("PWR_FLAG", [("1", "PWR", "power_out", "left")], 5.08, 5.08, in_bom=False, on_board=False)
define_symbol("CONN_1X2", [("1", "PIN_1", "passive", "left"), ("2", "PIN_2", "passive", "left")], 10.16, 7.62)
define_symbol("CONN_2X10", [(str(pin), f"PIN_{pin}", "passive", "left" if pin % 2 else "right") for pin in range(1, 21)], 20.32, 27.94)
define_symbol("CONN_2X12", [(str(pin), f"PIN_{pin}", "passive", "left" if pin % 2 else "right") for pin in range(1, 25)], 20.32, 33.02)
define_symbol("CONN_2X5", [(str(pin), f"PIN_{pin}", "passive", "left" if pin % 2 else "right") for pin in range(1, 11)], 15.24, 15.24)
define_symbol("CONN_1X8", [(str(pin), f"PIN_{pin}", "passive", "left") for pin in range(1, 9)], 12.7, 22.86)
define_symbol("TSR2_2450N", [("1", "VIN", "power_in", "left"), ("2", "0V", "power_in", "left"), ("3", "VOUT", "power_out", "right")], 17.78, 10.16)
define_symbol("LM27761", [
    ("1", "C1+", "passive", "left"), ("2", "VIN", "power_in", "left"),
    ("3", "C1-", "passive", "left"), ("4", "0V", "power_in", "left"),
    ("5", "EN", "input", "left"), ("6", "VOUT", "power_out", "right"),
    ("7", "VFB", "input", "right"), ("8", "CPOUT", "power_out", "right"),
], 20.32, 17.78)
define_symbol("DAC8568C", [
    ("1", "LDAC", "input", "left"), ("2", "SYNC", "input", "left"),
    ("3", "AVDD", "power_in", "left"), ("8", "VREF", "passive", "left"),
    ("9", "CLR", "input", "left"), ("14", "0V", "power_in", "left"),
    ("15", "DIN", "input", "left"), ("16", "SCLK", "input", "left"),
    ("4", "VOUTA", "output", "right"), ("13", "VOUTB", "output", "right"),
    ("5", "VOUTC", "output", "right"), ("12", "VOUTD", "output", "right"),
    ("6", "VOUTE", "output", "right"), ("11", "VOUTF", "output", "right"),
    ("7", "VOUTG", "output", "right"), ("10", "VOUTH", "output", "right"),
], 25.4, 40.64)
define_symbol("OPA4197", [
    ("3", "A+", "input", "left"), ("2", "A-", "input", "left"),
    ("5", "B+", "input", "left"), ("6", "B-", "input", "left"),
    ("10", "C+", "input", "left"), ("9", "C-", "input", "left"),
    ("12", "D+", "input", "left"), ("13", "D-", "input", "left"),
    ("4", "V+", "power_in", "left"), ("11", "V-", "power_in", "left"),
    ("1", "OUTA", "output", "right"), ("7", "OUTB", "output", "right"),
    ("8", "OUTC", "output", "right"), ("14", "OUTD", "output", "right"),
], 25.4, 27.94)
define_symbol("74AHCT244", [
    ("1", "1OE", "input", "left"), ("19", "2OE", "input", "left"),
    ("2", "1A0", "input", "left"), ("4", "1A1", "input", "left"),
    ("6", "1A2", "input", "left"), ("8", "1A3", "input", "left"),
    ("17", "2A0", "input", "left"), ("15", "2A1", "input", "left"),
    ("13", "2A2", "input", "left"), ("11", "2A3", "input", "left"),
    ("10", "0V", "power_in", "left"), ("20", "VCC", "power_in", "left"),
    ("18", "1Y0", "output", "right"), ("16", "1Y1", "output", "right"),
    ("14", "1Y2", "output", "right"), ("12", "1Y3", "output", "right"),
    ("3", "2Y0", "output", "right"), ("5", "2Y1", "output", "right"),
    ("7", "2Y2", "output", "right"), ("9", "2Y3", "output", "right"),
], 25.4, 30.48)
define_symbol("LM393B", [
    ("2", "1-", "input", "left"), ("3", "1+", "input", "left"),
    ("5", "2+", "input", "left"), ("6", "2-", "input", "left"),
    ("4", "0V", "power_in", "left"), ("8", "VCC", "power_in", "left"),
    ("1", "OUT1", "open_collector", "right"), ("7", "OUT2", "open_collector", "right"),
], 20.32, 17.78)
define_symbol("TLV75533", [
    ("1", "IN", "power_in", "left"), ("2", "GND", "power_in", "left"),
    ("3", "EN", "input", "left"), ("4", "NC", "passive", "right"),
    ("5", "OUT", "power_out", "right"),
], 15.24, 12.7)
define_symbol("CY15B104QN", [
    ("1", "/CS", "input", "left"), ("3", "/WP", "input", "left"),
    ("4", "VSS", "power_in", "left"), ("5", "SI", "input", "left"),
    ("6", "SCK", "input", "left"), ("7", "DNU", "passive", "left"),
    ("2", "SO", "output", "right"), ("8", "VDD", "power_in", "right"),
], 20.32, 20.32)

mcu_pin_names = {
    1: "VBAT", 2: "PC13", 3: "PC14/OSC32_IN", 4: "PC15/OSC32_OUT",
    5: "PH0/OSC_IN", 6: "PH1/OSC_OUT", 7: "NRST", 8: "PC0", 9: "PC1",
    10: "PC2", 11: "PC3", 12: "VSSA/VREF-", 13: "VDDA/VREF+", 14: "PA0",
    15: "PA1", 16: "PA2", 17: "PA3", 18: "VSS", 19: "VDD", 20: "PA4",
    21: "PA5", 22: "PA6", 23: "PA7", 24: "PC4", 25: "PC5", 26: "PB0",
    27: "PB1", 28: "PB2", 29: "PB10", 30: "VCAP_1", 31: "VSS", 32: "VDD",
    33: "PB12", 34: "PB13", 35: "PB14", 36: "PB15", 37: "PC6", 38: "PC7",
    39: "PC8", 40: "PC9", 41: "PA8", 42: "PA9", 43: "PA10", 44: "PA11",
    45: "PA12", 46: "PA13/SWDIO", 47: "VSS", 48: "VDD", 49: "PA14/SWCLK",
    50: "PA15", 51: "PC10", 52: "PC11", 53: "PC12", 54: "PD2", 55: "PB3/SWO",
    56: "PB4", 57: "PB5", 58: "PB6", 59: "PB7", 60: "BOOT0", 61: "PB8",
    62: "PB9", 63: "VSS", 64: "VDD",
}
mcu_power_pins = {1, 12, 13, 18, 19, 31, 32, 47, 48, 63, 64}
mcu_pins = []
for pin in range(1, 65):
    pin_type = "power_in" if pin in mcu_power_pins else "bidirectional"
    if pin == 30:
        pin_type = "power_out"
    elif pin in (7, 60):
        pin_type = "input"
    side = "left" if pin <= 32 else "right"
    mcu_pins.append((str(pin), mcu_pin_names[pin], pin_type, side))
define_symbol("STM32F411RET6", mcu_pins, 35.56, 83.82)

display_names = {
    1: "VSS", 2: "VSS", 3: "VDD", 4: "VDD", 5: "/SCS", 6: "SDO", 7: "SDI", 8: "SCLK",
    9: "WAIT", 10: "INT", 11: "/RESET", 12: "NC", 13: "VSS", 14: "BL_CONTROL",
    **{pin: f"DB{pin - 15}" for pin in range(15, 31)}, 31: "VSS", 32: "RTP_CS", 33: "TP_INT",
    34: "TP_DATA", 35: "TP_CLK", 36: "TP_RESET", 37: "VDD", 38: "VDD", 39: "VSS", 40: "VSS",
}
display_pins = []
for pin in range(1, 41):
    pin_type = "passive"
    if pin in (5, 7, 8, 11, 14):
        pin_type = "input"
    elif pin in (6, 9, 10):
        pin_type = "output"
    display_pins.append((str(pin), display_names[pin], pin_type, "left" if pin % 2 else "right"))
define_symbol("ER_TFT070A2", display_pins, 35.56, 55.88)


add_section("POWER INPUT AND RAILS", 20, 15)
add_component("PWR_FLAG", "#FLG01", "+12V SOURCE", 25, 55, {"1": "+12V_A"})
add_component("PWR_FLAG", "#FLG02", "0V SOURCE", 25, 70, {"1": "GND"})
add_component("PWR_FLAG", "#FLG03", "DISPLAY 5V SOURCE", 25, 85, {"1": "+5V_DISPLAY"})
add_component("PWR_FLAG", "#FLG04", "ANALOG 5V SOURCE", 25, 100, {"1": "+5V_ANALOG"})
add_component("PWR_FLAG", "#FLG05", "MCU ANALOG 3V3 SOURCE", 25, 115, {"1": "+3V3_MCU_A"})
add_component("CONN_1X2", "J20", "SWITCHED 12V CASE HARNESS", 55, 32, {"1": "12V_SW", "2": "GND"}, "Connector_Molex:Molex_Micro-Fit_3.0_43650-0200_1x02_P3.00mm_Horizontal")
add_two_pin("R", "R", "PTC 1.1A", 100, 32, "12V_SW", "12V_FUSED", "Fuse:Fuse_1206_3216Metric")
add_two_pin("D", "D", "SS34", 130, 32, "12V_FUSED", "+12V_A", "Diode_SMD:D_SMA")
add_two_pin("D", "D", "SMBJ15A", 130, 45, "+12V_A", "GND", "Diode_SMD:D_SMB")
add_two_pin("C", "C", "100u/25V", 130, 56, "+12V_A", "GND", "Capacitor_SMD:C_Elec_8x10.2")
add_two_pin("C", "C", "22u/50V", 130, 67, "+12V_A", "GND", "Capacitor_SMD:C_Elec_6.3x7.7")
add_component("TSR2_2450N", "U7", "TSR 2-2450N", 72, 65, {"1": "+12V_A", "2": "GND", "3": "+5V"}, "Converter_DCDC:Converter_DCDC_TRACO_TSR2-24xxN_TSR2-24xxxN_THT")
add_two_pin("R", "R", "FB 600R@100MHz", 102, 80, "+5V", "+5V_DISPLAY", "Inductor_SMD:L_1206_3216Metric")
add_two_pin("R", "R", "FB 600R@100MHz", 102, 91, "+5V", "+5V_ANALOG", "Inductor_SMD:L_1206_3216Metric")
add_two_pin("C", "C", "470u/10V", 130, 80, "+5V_DISPLAY", "GND", "Capacitor_SMD:C_Elec_8x10.2")
add_component("LM27761", "U8", "LM27761DSGR", 65, 115, {
    "1": "LM_C1P", "2": "+5V", "3": "LM_C1N", "4": "GND", "5": "+5V",
    "6": "-3V3_A", "7": "LM_FB", "8": "LM_CPOUT",
}, "Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm_ThermalVias")
add_two_pin("C", "C", "1u", 105, 106, "LM_C1P", "LM_C1N", "Capacitor_SMD:C_0603_1608Metric")
add_two_pin("C", "C", "4.7u", 105, 117, "+5V", "GND", "Capacitor_SMD:C_0805_2012Metric")
add_two_pin("C", "C", "4.7u", 105, 128, "LM_CPOUT", "GND", "Capacitor_SMD:C_0805_2012Metric")
add_two_pin("C", "C", "2.2u", 105, 139, "-3V3_A", "GND", "Capacitor_SMD:C_0805_2012Metric")
add_two_pin("R", "R", "856k 1%", 135, 112, "-3V3_A", "LM_FB", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "500k 1%", 135, 123, "LM_FB", "GND", "Resistor_SMD:R_0603_1608Metric")


add_section("STM32 AND DISPLAY", 170, 15)
mcu_nets = {
    "1": "+3V3", "7": "MCU_NRST", "8": "GATE1_MCU", "9": "GATE2_MCU",
    "10": "GATE3_MCU", "11": "GATE4_MCU", "12": "GND", "13": "+3V3_MCU_A",
    "14": "CHANNEL_LED_DATA_MCU", "15": "CHANNEL_BUTTON_DATA_MCU",
    "16": "CONTROL_LED_DATA_MCU", "17": "CONTROL_BUTTON_DATA_MCU",
    "18": "GND", "19": "+3V3", "20": "DISP_CS_MCU", "21": "DISP_SCK_MCU",
    "22": "DISPLAY_MISO", "23": "DISP_MOSI_MCU", "24": "GATE5_MCU", "25": "GATE6_MCU",
    "26": "DISPLAY_RESET", "27": "STEP_LED_DATA_MCU", "28": "STEP_BUTTON_DATA_MCU",
    "29": "DISPLAY_BACKLIGHT", "30": "MCU_VCAP", "31": "GND",
    "32": "+3V3", "33": "DAC_SYNC_MCU", "34": "DAC_SCLK_MCU", "35": "DAC_LDAC_MCU",
    "36": "DAC_MOSI_MCU", "37": "GATE7_MCU", "38": "GATE8_MCU", "39": "CLOCK_OUT_MCU",
    "40": "CLOCK_IN_LOGIC", "41": "LED_BLANK_MCU", "43": "RESET_IN_LOGIC",
    "46": "SWDIO", "47": "GND", "48": "+3V3", "49": "SWCLK",
    "51": "FRAM_SCK", "52": "FRAM_MISO", "53": "FRAM_MOSI", "55": "SWO",
    "58": "FRAM_CS", "60": "BOOT0", "61": "BUTTON_CLK_MCU",
    "62": "BUTTON_FRAME_MCU", "63": "GND", "64": "+3V3",
}
add_component(
    "STM32F411RET6",
    "U9",
    "STM32F411RET6",
    210,
    70,
    mcu_nets,
    "Package_QFP:LQFP-64_10x10mm_P0.5mm",
    "https://www.st.com/resource/en/datasheet/stm32f411re.pdf",
)
add_two_pin("R", "R", "33R", 275, 32, "DISP_CS_MCU", "DISPLAY_CS", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "33R", 275, 43, "DISP_SCK_MCU", "DISPLAY_SCK", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "33R", 275, 54, "DISP_MOSI_MCU", "DISPLAY_MOSI", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "10k", 275, 65, "+3V3", "DISPLAY_RESET", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "100k", 275, 76, "DISPLAY_BACKLIGHT", "GND", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "100k", 275, 87, "BUTTON_CLK_MCU", "GND", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "100k", 275, 98, "BUTTON_FRAME_MCU", "GND", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "10k", 275, 109, "+3V3", "LED_BLANK_MCU", "Resistor_SMD:R_0603_1608Metric")
add_component("R", "R69", "100k", 275, 120, {"1": "STEP_LED_DATA_MCU", "2": "GND"}, "Resistor_SMD:R_0603_1608Metric")
add_component("R", "R70", "100k", 275, 131, {"1": "CHANNEL_LED_DATA_MCU", "2": "GND"}, "Resistor_SMD:R_0603_1608Metric")
add_component("R", "R71", "100k", 275, 142, {"1": "CONTROL_LED_DATA_MCU", "2": "GND"}, "Resistor_SMD:R_0603_1608Metric")
display_nets = {
    "1": "GND", "2": "GND", "3": "+5V_DISPLAY", "4": "+5V_DISPLAY", "5": "DISPLAY_CS",
    "6": "DISPLAY_MISO", "7": "DISPLAY_MOSI", "8": "DISPLAY_SCK", "11": "DISPLAY_RESET",
    "13": "GND", "14": "DISPLAY_BACKLIGHT", "31": "GND", "37": "+5V_DISPLAY", "38": "+5V_DISPLAY",
    "39": "GND", "40": "GND",
}
add_component("ER_TFT070A2", "J23", "ER-TFT070A2-6-5633 HEADER", 340, 58, display_nets, "Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical")
for reference, value, x, prefix, led_data, button_data, resistor_base in (
    ("J26", "STEP BUTTON BOARD 16", 400, "STEP", "STEP_LED_DATA_MCU", "STEP_BUTTON_DATA_MCU", 72),
    ("J28", "CHANNEL BUTTON BOARD 8", 435, "CHANNEL", "CHANNEL_LED_DATA_MCU", "CHANNEL_BUTTON_DATA_MCU", 77),
    ("J29", "CONTROL BUTTON BOARD 15+", 470, "CONTROL", "CONTROL_LED_DATA_MCU", "CONTROL_BUTTON_DATA_MCU", 82),
):
    connector_nets = {
        "1": "+5V", "2": "+3V3", "3": "GND", "4": f"{prefix}_BUTTON_CLK",
        "5": f"{prefix}_BUTTON_FRAME", "6": f"{prefix}_LED_BLANK",
        "7": f"{prefix}_LED_DATA", "8": f"{prefix}_BUTTON_DATA",
    }
    add_component(
        "CONN_1X8",
        reference,
        value,
        x,
        58,
        connector_nets,
        "Connector_JST:JST_XH_B8B-XH-A_1x08_P2.50mm_Vertical",
    )
    series_connections = (
        ("33R", "BUTTON_CLK_MCU", f"{prefix}_BUTTON_CLK"),
        ("33R", "BUTTON_FRAME_MCU", f"{prefix}_BUTTON_FRAME"),
        ("33R", "LED_BLANK_MCU", f"{prefix}_LED_BLANK"),
        ("33R", led_data, f"{prefix}_LED_DATA"),
        ("100R", f"{prefix}_BUTTON_DATA", button_data),
    )
    for offset, (value, net_a, net_b) in enumerate(series_connections):
        add_component(
            "R",
            f"R{resistor_base + offset}",
            value,
            x,
            82 + offset * 10,
            {"1": net_a, "2": net_b},
            "Resistor_SMD:R_0603_1608Metric",
        )

add_component("TLV75533", "U10", "TLV75533PDBVR", 340, 120, {
    "1": "+5V", "2": "GND", "3": "+5V", "5": "+3V3",
}, "Package_TO_SOT_SMD:SOT-23-5", "https://www.ti.com/lit/ds/symlink/tlv755p.pdf")
add_component("C", "C20", "1u", 375, 108, {"1": "+5V", "2": "GND"}, "Capacitor_SMD:C_0603_1608Metric")
add_component("C", "C21", "1u", 375, 118, {"1": "+3V3", "2": "GND"}, "Capacitor_SMD:C_0603_1608Metric")
add_component("C", "C22", "4.7u", 375, 128, {"1": "+3V3", "2": "GND"}, "Capacitor_SMD:C_0805_2012Metric")
for index, x in enumerate((420, 445, 470, 495), 23):
    add_component("C", f"C{index}", "100n MCU VDD", x, 108, {"1": "+3V3", "2": "GND"}, "Capacitor_SMD:C_0603_1608Metric")
add_component("C", "C27", "100n VBAT", 420, 118, {"1": "+3V3", "2": "GND"}, "Capacitor_SMD:C_0603_1608Metric")
add_component("R", "R68", "FB 600R@100MHz", 445, 118, {"1": "+3V3", "2": "+3V3_MCU_A"}, "Inductor_SMD:L_0603_1608Metric")
add_component("C", "C28", "100n VDDA", 470, 118, {"1": "+3V3_MCU_A", "2": "GND"}, "Capacitor_SMD:C_0603_1608Metric")
add_component("C", "C29", "1u VDDA", 495, 118, {"1": "+3V3_MCU_A", "2": "GND"}, "Capacitor_SMD:C_0603_1608Metric")
add_component("C", "C30", "4.7u VCAP", 420, 128, {"1": "MCU_VCAP", "2": "GND"}, "Capacitor_SMD:C_0805_2012Metric")
add_component("R", "R66", "10k", 445, 128, {"1": "+3V3", "2": "MCU_NRST"}, "Resistor_SMD:R_0603_1608Metric")
add_component("C", "C31", "100n NRST", 470, 128, {"1": "MCU_NRST", "2": "GND"}, "Capacitor_SMD:C_0603_1608Metric")
add_component("R", "R67", "10k", 495, 128, {"1": "BOOT0", "2": "GND"}, "Resistor_SMD:R_0603_1608Metric")
add_component("SWITCH", "SW2", "RESET", 530, 108, {"1": "MCU_NRST", "2": "GND"}, "Button_Switch_SMD:SW_SPST_EVQPE1")
add_component("SWITCH", "SW3", "BOOT0", 530, 123, {"1": "+3V3", "2": "BOOT0"}, "Button_Switch_SMD:SW_SPST_EVQPE1")
add_component("CONN_2X5", "J27", "CORTEX SWD 10-PIN", 565, 118, {
    "1": "+3V3", "2": "SWDIO", "3": "GND", "4": "SWCLK", "5": "GND",
    "6": "SWO", "9": "GND", "10": "MCU_NRST",
}, "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical")
add_section("F-RAM PRESET STORAGE", 325, 150)
add_component("CY15B104QN", "U11", "CY15B104QN-50SXI", 360, 165, {
    "1": "FRAM_CS", "2": "FRAM_MISO", "3": "+3V3", "4": "GND",
    "5": "FRAM_MOSI", "6": "FRAM_SCK", "7": "+3V3", "8": "+3V3",
}, "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", "https://www.infineon.com/assets/row/public/documents/10/49/infineon-cy15b104qn-cy15v104qn-4-mb-excelon-lp-ferroelectric-ram-f-ram-serial-spi-512k-8-industrial-datasheet-en.pdf")
add_component("C", "C32", "100n", 400, 150, {"1": "+3V3", "2": "GND"}, "Capacitor_SMD:C_0603_1608Metric")
add_component("C", "C33", "1u", 425, 150, {"1": "+3V3", "2": "GND"}, "Capacitor_SMD:C_0603_1608Metric")
add_component("R", "R87", "10k", 450, 150, {"1": "+3V3", "2": "FRAM_CS"}, "Resistor_SMD:R_0603_1608Metric")
add_component("R", "R88", "100k", 475, 150, {"1": "FRAM_SCK", "2": "GND"}, "Resistor_SMD:R_0603_1608Metric")
add_component("R", "R89", "100k", 500, 150, {"1": "FRAM_MOSI", "2": "GND"}, "Resistor_SMD:R_0603_1608Metric")


add_section("DAC AND 0-10V CV OUTPUTS", 20, 175)
add_component("DAC8568C", "U1", "DAC8568ICPW", 70, 225, {
    "1": "DAC_LDAC_5V", "2": "DAC_SYNC_5V", "3": "+5V_ANALOG", "4": "DAC_OUT1",
    "5": "DAC_OUT3", "6": "DAC_OUT5", "7": "DAC_OUT7", "8": "DAC_VREF", "9": "+5V_ANALOG",
    "10": "DAC_OUT8", "11": "DAC_OUT6", "12": "DAC_OUT4", "13": "DAC_OUT2", "14": "GND",
    "15": "DAC_MOSI_5V", "16": "DAC_SCLK_5V",
}, "Package_SO:TSSOP-16_4.4x5mm_P0.65mm", "https://www.ti.com/lit/ds/symlink/dac8568.pdf")
add_two_pin("C", "C", "1u C0G", 120, 190, "DAC_VREF", "GND", "Capacitor_SMD:C_0805_2012Metric")
add_two_pin("C", "C", "100n", 120, 201, "+5V_ANALOG", "GND", "Capacitor_SMD:C_0603_1608Metric")

add_component("74AHCT244", "U5", "74AHCT244D", 70, 285, {
    "1": "GND", "19": "GND", "2": "DAC_SCLK_MCU", "4": "DAC_MOSI_MCU", "6": "DAC_SYNC_MCU",
    "8": "DAC_LDAC_MCU", "17": "CLOCK_OUT_MCU", "15": "GND", "13": "GND", "11": "GND",
    "10": "GND", "20": "+5V", "18": "DAC_SCLK_5V", "16": "DAC_MOSI_5V", "14": "DAC_SYNC_5V",
    "12": "DAC_LDAC_5V", "3": "CLOCK_OUT_5V",
}, "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm")
add_two_pin("C", "C", "100n", 120, 274, "+5V", "GND", "Capacitor_SMD:C_0603_1608Metric")

for chip, first_channel, x, y in (("U2", 1, 190, 245), ("U3", 5, 390, 245)):
    nets = {"4": "+12V_A", "11": "-3V3_A"}
    channel_pins = (("3", "2", "1"), ("5", "6", "7"), ("10", "9", "8"), ("12", "13", "14"))
    for offset, (plus_pin, minus_pin, output_pin) in enumerate(channel_pins):
        channel = first_channel + offset
        nets[plus_pin] = f"DAC_OUT{channel}"
        nets[minus_pin] = f"CV_FB{channel}"
        nets[output_pin] = f"CV_RAW{channel}"
    add_component("OPA4197", chip, "OPA4197ID", x, y, nets, "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm")

for channel in range(1, 9):
    column = 0 if channel <= 4 else 1
    row = (channel - 1) % 4
    x = 245 + column * 200
    y = 190 + row * 38
    add_two_pin("R", "R", "10k 0.05%", x, y, f"CV_RAW{channel}", f"CV_FB{channel}", "Resistor_SMD:R_0603_1608Metric")
    add_two_pin("R", "R", "10k 0.05%", x, y + 10, f"CV_FB{channel}", "GND", "Resistor_SMD:R_0603_1608Metric")
    add_two_pin("R", "R", "1k 0.1%", x + 45, y, f"CV_RAW{channel}", f"CV_OUT{channel}", "Resistor_SMD:R_0805_2012Metric")
    add_component("TESTPOINT", next_reference("TP"), f"CV{channel}_RAW", x + 45, y + 10, {"1": f"CV_RAW{channel}"}, "TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm")

add_two_pin("C", "C", "100n", 190, 275, "+12V_A", "GND", "Capacitor_SMD:C_0603_1608Metric")
add_two_pin("C", "C", "100n", 190, 286, "-3V3_A", "GND", "Capacitor_SMD:C_0603_1608Metric")
add_two_pin("C", "C", "100n", 390, 275, "+12V_A", "GND", "Capacitor_SMD:C_0603_1608Metric")
add_two_pin("C", "C", "100n", 390, 286, "-3V3_A", "GND", "Capacitor_SMD:C_0603_1608Metric")


add_section("GATE AND CLOCK OUTPUTS", 600, 15)
gate_buffer_nets = {"1": "GND", "19": "GND", "10": "GND", "20": "+5V"}
gate_pairs = (("2", "18"), ("4", "16"), ("6", "14"), ("8", "12"), ("17", "3"), ("15", "5"), ("13", "7"), ("11", "9"))
for channel, (input_pin, output_pin) in enumerate(gate_pairs, 1):
    gate_buffer_nets[input_pin] = f"GATE{channel}_MCU"
    gate_buffer_nets[output_pin] = f"GATE{channel}_5V"
add_component("74AHCT244", "U4", "74AHCT244D", 650, 55, gate_buffer_nets, "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm")
add_two_pin("C", "C", "100n", 700, 31, "+5V", "GND", "Capacitor_SMD:C_0603_1608Metric")
for channel in range(1, 9):
    y = 83 + (channel - 1) * 12
    add_two_pin("R", "R", "100k", 625, y, f"GATE{channel}_MCU", "GND", "Resistor_SMD:R_0603_1608Metric")
    add_two_pin("R", "R", "1k", 675, y, f"GATE{channel}_5V", f"GATE_OUT{channel}", "Resistor_SMD:R_0805_2012Metric")
add_two_pin("R", "R", "100k", 625, 181, "CLOCK_OUT_MCU", "GND", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "1k", 675, 181, "CLOCK_OUT_5V", "CLOCK_OUT_JACK", "Resistor_SMD:R_0805_2012Metric")


add_section("CLOCK AND RESET INPUTS", 600, 215)
add_component("LM393B", "U6", "LM393BIDR", 770, 275, {
    "2": "SYNC_REF", "3": "CLOCK_SENSE", "5": "RESET_SENSE", "6": "SYNC_REF",
    "4": "GND", "8": "+5V", "1": "CLOCK_IN_LOGIC", "7": "RESET_IN_LOGIC",
}, "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
add_two_pin("C", "C", "100n", 770, 305, "+5V", "GND", "Capacitor_SMD:C_0603_1608Metric")

for name, input_net, sense_net, output_net, x, y in (
    ("CLOCK", "CLOCK_IN_JACK", "CLOCK_SENSE", "CLOCK_IN_LOGIC", 655, 235),
    ("RESET", "RESET_IN_JACK", "RESET_SENSE", "RESET_IN_LOGIC", 655, 305),
):
    add_two_pin("R", "R", "100k", x, y, input_net, sense_net, "Resistor_SMD:R_0603_1608Metric")
    add_two_pin("R", "R", "33k", x, y + 10, sense_net, "GND", "Resistor_SMD:R_0603_1608Metric")
    add_two_pin("C", "C", "1n C0G", x, y + 20, sense_net, "GND", "Capacitor_SMD:C_0603_1608Metric")
    add_two_pin("D", "D", "BAT54", x + 35, y, sense_net, "+3V3", "Diode_SMD:D_SOD-323")
    add_two_pin("D", "D", "BAT54", x + 35, y + 10, "GND", sense_net, "Diode_SMD:D_SOD-323")
    add_two_pin("R", "R", "1M", x + 35, y + 20, output_net, sense_net, "Resistor_SMD:R_0603_1608Metric")
    add_two_pin("R", "R", "10k", x + 70, y, "+3V3", output_net, "Resistor_SMD:R_0603_1608Metric")

add_two_pin("R", "R", "49.9k", 660, 370, "+3V3", "SYNC_REF", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("R", "R", "10k", 705, 370, "SYNC_REF", "GND", "Resistor_SMD:R_0603_1608Metric")
add_two_pin("C", "C", "100n", 750, 370, "SYNC_REF", "GND", "Capacitor_SMD:C_0603_1608Metric")


add_section("PASSIVE JACK BOARD INTERCONNECTS", 600, 405)
cv_panel_nets = {str(channel * 2 - 1): f"CV_OUT{channel}" for channel in range(1, 9)}
cv_panel_nets.update({str(pin): "GND" for pin in range(2, 21, 2)})
add_component(
    "CONN_2X10",
    "J24",
    "CV JACK BOARD",
    670,
    440,
    cv_panel_nets,
    "Connector_IDC:IDC-Header_2x10_P2.54mm_Vertical",
)

digital_panel_signals = [
    *(f"GATE_OUT{channel}" for channel in range(1, 9)),
    "CLOCK_OUT_JACK",
    "CLOCK_IN_JACK",
    "RESET_IN_JACK",
]
digital_panel_nets = {str(index * 2 - 1): net for index, net in enumerate(digital_panel_signals, 1)}
digital_panel_nets.update({str(pin): "GND" for pin in range(2, 25, 2)})
add_component(
    "CONN_2X12",
    "J25",
    "GATE CLOCK RESET JACK BOARD",
    760,
    440,
    digital_panel_nets,
    "Connector_IDC:IDC-Header_2x12_P2.54mm_Vertical",
)


library = "\n".join(symbol_definition(name, symbol) for name, symbol in symbols.items())
external_library = "\n".join(symbol_definition(name, symbol, qualified=False) for name, symbol in symbols.items())
external_library = "\n".join(line[1:] if line.startswith("\t") else line for line in external_library.splitlines())
SYMBOL_LIBRARY_OUTPUT.write_text(f"""(kicad_symbol_lib
\t(version 20231120)
\t(generator "kicad_symbol_editor")
{external_library}
)\n""")
content = f"""(kicad_sch
\t(version 20260306)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "{ROOT_UUID}")
\t(paper "A1")
\t(title_block
\t\t(title "SEQ-08 Desktop Sequencer Revision A")
\t\t(date "2026-07-17")
\t\t(rev "A")
\t\t(company "SEQ-08")
\t\t(comment 1 "Eight 0-10 V CV outputs, eight 5 V gates, clock I/O, reset input")
\t\t(comment 2 "STM32F411RET6 and ER-TFT070A2-6-5633, 4-wire SPI, no touch")
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
)\n"""
SCHEMATIC_OUTPUT.write_text(content)
