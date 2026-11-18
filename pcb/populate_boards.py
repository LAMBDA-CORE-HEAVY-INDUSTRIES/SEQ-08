#!/usr/bin/env python3

from pathlib import Path
from subprocess import run
from sys import argv
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree

import pcbnew


ROOT = Path(__file__).parent
PROJECTS = (
    {
        "name": "seq08-io",
        "directory": ROOT / "seq08-io",
        "placement": "main",
        "copper_layers": 4,
        "local_libraries": {"SEQ08": ROOT / "seq08-io" / "seq08.pretty"},
    },
    {
        "name": "seq08-jacks",
        "directory": ROOT / "seq08-jacks",
        "placement": "jacks",
        "copper_layers": 2,
        "local_libraries": {},
    },
)


def load_footprint(identifier, local_libraries):
    library, name = identifier.split(":", 1)
    library_path = local_libraries.get(library, Path("/usr/share/kicad/footprints") / f"{library}.pretty")
    footprint = pcbnew.FootprintLoad(str(library_path), name)
    if footprint is None:
        raise RuntimeError(f"footprint not found: {identifier}")
    return footprint


def set_position(footprint, x, y, angle=0):
    footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    footprint.SetOrientationDegrees(angle)


def place_main(footprints):
    placements = {
        "J20": (126, 21, 0),
        "J23": (176, 25, 0),
        "J24": (38, 17, 90),
        "J25": (76, 17, 90),
        "J26": (105, 107, 0),
        "J28": (132, 107, 0),
        "J29": (158, 107, 0),
        "U1": (64, 47, 0),
        "U2": (31, 60, 0),
        "U3": (52, 60, 0),
        "U4": (76, 40, 0),
        "U5": (76, 61, 0),
        "U6": (105, 35, 0),
        "U7": (132, 42, 0),
        "U8": (148, 53, 0),
        "U9": (97, 62, 0),
        "U10": (127, 61, 0),
        "U11": (114, 61, 0),
        "J27": (88, 91, 0),
        "SW2": (78, 82, 0),
        "SW3": (96, 82, 0),
        "R1": (127, 25, 0),
        "R2": (143, 38, 0),
        "R3": (143, 42, 0),
        "R4": (154, 50, 0),
        "R5": (154, 54, 0),
        "R6": (164, 55, 90),
        "R7": (164, 59, 90),
        "R8": (164, 63, 90),
        "R9": (168, 55, 90),
        "R10": (168, 59, 90),
        "R11": (106, 75, 0),
        "R12": (110, 75, 0),
        "R13": (114, 75, 0),
        "R56": (96, 25, 0),
        "R57": (100, 25, 0),
        "R58": (108, 29, 0),
        "R59": (116, 25, 0),
        "R60": (96, 43, 0),
        "R61": (100, 43, 0),
        "R62": (108, 47, 0),
        "R63": (116, 43, 0),
        "R64": (112, 39, 0),
        "R65": (116, 39, 0),
        "R66": (87, 75, 0),
        "R67": (101, 75, 0),
        "R68": (106, 50, 0),
        "R69": (118, 75, 0),
        "R70": (122, 75, 0),
        "R71": (126, 75, 0),
        "R87": (112, 68, 0),
        "R88": (116, 68, 0),
        "R89": (120, 68, 0),
        "C1": (157, 24, 0),
        "C2": (157, 36, 0),
        "C3": (164, 44, 0),
        "C4": (142, 50, 0),
        "C5": (142, 54, 0),
        "C6": (142, 58, 0),
        "C7": (154, 58, 0),
        "C8": (61, 53, 0),
        "C9": (67, 53, 0),
        "C10": (84, 61, 0),
        "C11": (24, 52, 0),
        "C12": (24, 56, 0),
        "C13": (58, 68, 0),
        "C14": (62, 68, 0),
        "C15": (84, 40, 0),
        "C16": (111, 35, 0),
        "C17": (104, 25, 0),
        "C18": (104, 43, 0),
        "C19": (120, 35, 0),
        "C20": (132, 57, 0),
        "C21": (132, 61, 0),
        "C22": (132, 65, 0),
        "C23": (89, 54, 0),
        "C24": (105, 54, 0),
        "C25": (89, 70, 0),
        "C26": (105, 70, 0),
        "C27": (92, 50, 0),
        "C28": (110, 50, 0),
        "C29": (114, 50, 0),
        "C30": (97, 73, 0),
        "C31": (91, 75, 0),
        "C32": (122, 57, 0),
        "C33": (122, 61, 0),
        "D1": (135, 25, 0),
        "D2": (144, 25, 0),
        "D3": (108, 25, 0),
        "D4": (112, 25, 0),
        "D5": (108, 43, 0),
        "D6": (112, 43, 0),
    }
    for first_resistor, first_x in ((72, 97), (77, 127), (82, 150)):
        for offset in range(5):
            placements[f"R{first_resistor + offset}"] = (first_x + offset * 4, 99, 0)
    for channel in range(1, 9):
        x = 20 + (channel - 1) * 7
        first_resistor = 14 + (channel - 1) * 3
        placements[f"R{first_resistor}"] = (x, 74, 0)
        placements[f"R{first_resistor + 1}"] = (x, 78, 0)
        placements[f"R{first_resistor + 2}"] = (x, 83, 90)
        placements[f"TP{channel}"] = (x, 91, 0)
    for channel in range(1, 10):
        x = 60 + (channel - 1) * 4
        first_resistor = 38 + (channel - 1) * 2
        placements[f"R{first_resistor}"] = (x, 27, 0)
        placements[f"R{first_resistor + 1}"] = (x, 30, 0)

    missing = sorted(set(footprints) - set(placements))
    if missing:
        raise RuntimeError(f"main-board placement missing: {', '.join(missing)}")
    for reference, (x, y, angle) in placements.items():
        set_position(footprints[reference], x, y, angle)


