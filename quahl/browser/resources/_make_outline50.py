from pathlib import Path

FILENAME_PATTERN = "*_outline.svg"
FILENAME_RENAME_SEARCH = "_outline.svg"
FILENAME_RENAME_REPLACE = "_outline50.svg"

EXCEPTIONS = (
    "app",
    "quahl",
)


def edit_opacity(source: str):
    source = source.replace("stroke-opacity:1", "stroke-opacity:0.5")
    source = source.replace("stroke-width:4", "stroke-width:1")
    return source.replace("fill-opacity:1", "fill-opacity:0.5")


def main():
    dir = Path("./")
    for path in dir.glob(FILENAME_PATTERN):
        print(path, "-> ", end="", flush=False)
        if str(path).removeprefix("icon_").removesuffix(FILENAME_RENAME_SEARCH) in EXCEPTIONS:
            print("IGNORED")
            continue
        svg_source = path.read_text()
        svg_edited = edit_opacity(svg_source)
        new_path = Path(str(path).replace(FILENAME_RENAME_SEARCH, FILENAME_RENAME_REPLACE))
        new_path.write_text(svg_edited)
        print(new_path)


if __name__ == "__main__":
    main()
