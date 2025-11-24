from pathlib import Path

# Fields used in the naming convention (except the index)
ATTR_FIELDS = ["type", "color", "fill", "liquid", "label", "cap"]


def parse_filename(path: Path):
    """Parse filename formatted as:
       type_color_fill_liquid_label_cap_index.jpg

       Returns dict or None if structure mismatches.
    """
    stem = path.stem
    parts = stem.split("_")

    if len(parts) != 7:
        return None

    data = {
        "type": parts[0],
        "color": parts[1],
        "fill": parts[2],
        "liquid": parts[3],
        "label": parts[4],
        "cap": parts[5],
        "index": parts[6],
    }

    return data


def build_filename(entry: dict, index: int) -> str:
    """Construct a filename with the standard dataset convention."""
    name = (
        f"{entry['type']}_"
        f"{entry['color']}_"
        f"{entry['fill']}_"
        f"{entry['liquid']}_"
        f"{entry['label']}_"
        f"{entry['cap']}_"
        f"{index:03d}.jpg"
    )
    return name.lower()


def count_existing_images(images_dir: Path) -> int:
    """Count how many valid indexed images exist in images_dir."""
    count = 0
    for file in images_dir.glob("*.jpg"):
        info = parse_filename(file)
        if info is None:
            continue
        try:
            int(info["index"])
            count += 1
        except ValueError:
            pass
    return count
