"""Move managed grassland from each filter's exclude list to its include list.

Usage: python tools/review/grass_filters.py <ftwd>/configs/filters [--apply]
Dry run prints, per filter, what moves and what grassland stays excluded.
"""

import re
import sys
from pathlib import Path

GRASS = re.compile(
    r"pasture|meadow|grassland|grass|ley\b|grünland|gras|gräs|wiese|weide|mähder|prairie|fourrage|"
    r"pastizal|pasto|trávn|tráv|lúk|pievos|þolës|grasland|raaigras|zwenkgras|beemdgras|timothy|"
    r"fescue|ryegrass|bluegrass|bentgrass|foxtail|oatgrass|hairgrass|brome|bromus",
    re.I,
)
# What stays background everywhere: rough, semi-natural, wooded, alpine and common grazing;
# strips, margins and buffers; turf, energy and cover grasses; fallow and out-of-production.
KEEP_OUT = (
    r"alpine|alm\b|almen|almweide|summer|sömmerung|mountain|montane|berg|hutweide|common|"
    r"gemeinschaft|forest|wald|wood|bush|shrub|pastoral|karst|rough|natural|nature|natur|heide|"
    r"heath|litter|streu|reed canary|rietzwenk|switch|energy|energie|elephant|miscanthus|silvergrass|"
    r"turf|sod\b|graszoden|afforest|aufforst|borehole|margin|edge|strip|rand,|halfa|lemon|"
    r"grass-poor|mosaic|restoration|protection|uncultivated|green cover|green manure|groenbedekker|"
    r"groenbemesting|vanggewas|not eligible|nicht beitrag|aus der erzeugung|unused|degraded|fen\b|moor|"
    r"ripar|uferwiese|riverside|altgras|non-agricultural|henyard|pigs|brache|fallow|diversity|"
    r"special-aid|environmental agreement|wiesenknopf|\(typ [a-g]\)|type [a-g]\)|nff|out of production|"
    r"etablierten lokalen|does not go|seed|samen|certified|trees|glanzgr|riesenweizen|"
    r"hoofdfunctie natuur|groenbemester|randen"
)
# Grassland a keep-out word catches by accident (e.g. "ohne Sömmerungsweiden").
FORCE_IN = {
    "switzerland_filter.yaml": r"^(616|Weiden \(Heimweiden)",
    "france_filter.yaml": r"^(PPH|PAT)$",
    "sweden_filter.yaml": r"^(49|50)$",
}
# Grass grown for seed is already field in most filters; where a filter excluded it, it stays as is.
EXTRA_KEEP_OUT = {
    "austria_filter.yaml": r"^(704|707|708|721|722|723|992)$",
    "france_filter.yaml": r"^(SPH|SPL|SIN|SNU|MSW|GRA)$",
    "croatia_filter.yaml": r"^321$",
    "portugal_filter.yaml": r"^(280|283|289)$",
    "sweden_filter.yaml": r"^(52|54|55|61|63|89|90|95)$",
    "denmark_filter.yaml": r"^(248|249|269|270|287|326|327|335|336|488|596|597)$",
    "finland_filter.yaml": r"^(4904|4905|6051|6300|6303|6304|6305|6307|6308|6600|6710|6720|9405|9409|9424|9425|9621|9801|9805|9810)$",
    "slovenia_filter.yaml": r"^(202|722)$",
    "latvia_filter.yaml": r"^(641|642)$",
    "de-bb-nds-nrw_filter.yaml": r"^(\"?093\"?|93|453|458|465|467|492|592|768|972)$",
    "de-mv-filter.yaml": r"^AGL$",
    "czechia_filter.yaml": r"^(\"?(348|349|457|40114|471|40286|556|40062)\"?)$",
    "switzerland_filter.yaml": r"^(618|621|622|623|625|635|698|851|930|933|935|936)$",
}
FILTERS = [
    "austria_filter.yaml", "be-flanders_filter.yaml", "be-wallonia_filter.yaml",
    "switzerland_filter.yaml", "de-bb-nds-nrw_filter.yaml", "de-by-filter.yaml",
    "de-mv-filter.yaml", "de-sh-filter.yaml", "de-sl-filter.yaml", "de-th-filter.yaml",
    "denmark_filter.yaml", "estonia_filter.yaml", "finland_filter.yaml", "france_filter.yaml",
    "croatia_filter.yaml", "latvia_filter.yaml", "lithuania_filter.yaml",
    "netherlands_filter.yaml", "portugal_filter.yaml", "sweden_filter.yaml",
    "slovakia_filter.yaml", "slovenia_filter.yaml", "czechia_filter.yaml", "es_cat_filter.yaml",
]
LINE = re.compile(r'^\s*-\s*("(?:[^"\\]|\\.)*"|[^#\n]+?)\s*(?:#\s*(.*))?$')
BLOCK = "  # Managed grassland: meadows, pastures and leys (see docs/grassland-review.md)\n"


def plan(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    section, move, stay = None, [], []
    for i, line in enumerate(lines):
        if re.match(r"^[a-z_]+:", line):
            section = line.split(":")[0]
            continue
        m = LINE.match(line)
        if section != "exclude" or not m:
            continue
        value, comment = m.group(1).strip(), (m.group(2) or "")
        bare = value.strip('"')
        text = f"{value} {comment}"
        force = FORCE_IN.get(path.name)
        if force and re.match(force, bare):
            move.append(i)
            continue
        if not GRASS.search(text):
            continue
        extra = EXTRA_KEEP_OUT.get(path.name)
        if re.search(KEEP_OUT, text, re.I) or (extra and re.match(extra, bare)):
            stay.append(line.strip())
        else:
            move.append(i)
    return lines, move, stay


def apply(path: Path, lines, move):
    moved = [lines[i] for i in move]
    kept = [line for i, line in enumerate(lines) if i not in set(move)]
    at = next(i for i, line in enumerate(kept) if line.startswith("exclude:"))
    while at > 0 and not kept[at - 1].strip():
        at -= 1
    kept[at:at] = ["\n", BLOCK, *moved]
    path.write_text("".join(kept), encoding="utf-8")


def main():
    root = Path(sys.argv[1])
    for name in FILTERS:
        path = root / name
        lines, move, stay = plan(path)
        print(f"== {name}: move {len(move)}, keep out {len(stay)}")
        for i in move:
            print("   +", lines[i].strip()[:100])
        for s in stay:
            print("   -", s[:100])
        if "--apply" in sys.argv and move:
            apply(path, lines, move)


if __name__ == "__main__":
    main()
