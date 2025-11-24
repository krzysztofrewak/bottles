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


def get_next_index_for_group(entry, images_dir: Path):
    """Return next index for a group defined by entry (per-group numbering)."""

    group_fields = (
        entry["type"],
        entry["color"],
        entry["fill"],
        entry["liquid"],
        entry["label"],
        entry["cap"],
    )

    max_index = 0

    for file in images_dir.iterdir():
        if file.is_dir() or file.name.startswith("."):
            continue

        info = parse_filename(file)
        if info is None:
            continue

        file_group = (
            info["type"],
            info["color"],
            info["fill"],
            info["liquid"],
            info["label"],
            info["cap"],
        )

        if file_group != group_fields:
            continue

        try:
            idx = int(info["index"])
            if idx > max_index:
                max_index = idx
        except ValueError:
            continue

    return max_index + 1
