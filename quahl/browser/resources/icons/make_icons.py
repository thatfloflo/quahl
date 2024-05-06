import re
import sys
from pathlib import Path
from typing import Any


# Icon variants in this set may be derived and polished internally
# (e.g. as intermediate steps), but they will not be written back to disk.
# Good if e.g. o50 should be derived so that d50 can be derived from that,
# but the 'derived o50' itself should then be discarded.
DO_NOT_OVERWRITE: set[str] = {
}
# Icon variants in this set will not be polished, and used as a
# derivation basis as-is. Only applicable to "_g", "_c" and "_o" variants.
DO_NOT_POLISH: set[str] = {
    "app_c",
    "app_g",
    "app_o",
    "quahl_c",
    "quahl_g",
    "quahl_o",
}
# Icon variants in this set will not be derived from others, but instead they
# will be loaded from disk and used as-is (e.g. to derive other icons from
# them). Only applicable to "_o50", "_d", and "_d50" variants.
DO_NOT_DERIVE: set[str] = {
    "app_o50",
    "quahl_o50",
}

IconSourceDictT = dict[str, dict[str, Any]]

re_color_hex_str = re.compile(r"^#[0-9a-fA-F]{6}$")
re_stroke_width = re.compile(r"(?P<property>[;\"] *stroke-width:)(?P<value> *[0-9]+(?:\.[0-9]+)? *)")
re_stroke_color = re.compile(r"(?P<property>[;\"] *stroke:)(?P<value> *#[0-9a-fA-F]{6} *)")
re_stroke_opacity = re.compile(r"(?P<property>[;\"] *stroke-opacity:)(?P<value> *[0-9]+(?:\.[0-9]+)? *)")
re_fill_color = re.compile(r"(?P<property>[;\"] *fill:)(?P<value> *#[0-9a-fA-F]{6})")
re_fill_opacity = re.compile(r"(?P<property>[;\"] *fill-opacity:)(?P<value> *[0-9]+(?:\.[0-9]+)? *)")


def change_stroke_width(source: str, new_stroke_width: int | float) -> str:
    return re_stroke_width.sub(f"\\g<property>{new_stroke_width}", source)


def change_stroke_color(source: str, new_stroke_color: str) -> str:
    if not re_color_hex_str.match(new_stroke_color):
        raise ValueError(f"new_stroke_color={new_stroke_color!r} is not a valid hex color")
    return re_stroke_color.sub(f"\\g<property>{new_stroke_color}", source)


def change_stroke_opacity(source: str, new_stroke_opacity: int | float) -> str:
    return re_stroke_opacity.sub(f"\\g<property>{new_stroke_opacity}", source)


def change_fill_color(source: str, new_fill_color: str) -> str:
    if not re_color_hex_str.match(new_fill_color):
        raise ValueError(f"new_fill_color={new_fill_color!r} is not a valid hex color")
    return re_fill_color.sub(f"\\g<property>{new_fill_color}", source)


def change_fill_opacity(source: str, new_fill_opacity: int | float) -> str:
    return re_fill_opacity.sub(f"\\g<property>{new_fill_opacity}", source)


def polish_variant_g(source: str) -> str:
    """Polish the g variant"""
    source = change_stroke_color(source, "#7f7f7f")
    source = change_stroke_width(source, "1")
    source = change_stroke_opacity(source, "1")
    source = change_fill_color(source, "#c8c8c8")
    source = change_fill_opacity(source, "0.25")
    return source


def polish_variant_o(source: str) -> str:
    """Polish the o variant"""
    source = change_stroke_color(source, "#000000")
    source = change_stroke_width(source, "4")
    source = change_stroke_opacity(source, "1")
    source = change_fill_color(source, "#000000")
    source = change_fill_opacity(source, "0")
    return source


def derive_variant_o50_from_o(source: str) -> str:
    """Derive o50 variant from o variant."""
    source = change_stroke_width(source, "1")
    source = change_stroke_opacity(source, "0.5")
    return source


def derive_variant_d_from_o(source: str) -> str:
    """Derive d variant from o variant."""
    source = change_stroke_color(source, "#ffffff")
    source = change_fill_color(source, "#ffffff")
    return source


def derive_variant_d50_from_o50(source: str) -> str:
    """Derive d50 variant from o50 variant."""
    source = change_stroke_color(source, "#ffffff")
    source = change_fill_color(source, "#ffffff")
    return source


def _new_icon_source_dict(c: str | None = None, g: str | None = None, o: str | None = None) -> dict[str, None]:
    return {"c": c, "g": g, "o": o, "o50": None, "d": None, "d50": None}


