import argparse
from pathlib import Path
import collections
from datetime import date

from .utils import parse_filename, ATTR_FIELDS

IMAGES_DIR = Path("images")


def load_filters():
    parser = argparse.ArgumentParser(description="Compute dataset statistics with optional filters.")
    parser.add_argument("--type")
    parser.add_argument("--color")
    parser.add_argument("--fill")
    parser.add_argument("--liquid")
    parser.add_argument("--label")
    parser.add_argument("--cap")
    return vars(parser.parse_args())


def matches_filters(info, filters):
    for field, expected in filters.items():
        if expected is None:
            continue
        if info[field] != expected:
            return False
    return True


def collect_statistics(filters):
    attribute_counts = {field: collections.Counter() for field in ATTR_FIELDS}
    combination_counts = collections.Counter()
    extension_counts = collections.Counter()
    parsing_errors = []

    for file in sorted(IMAGES_DIR.iterdir()):
        if file.is_dir() or file.name.startswith("."):
            continue

        ext = file.suffix.lower()[1:]

        info = parse_filename(file)
        if info is None:
            parsing_errors.append(file.name)
            continue

        if not matches_filters(info, filters):
            continue

        extension_counts[ext] += 1

        for field in ATTR_FIELDS:
            attribute_counts[field][info[field]] += 1

        combination_key = tuple(info[field] for field in ATTR_FIELDS)
        combination_counts[combination_key] += 1

    total_images = sum(attribute_counts[ATTR_FIELDS[0]].values())

    return total_images, attribute_counts, combination_counts, extension_counts, parsing_errors


def print_statistics(filters):
    total, attribute_counts, combination_counts, extension_counts, parsing_errors = collect_statistics(filters)

    print(f"Date: {date.today()}")
    print(f"Total images: {total}")
    print()

    if any(value is not None for value in filters.values()):
        print("Filters:")
        for field, value in filters.items():
            if value is not None:
                print(f"  - {field}: {value}")
        print()

    print("Attribute distributions:")
    for field, counter in attribute_counts.items():
        print(f"- {field}:")
        for value, count in counter.most_common():
            print(f"  - {value}: {count}")
    print()

    print("File extensions:")
    for ext, count in extension_counts.most_common():
        print(f"  - {ext}: {count}")
    print()

    print(f"Unique combinations: {len(combination_counts)}")
    for combo, count in sorted(combination_counts.items(), key=lambda x: -x[1]):
        label = "_".join(combo)
        print(f"  - {label}: {count}")
    print()

    if parsing_errors:
        print("Files with invalid naming:")
        for name in parsing_errors:
            print(f"  {name}")


def main():
    filters = load_filters()
    print_statistics(filters)


if __name__ == "__main__":
    main()
