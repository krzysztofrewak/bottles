import json
from pathlib import Path
from .utils import parse_filename

IMAGES_DIR = Path("images")
OUTPUT_DIR = Path("annotations")
OUTPUT_FILE = OUTPUT_DIR / "annotations.json"


def generate_annotations():
    annotations = []
    groups = {}

    for file in IMAGES_DIR.iterdir():
        if file.is_dir() or file.name.startswith("."):
            continue

        info = parse_filename(file)
        if info is None:
            continue

        key = (
            info["type"],
            info["color"],
            info["fill"],
            info["liquid"],
            info["label"],
            info["cap"],
        )

        groups[key] = groups.get(key, 0) + 1

    for file in sorted(IMAGES_DIR.iterdir()):
        if file.is_dir() or file.name.startswith("."):
            continue

        info = parse_filename(file)
        if info is None:
            continue

        key = (
            info["type"],
            info["color"],
            info["fill"],
            info["liquid"],
            info["label"],
            info["cap"],
        )

        entry = {
            "filename": file.name,
            "extension": file.suffix[1:].lower(),
            "collection": {
              "index": int(info["index"]),
              "of": groups[key],
            },
            "parameters": {
              "type": info["type"],
              "color": info["color"],
              "fill": info["fill"],
              "liquid": info["liquid"],
              "label": info["label"],
              "cap": info["cap"]
            }
        }

        annotations.append(entry)

    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"images": annotations}, f, indent=2)

    print(f"Annotations written to: {OUTPUT_FILE}")
    print(f"Total annotated images: {len(annotations)}")


def main():
    generate_annotations()


if __name__ == "__main__":
    main()
