import hashlib
from pathlib import Path
from .utils import parse_filename, ATTR_FIELDS

IMAGES_DIR = Path("images")

ALLOWED_VALUES = {
    "type": ["euro", "vichy", "vichylight", "bugel", "amber", "tulip", "steine", "kraft"],
    "color": ["transparent", "brown", "green"],
    "fill": ["filled", "unfilled", "overfilled", "empty"],
    "liquid": ["transparent", "light", "dark", "black", "empty"],
    "label": ["labeled", "unlabeled"],
    "cap": ["crowned", "open"],
}


def validate_attributes(attributes):
    errors = []

    # Validate allowed categorical values
    for field in ATTR_FIELDS:
        value = attributes[field]
        if field in ALLOWED_VALUES and value not in ALLOWED_VALUES[field]:
            allowed = ALLOWED_VALUES[field]
            errors.append(f"{field}: '{value}' not in allowed set {allowed}")

    # Semantic rule: if fill == empty, liquid must be empty
    if attributes.get("fill") == "empty" and attributes.get("liquid") != "empty":
        errors.append(
            f"Invalid liquid='{attributes.get('liquid')}' for fill='empty'. "
            "Liquid must be 'empty' when fill='empty'."
        )

    return errors


def validate_group_indices(indices):
    errors = []
    numeric = []

    for index in indices:
        try:
            numeric.append(int(index))
        except ValueError:
            errors.append(f"Non-numeric index: {index}")

    if not numeric:
        return errors

    numeric_sorted = sorted(numeric)

    # Indices must start at 1
    if numeric_sorted[0] != 1:
        errors.append(f"Indices must start at 1, found start at {numeric_sorted[0]}")

    # Check duplicates
    if len(numeric_sorted) != len(set(numeric_sorted)):
        errors.append("Duplicate indices inside this group")

    # Continuity check
    expected = list(range(1, numeric_sorted[-1] + 1))
    missing = sorted(set(expected) - set(numeric_sorted))
    if missing:
        errors.append(f"Non-continuous sequence, missing: {missing}")

    return errors


def file_sha256(path: Path, block_size=65536):
    """Compute SHA256 hash of a file for content-duplicate detection."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(block_size):
            h.update(chunk)
    return h.hexdigest()


def main(return_success=False):
    parsing_errors = []
    attribute_errors = []

    groups = {}

    # Parse files and group metadata
    for file in sorted(IMAGES_DIR.iterdir()):
        if file.is_dir() or file.name.startswith("."):
            continue

        info = parse_filename(file)
        if info is None:
            parsing_errors.append(file.name)
            continue

        errors = validate_attributes(info)
        if errors:
            attribute_errors.append((file.name, errors))

        group_key = tuple(info[field] for field in ATTR_FIELDS)
        groups.setdefault(group_key, []).append((file.name, info["index"]))

    # Validate indices inside groups
    group_index_errors = {}
    duplicate_indices = {}

    for key, files in groups.items():
        indices = [index for _, index in files]
        index_errors = validate_group_indices(indices)

        if index_errors:
            group_index_errors[key] = index_errors

        index_map = {}
        for filename, index in files:
            index_map.setdefault(index, []).append(filename)

        duplicates = {idx: names for idx, names in index_map.items() if len(names) > 1}
        if duplicates:
            duplicate_indices[key] = duplicates

    # Duplicate images by content
    hash_map = {}
    duplicates_by_hash = {}

    for file in sorted(IMAGES_DIR.iterdir()):
        if file.is_dir() or file.name.startswith("."):
            continue

        digest = file_sha256(file)
        hash_map.setdefault(digest, []).append(file.name)

    for digest, files in hash_map.items():
        if len(files) > 1:
            duplicates_by_hash[digest] = files

    # If called programmatically by build.py, return boolean only
    if return_success:
        return (
            not parsing_errors
            and not attribute_errors
            and not group_index_errors
            and not duplicate_indices
            and not duplicates_by_hash
        )

    # Terminal report
    print("\nDataset validation report\n")

    print("Files with invalid naming:")
    if parsing_errors:
        for name in parsing_errors:
            print(f"  {name}")
    else:
        print("  None")
    print()

    print("Files with invalid attribute values:")
    if attribute_errors:
        for name, errs in attribute_errors:
            print(f"  {name}:")
            for err in errs:
                print(f"    - {err}")
    else:
        print("  None")
    print()

    print("Index validation inside groups:")
    if group_index_errors:
        for key, errs in group_index_errors.items():
            label = "_".join(key)
            print(f"  Group: {label}")
            for err in errs:
                print(f"    - {err}")
    else:
        print("  All groups valid")
    print()

    print("Duplicate indices inside groups:")
    if duplicate_indices:
        for key, dups in duplicate_indices.items():
            label = "_".join(key)
            print(f"  Group: {label}")
            for index, files in dups.items():
                print(f"    index {index}:")
                for f in files:
                    print(f"      - {f}")
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
