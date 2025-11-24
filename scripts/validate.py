from pathlib import Path
from .utils import parse_filename, ATTR_FIELDS

IMAGES_DIR = Path("images")

ALLOWED_VALUES = {
    "type": ["euro", "vichy", "vichylight", "bugel", "amber", "tulip", "steine", "kraft"],
    "color": ["transparent", "brown", "green"],
    "fill": ["filled", "unfilled", "overfilled", "empty"],
    "liquid": ["transparent", "light", "dark", "black"],
    "label": ["labeled", "unlabeled"],
    "cap": ["crowned", "open"],
}


def validate_attributes(attributes):
    errors = []
    for field in ATTR_FIELDS:
        value = attributes[field]
        if field in ALLOWED_VALUES and value not in ALLOWED_VALUES[field]:
            errors.append(f"{field}: '{value}' not in allowed set {ALLOWED_VALUES[field]}")
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

    if numeric_sorted[0] != 1:
        errors.append(f"Indices must start at 1, found start at {numeric_sorted[0]}")

    if len(numeric_sorted) != len(set(numeric_sorted)):
        errors.append("Duplicate indices inside this group")

    expected = list(range(1, numeric_sorted[-1] + 1))
    missing = sorted(set(expected) - set(numeric_sorted))
    if missing:
        errors.append(f"Non-continuous sequence, missing: {missing}")

    return errors


def main():
    parsing_errors = []
    attribute_errors = []

    groups = {}

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

        duplicates = {
            index: file_list
            for index, file_list in index_map.items()
            if len(file_list) > 1
        }
        if duplicates:
            duplicate_indices[key] = duplicates

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
            group_label = "_".join(key)
            print(f"  Group: {group_label}")
            for err in errs:
                print(f"    - {err}")
    else:
        print("  All groups valid")
    print()

    print("Duplicate indices inside groups:")
    if duplicate_indices:
        for key, duplicates in duplicate_indices.items():
            group_label = "_".join(key)
            print(f"  Group: {group_label}")
            for index, file_list in duplicates.items():
                print(f"    index {index}:")
                for filename in file_list:
                    print(f"      - {filename}")
    else:
        print("  None")
    print()


if __name__ == "__main__":
    main()
