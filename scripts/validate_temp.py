import csv
import hashlib
from pathlib import Path

from .utils import ATTR_FIELDS
from .validate import ALLOWED_VALUES

TEMP_DIR = Path("images_temp")
METADATA_FILE = TEMP_DIR / "metadata.csv"


def load_metadata(path: Path):
    entries = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row_num, row in enumerate(reader, start=2):
            entry = {
                "row": row_num,
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


def validate_attributes(attributes):
    errors = []

    for field in ATTR_FIELDS:
        value = attributes.get(field, "")
        if not value:
            errors.append(f"Missing value for '{field}'")
            continue

        if field in ALLOWED_VALUES and value not in ALLOWED_VALUES[field]:
            allowed = ALLOWED_VALUES[field]
            errors.append(f"{field}: '{value}' not in allowed set {allowed}")

    if attributes.get("fill") == "empty" and attributes.get("liquid") != "empty":
        errors.append(
            f"Invalid liquid='{attributes.get('liquid')}' for fill='empty'. "
            "Liquid must be 'empty' when fill='empty'."
        )

    return errors


def file_sha256(path: Path, block_size=65536):
    """Compute SHA256 hash of a file for content-duplicate detection."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(block_size):
            h.update(chunk)
    return h.hexdigest()


def main(return_success=False):
    if not METADATA_FILE.exists():
        if return_success:
            return False
        print(f"Metadata file not found: {METADATA_FILE}")
        return

    entries = load_metadata(METADATA_FILE)

    attribute_errors = []
    missing_files = []
    metadata_filenames = set()
    duplicate_filenames = {}

    for entry in entries:
        filename = entry["filename"]

        if filename in metadata_filenames:
            duplicate_filenames.setdefault(filename, []).append(entry["row"])
        else:
            metadata_filenames.add(filename)

        errors = validate_attributes(entry)
        if errors:
            attribute_errors.append((entry["row"], filename, errors))

        file_path = TEMP_DIR / filename
        if not file_path.exists():
            missing_files.append(filename)

    orphaned_files = []
    for file in sorted(TEMP_DIR.iterdir()):
        if file.is_dir() or file.name.startswith(".") or file.name == "metadata.csv":
            continue

        if file.name not in metadata_filenames:
            orphaned_files.append(file.name)

    hash_map = {}
    duplicates_by_hash = {}

    for file in sorted(TEMP_DIR.iterdir()):
        if file.is_dir() or file.name.startswith(".") or file.name == "metadata.csv":
            continue

        digest = file_sha256(file)
        hash_map.setdefault(digest, []).append(file.name)

    for digest, files in hash_map.items():
        if len(files) > 1:
            duplicates_by_hash[digest] = files

    if return_success:
        return (
                not attribute_errors
                and not missing_files
                and not orphaned_files
                and not duplicate_filenames
                and not duplicates_by_hash
        )

    print("\nTemporary dataset validation report\n")

    print("Metadata entries with invalid attributes:")
    if attribute_errors:
        for row, filename, errs in attribute_errors:
            print(f"  Row {row} ({filename}):")
            for err in errs:
                print(f"    - {err}")
    else:
        print("  None")
    print()

    print("Duplicate filenames in metadata:")
    if duplicate_filenames:
        for filename, rows in duplicate_filenames.items():
            print(f"  {filename}: appears at rows {rows}")
    else:
        print("  None")
    print()

    print("Missing files (referenced in metadata but not found):")
    if missing_files:
        for name in missing_files:
            print(f"  {name}")
    else:
        print("  None")
    print()

    print("Orphaned files (exist but not in metadata):")
    if orphaned_files:
        for name in orphaned_files:
            print(f"  {name}")
    else:
        print("  None")
    print()

    print("Duplicate images (identical file content):")
    if duplicates_by_hash:
        for digest, files in duplicates_by_hash.items():
            print(f"  Hash: {digest[:16]}...")
            for name in files:
                print(f"    - {name}")
    else:
        print("  None")
    print()


if __name__ == "__main__":
    main()
