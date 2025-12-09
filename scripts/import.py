import csv
import shutil
import argparse
from pathlib import Path

from .utils import build_filename, get_next_index_for_group

IMAGES_DIR = Path("images")
TEMP_DIR = Path("images_temp")

METADATA_FILE = TEMP_DIR / "metadata.csv"


def load_metadata(path: Path):
    entries = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            entry = {
                "filename": row["Filename"],
                "type": row["Bottle type"],
                "color": row["Glass color"],
                "fill": row["Fill level"],
                "liquid": row["Liquid color"],
                "label": row["Label presence"],
                "cap": row["Cap presence"],
            }
            entries.append(entry)
    return entries


def process_entries(entries, dry_run=False):
    summary = []

    for entry in entries:
        original_name = entry["filename"]
        src = TEMP_DIR / original_name

        if not src.exists():
            summary.append((original_name, None, "File not found"))
            continue

        next_index = get_next_index_for_group(entry, IMAGES_DIR)

        new_name = build_filename(entry, next_index)
        dst = IMAGES_DIR / new_name

        summary.append((original_name, new_name, "OK"))

        if not dry_run:
            shutil.move(str(src), str(dst))

    return summary


def print_summary(summary, dry_run=False):
    if dry_run:
        print("Dry-run mode: no files were modified.\n")

    print("Import summary:\n")
    for original, new, status in summary:
        if status == "OK":
            print(f"{original} -> {new}")
        else:
            print(f"{original} -> ERROR: {status}")


def main():
    parser = argparse.ArgumentParser(description="Import new bottle images from images_temp/")
    parser.add_argument(
        "--dry", "-d", action="store_true",
        help="Perform a dry run without modifying any files"
    )
    args = parser.parse_args()

    dry_run = args.dry

    if not METADATA_FILE.exists():
        print(f"Metadata file not found: {METADATA_FILE}")
        return

    entries = load_metadata(METADATA_FILE)
    summary = process_entries(entries, dry_run=dry_run)
    print_summary(summary, dry_run=dry_run)


if __name__ == "__main__":
    main()