def place_jacks(footprints):
    for channel in range(1, 9):
        footprints[f"J{channel}"].SetPosition(pcbnew.VECTOR2I_MM(25 + (channel - 1) * 15, 30))
        footprints[f"J{channel + 8}"].SetPosition(pcbnew.VECTOR2I_MM(25 + (channel - 1) * 15, 55))
    footprints["J17"].SetPosition(pcbnew.VECTOR2I_MM(25, 80))
    footprints["J18"].SetPosition(pcbnew.VECTOR2I_MM(45, 80))
    footprints["J19"].SetPosition(pcbnew.VECTOR2I_MM(65, 80))
    footprints["J24"].SetPosition(pcbnew.VECTOR2I_MM(105, 80))
    footprints["J25"].SetPosition(pcbnew.VECTOR2I_MM(140, 80))


def add_outline(board, left, top, right, bottom):
    for start, end in (
        ((left, top), (right, top)),
        ((right, top), (right, bottom)),
        ((right, bottom), (left, bottom)),
        ((left, bottom), (left, top)),
    ):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(pcbnew.VECTOR2I_MM(*start))
        edge.SetEnd(pcbnew.VECTOR2I_MM(*end))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(pcbnew.FromMM(0.05))
        board.Add(edge)


def add_mounting_holes(board, positions):
    library = Path("/usr/share/kicad/footprints/MountingHole.pretty")
    for index, position in enumerate(positions, 1):
        footprint = pcbnew.FootprintLoad(str(library), "MountingHole_3.2mm_M3")
        footprint.SetReference(f"H{index}")
        footprint.SetValue("M3 MOUNTING HOLE")
        footprint.SetBoardOnly(True)
        footprint.SetExcludedFromBOM(True)
        footprint.SetExcludedFromPosFiles(True)
        footprint.SetPosition(pcbnew.VECTOR2I_MM(*position))
        board.Add(footprint)


def add_mechanics(board, placement):
    if placement == "main":
        add_outline(board, 10, 10, 190, 114)
        add_mounting_holes(board, ((15, 15), (185, 15), (15, 109), (185, 109)))
    else:
        add_outline(board, 10, 15, 170, 115)
        add_mounting_holes(board, ((15, 20), (165, 20), (15, 110), (165, 110)))


def populate(project):
    directory = project["directory"]
    schematic_path = directory / f"{project['name']}.kicad_sch"
    board_path = directory / f"{project['name']}.kicad_pcb"
    replace = "--replace" in argv
    board = pcbnew.BOARD() if replace else pcbnew.LoadBoard(str(board_path))
    if board.GetFootprints():
        raise RuntimeError(f"{board_path} already contains footprints. Pass --replace to discard PCB edits")
    board.SetCopperLayerCount(project["copper_layers"])
    if project["placement"] == "main":
        board.GetDesignSettings().m_MinThroughDrill = pcbnew.FromMM(0.2)

    with NamedTemporaryFile(suffix=".xml") as netlist_file:
        run(
            [
                "kicad-cli",
                "sch",
                "export",
                "netlist",
                "--format",
                "kicadxml",
                "-o",
                netlist_file.name,
                str(schematic_path),
            ],
            check=True,
        )
        root = ElementTree.parse(netlist_file.name).getroot()

    footprints = {}
    for component in root.findall("./components/comp"):
        reference = component.attrib["ref"]
        footprint_identifier = component.findtext("footprint")
        if not footprint_identifier:
            raise RuntimeError(f"{reference} has no footprint")
        footprint = load_footprint(footprint_identifier, project["local_libraries"])
        footprint.SetReference(reference)
        footprint.SetValue(component.findtext("value", ""))
        timestamp = component.findtext("tstamps")
        footprint.SetPath(pcbnew.KIID_PATH(f"/{timestamp}"))
        board.Add(footprint)
        footprints[reference] = footprint

    nets = {}
    for net_element in root.findall("./nets/net"):
        name = net_element.attrib["name"]
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
        nets[name] = net
        for node in net_element.findall("node"):
            footprint = footprints[node.attrib["ref"]]
            pad = footprint.FindPadByNumber(node.attrib["pin"])
            if pad is None:
                raise RuntimeError(f"missing pad {node.attrib['ref']}.{node.attrib['pin']}")
            pad.SetNet(net)

    if project["placement"] == "main":
        place_main(footprints)
    else:
        place_jacks(footprints)
    add_mechanics(board, project["placement"])
    pcbnew.SaveBoard(str(board_path), board)
    print(f"Populated {board_path} with {len(footprints)} footprints and {len(nets)} nets")


requested_projects = {argument for argument in argv[1:] if not argument.startswith("--")}
for project in PROJECTS:
    if not requested_projects or project["name"] in requested_projects:
        populate(project)
