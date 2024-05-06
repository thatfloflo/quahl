from pathlib import Path
import re


FILENAME_PATTERN = "*_outline50.svg"
FILENAME_RENAME_SEARCH = "_outline50.svg"
FILENAME_RENAME_REPLACE = "_outline50_d.svg"

EXCEPTIONS = (
    "app",
    "quahl",
)

EXCEPTIONS = tuple()

FIND_COLOURS_RE = re.compile(r"#[a-fA-F0-9]{6}")


def invert_hex_color(raw_col: str) -> str:
    try:
        col = raw_col.strip().removeprefix("#")
        r = "%x" % (0xFF - int(col[0:2], base=16))
        g = "%x" % (0xFF - int(col[2:4], base=16))
        b = "%x" % (0xFF - int(col[4:6], base=16))
        return f"#{r.zfill(2)}{g.zfill(2)}{b.zfill(2)}"
    except Exception:
        return raw_col


def invert_colors(source: str):
    found: set[str] = set(FIND_COLOURS_RE.findall(source))
    for original in found:
        inverted = invert_hex_color(original)
        print(f"... {original} -> {inverted}")
        source = source.replace(original, inverted)
    return source


def main():
    dir = Path("./")
    for path in dir.glob(FILENAME_PATTERN):
        new_path = Path(str(path).replace(FILENAME_RENAME_SEARCH, FILENAME_RENAME_REPLACE))
        print(path, "-> ", end="", flush=False)
        print(new_path)
        if str(path).removeprefix("icon_").removesuffix(FILENAME_RENAME_SEARCH) in EXCEPTIONS:
            print("... FILE IGNORED")
            continue
        svg_source = path.read_text()
        svg_edited = invert_colors(svg_source)
        new_path.write_text(svg_edited)


if __name__ == "__main__":
    main()