def read_source_icons(base_dir: Path | None = None) -> IconSourceDictT:
    source_icons: IconSourceDictT = {}
    if base_dir is None:
        base_dir = Path("./")
    # Read full color icons
    color_dir = base_dir / "color"
    for path in color_dir.glob("*_c.svg"):
        if not path.is_file():
            continue
        icon_name = path.name.removesuffix("_c.svg")
        source_icons[icon_name] = _new_icon_source_dict(c=path.read_text())
    # Read grey color icons
    for path in color_dir.glob("*_g.svg"):
        if not path.is_file():
            continue
        icon_name = path.name.removesuffix("_g.svg")
        if icon_name in source_icons:
            source_icons[icon_name]["g"] = path.read_text()
        else:
            source_icons[icon_name] = _new_icon_source_dict(g=path.read_text())
    # Read outline icons
    outline_dir = base_dir / "outline"
    for path in outline_dir.glob("*_o.svg"):
        if not path.is_file():
            continue
        icon_name = path.name.removesuffix("_o.svg")
        if icon_name in source_icons:
            source_icons[icon_name]["o"] = path.read_text()
        else:
            source_icons[icon_name] = _new_icon_source_dict(o=path.read_text())
    return source_icons


def read_special_icon_variants(
        icon_dict: IconSourceDictT,
        special_variants: set[str],
        base_dir: Path | None = None) -> IconSourceDictT:
    """Load items in special_variants from disk and add to icon_dict."""
    if base_dir is None:
        base_dir = Path("./")
    for var_name in special_variants:
        var = var_name.split("_", 1)
        icon = var[0]
        if icon not in icon_dict:
            raise ValueError(f"Attempting to load special variant {var_name}, but {icon} not loaded")
        var = var[1] if len(var) > 0 else None
        if var in ("c", "g"):
            var_dir = base_dir / "color"
        elif var in ("o", "o50"):
            var_dir = base_dir / "outline"
        elif var in ("d", "d50"):
            var_dir = base_dir / "darko"
        else:
            raise ValueError("Special variant does not include _c/g/o/o50/d/d50 tag:", var_name)
        path = var_dir / f"{var_name}.svg"
        if not path.is_file():
            raise RuntimeError("Could not load special variant from ", path)
        icon_dict[icon][var] = path.read_text()
    return icon_dict


def check_missing_required(d: IconSourceDictT) -> list[str]:
    incompletes: list[str] = []
    for icon_name, icon_dict in d.items():
        if tuple(icon_dict) != ("c", "g", "o", "o50", "d", "d50"):
            raise ValueError("Malformed IconSourceDict not including all required keys")
        if not icon_dict["c"] or not icon_dict["g"] or not icon_dict["o"]:
            incompletes.append(icon_name)
    return incompletes


def main() -> int:
    CONFIRM_ALL = "--yes" in sys.argv
    # Read required source icons
    print("Loading required icons...")
    icon_dict = read_source_icons()
    missing = check_missing_required(icon_dict)
    if missing:
        print("    ERROR: One or more icons missing required style/variant: ", missing)
        return 1
    print(f"    {len(icon_dict)} icons loaded with _c, _g, and _o variant.")
    # Read special variants
    icon_dict = read_special_icon_variants(icon_dict, DO_NOT_DERIVE)
    print("The following have been loaded as special variants:")
    for varname in DO_NOT_POLISH:
        print(f"    {varname}")
    print("The following files will NOT be overwritten:")
    for fname in DO_NOT_OVERWRITE:
        print(f"    {fname}")
    # Confirm user wants to go ahead
    if not CONFIRM_ALL:
        if input("Do you want to continue? [yes/No] ").lower() not in ("y", "yes"):
            print("    Aborted. Nothing has been touched.")
            return 2
    # Compute all the icons
    print("Polishing and deriving icons...")
    for icon in icon_dict:
        print(f"    {icon}: ", end="", flush=True)
        if f"{icon}_g" not in DO_NOT_POLISH:
            icon_dict[icon]["g"] = polish_variant_g(icon_dict[icon]["g"])
        if f"{icon}_o" not in DO_NOT_POLISH:
            icon_dict[icon]["o"] = polish_variant_o(icon_dict[icon]["o"])
        if f"{icon}_o50" not in DO_NOT_DERIVE:
            icon_dict[icon]["o50"] = derive_variant_o50_from_o(icon_dict[icon]["o"])
        if f"{icon}_d" not in DO_NOT_DERIVE:
            icon_dict[icon]["d"] = derive_variant_d_from_o(icon_dict[icon]["o"])
        if f"{icon}_d50" not in DO_NOT_DERIVE:
            icon_dict[icon]["d50"] = derive_variant_d50_from_o50(icon_dict[icon]["o50"])
        print("✓")
    # Write all the icons
    print("Writing icons back to disk...")
    print("    ", end="", flush=True)
    for icon in icon_dict:
        for var in ("c", "g", "o", "o50", "d", "d50"):
            if f"{icon}_{var}" in DO_NOT_OVERWRITE:
                continue
            fname = f"{icon}_{var}.svg"
            if var in ("c", "g"):
                path = Path("./color") / fname
            elif var in ("o", "o50"):
                path = Path("./outline") / fname
            elif var in ("d", "d50"):
                path = Path("./darko") / fname
            path.write_text(icon_dict[icon][var])
        print(".", end="", flush=True)
    print("")
    print("All done 😄")
    return 0


if __name__ == "__main__":
    main()
