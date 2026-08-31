"""Index images by the physical bottle they show.

The published images carry no EXIF (sanitize.py writes exif=b""), so there is no
capture timestamp to group by. The ordering survives elsewhere: import.py walks
metadata.csv in camera order and hands out per-group indices through
get_next_index_for_group(), so within one parameter group the numeric suffix
preserves the order the photos were taken in. Shots of one bottle are therefore a
contiguous block of indices, and identifying bottles reduces to finding the points
where that sequence jumps to a different bottle.

Four visual cues vote on every gap between neighbouring indices. Each is turned
into a robust z-score inside its own group before they are summed, so a cue that
happens to be flat for one group cannot drown out the one that actually separates
its bottles.

The detector is good but not exact, so the result is meant to be reviewed:

    python -m scripts.bottles signatures     # one slow pass over images/ (cached)
    python -m scripts.bottles index          # write annotations/bottles.json
    python -m scripts.bottles sheets         # contact sheets with the cuts drawn
    python -m scripts.bottles report         # runs, plus the gaps worth checking

Corrections go into annotations/bottle_overrides.json and survive re-runs; see
load_overrides() for the format.

A bottle_id is scoped to its parameter group, and label and cap are part of that
group, so one physical bottle photographed labeled and then unlabeled lands in two
groups and gets two unrelated ids. Nothing visual joins them back: the signature
leans on the label, which is the very thing that changed. The join is therefore
recorded by hand — an "identity" name in the overrides — and collected into the
"identities" block of the output; see resolve_identities().
"""

import json
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .utils import parse_filename, ATTR_FIELDS

IMAGES_DIR = Path("images")
OUTPUT_DIR = Path("annotations")
OUTPUT_FILE = OUTPUT_DIR / "bottles.json"
OVERRIDES_FILE = OUTPUT_DIR / "bottle_overrides.json"
CACHE_FILE = Path(".cache/bottle_signatures.npz")
SHEETS_DIR = Path("bottle_sheets")

# Window of neighbours averaged on each side of a gap. Small enough to sit inside
# a short run, large enough that one odd camera angle cannot open a cut.
WINDOW = 4

# Tuned against three groups verified by eye (7 true boundaries): catches 6 of 7
# with 4 false cuts. Lowering CUT_THRESHOLD to 2.5 catches all 7 but roughly
# triples the false ones.
CUT_THRESHOLD = 3.0

# Re-joins neighbouring runs whose label colours agree, which undoes cuts that
# fired on a change of backdrop rather than a change of bottle.
MERGE_THRESHOLD = 0.6

THUMB = 64          # grayscale thumbnail edge, for framing/layout comparison
CENTRE_SIZE = (10, 22)  # bottle-column thumbnail, width x height


def group_key(info):
    return "_".join(info[field] for field in ATTR_FIELDS)


def iter_images(images_dir):
    """Yield (path, info) for validly named images, in group then index order."""
    entries = []
    for file in sorted(images_dir.iterdir()):
        if file.is_dir() or file.name.startswith("."):
            continue
        info = parse_filename(file)
        if info is None:
            continue
        try:
            index = int(info["index"])
        except ValueError:
            continue
        entries.append((group_key(info), index, file, info))

    entries.sort(key=lambda e: (e[0], e[1]))
    return [(file, info) for _, _, file, info in entries]


# --------------------------------------------------------------------------- #
# Signatures
# --------------------------------------------------------------------------- #

def extract_signature(path):
    """Cheap visual fingerprint of one image.

    JPEG is decoded at 1/8 scale through Pillow's DCT shortcut, which is what
    keeps a full pass over the dataset in the minutes rather than hours range.
    """
    image = Image.open(path)
    image.draft("RGB", (image.size[0] // 8, image.size[1] // 8))
    image = image.convert("RGB")

    pixels = np.asarray(image, dtype=np.float32) / 255.0
    height, width, _ = pixels.shape

    small = np.asarray(image.resize((THUMB, THUMB), Image.BILINEAR), dtype=np.float32) / 255.0
    gray = small @ np.array([0.299, 0.587, 0.114], dtype=np.float32)

    # The bottle stands in the middle, so the frame edges describe the surface
    # and the lighting instead — a session fingerprint rather than a bottle one.
    border = np.concatenate([
        small[:6].reshape(-1, 3), small[-6:].reshape(-1, 3),
        small[:, :6].reshape(-1, 3), small[:, -6:].reshape(-1, 3),
    ])

    centre = pixels[int(height * 0.12):int(height * 0.95),
                    int(width * 0.28):int(width * 0.72)]
    centre_thumb = np.asarray(
        Image.fromarray((centre * 255).astype(np.uint8)).resize(CENTRE_SIZE, Image.BILINEAR),
        dtype=np.float32,
    ) / 255.0

    channel_max = centre.max(2)
    saturation = np.where(channel_max > 1e-6,
                          (channel_max - centre.min(2)) / np.maximum(channel_max, 1e-6), 0.0)
    red, green, blue = centre[..., 0], centre[..., 1], centre[..., 2]
    warm = red - blue                      # yellow and red labels against neutral ones
    greenness = green - (red + blue) / 2

    tint = np.concatenate([
        [warm.mean(), warm.std(), greenness.mean(), greenness.std()],
        np.histogram(saturation, bins=12, range=(0, 1), density=True)[0],
    ])

    return {
        "gray": gray.flatten(),
        "background": border.mean(0),
        "centre": centre_thumb.flatten(),
        "tint": tint,
    }


def build_signatures(images_dir=IMAGES_DIR, cache_file=CACHE_FILE):
    entries = iter_images(images_dir)
    if not entries:
        print(f"No validly named images found in {images_dir}")
        return None

    names, gray, background, centre, tint = [], [], [], [], []
    for position, (path, _) in enumerate(entries, 1):
        try:
            signature = extract_signature(path)
        except Exception as error:
            print(f"Skipping {path.name}: {error}")
            continue

        names.append(path.name)
        gray.append(signature["gray"])
        background.append(signature["background"])
        centre.append(signature["centre"])
        tint.append(signature["tint"])

        if position % 250 == 0 or position == len(entries):
            print(f"  {position}/{len(entries)} images")

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache_file,
        names=np.array(names),
        gray=np.array(gray, dtype=np.float16),
        background=np.array(background, dtype=np.float32),
        centre=np.array(centre, dtype=np.float16),
        tint=np.array(tint, dtype=np.float32),
    )
    print(f"Signatures written to: {cache_file} ({len(names)} images)")
    return cache_file


def load_signatures(cache_file=CACHE_FILE):
    if not cache_file.exists():
        raise SystemExit(
            f"No signature cache at {cache_file}. Run: python -m scripts.bottles signatures"
        )
    data = np.load(cache_file, allow_pickle=False)
    # Each key lookup on an NpzFile decompresses that whole array, so pull the
    # four of them out once rather than once per image.
    names = data["names"]
    gray = data["gray"].astype(np.float32)
    background = data["background"].astype(np.float64)
    centre = data["centre"].astype(np.float64)
    tint = data["tint"].astype(np.float64)

    return {
        name: {
            "gray": gray[i],
            "background": background[i],
            "centre": centre[i],
            "tint": tint[i],
        }
        for i, name in enumerate(names)
    }


# --------------------------------------------------------------------------- #
# Change point detection
# --------------------------------------------------------------------------- #

def cue_matrices(signatures, names):
    """Four all-pairs similarity matrices, one per visual cue."""
    with np.errstate(all="ignore"):  # Accelerate's BLAS raises spurious FP flags
        gray = np.array([signatures[n]["gray"] for n in names])
        gray = gray - gray.mean(1, keepdims=True)
        gray = gray / np.maximum(gray.std(1, keepdims=True), 1e-6)
        framing = np.clip(gray @ gray.T / gray.shape[1], -1.0, 1.0)

        background = np.array([signatures[n]["background"] for n in names])
        surface = np.exp(-np.linalg.norm(background[:, None] - background[None, :], axis=-1) / 0.08)

        centre = np.array([signatures[n]["centre"] for n in names])
        label = np.exp(-np.linalg.norm(centre[:, None] - centre[None, :], axis=-1)
                       / (0.9 * np.sqrt(centre.shape[1])))

        tint = np.array([signatures[n]["tint"] for n in names])
        tint = (tint - tint.mean(0)) / (tint.std(0) + 1e-6)
        hue = np.exp(-np.linalg.norm(tint[:, None] - tint[None, :], axis=-1)
                     / (1.5 * np.sqrt(tint.shape[1])))

    return framing, surface, label, hue


def window_scores(matrix):
    """Per gap: how much more alike each side is internally than to the other."""
    count = len(matrix)
    scores = np.zeros(max(0, count - 1))
    for gap in range(count - 1):
        left = slice(max(0, gap - WINDOW + 1), gap + 1)
        right = slice(gap + 1, min(count, gap + 1 + WINDOW))
        within = (matrix[left, left].mean() + matrix[right, right].mean()) / 2
        scores[gap] = within - matrix[left, right].mean()
    return scores


def robust_z(values):
    median = np.median(values)
    deviation = np.median(np.abs(values - median))
    return (values - median) / (1.4826 * deviation + 1e-6)


def gap_scores(signatures, names):
    """Fused per-gap boundary score. Index i scores the gap after names[i]."""
    if len(names) < 2 * WINDOW:
        # Too short for the window to mean anything; treat it as one bottle.
        return np.zeros(max(0, len(names) - 1))
    per_cue = [robust_z(window_scores(matrix)) for matrix in cue_matrices(signatures, names)]
    return np.mean(per_cue, axis=0)


def label_profile(signatures, names):
    """Median label colour of a run — the part that ignores the backdrop."""
    centre = np.median([signatures[n]["centre"] for n in names], axis=0)
    tint = np.median([signatures[n]["tint"] for n in names], axis=0)
    return centre, tint


def merge_similar_runs(signatures, runs, protected=frozenset()):
    """Re-join neighbouring runs that show the same bottle on a new backdrop.

    Boundaries in `protected` came from a human and are left alone.
    """
    if len(runs) < 2:
        return runs

    index_of = lambda name: int(name.rsplit("_", 1)[1].split(".")[0])

    profiles = [label_profile(signatures, run) for run in runs]
    merged = [list(runs[0])]
    for position in range(1, len(runs)):
        if index_of(runs[position - 1][-1]) in protected:
            merged.append(list(runs[position]))
            continue

        centre_now, tint_now = profiles[position]
        centre_prev, tint_prev = profiles[position - 1]
        distance = (
            np.linalg.norm(centre_now - centre_prev) / np.sqrt(len(centre_now))
            + np.linalg.norm(tint_now - tint_prev) / np.sqrt(len(tint_now))
        )
        if distance >= MERGE_THRESHOLD:
            merged.append(list(runs[position]))
        else:
            merged[-1].extend(runs[position])
    return merged


# --------------------------------------------------------------------------- #
# Manual corrections
# --------------------------------------------------------------------------- #

def load_overrides(path=OVERRIDES_FILE):
    """Human corrections, keyed by group name.

        {
          "amber_brown_empty_empty_labeled_crowned": {
            "verified": true,
            "cut_after": [46, 82, 100]
          },
          "euro_brown_overfilled_transparent_labeled_opened": {
            "cut_after": [45],
            "keep_together": [1],
            "identity": ["mister_style", null]
          }
        }

    Numbers are the index of the last image before a cut, as printed by `report`
    and drawn by `sheets`. "verified": true means the cut_after list is the whole
    truth for that group and detection is skipped. Without it, cut_after adds cuts
    and keep_together removes them, leaving the rest to the detector.

    "identity" names the physical bottles of the group; see resolve_identities().
    """
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def apply_overrides(group, cuts, overrides):
    """Turn detected cuts into a final cut set for one group."""
    rule = overrides.get(group)
    if not rule:
        return cuts

    if rule.get("verified"):
        return {int(i) for i in rule.get("cut_after", [])}

    cuts = set(cuts)
    cuts |= {int(i) for i in rule.get("cut_after", [])}
    cuts -= {int(i) for i in rule.get("keep_together", [])}
    return cuts


def resolve_identities(rule, run_count):
    """Name the physical bottles of one group. Returns (mapping, complaint).

    A bottle_id only identifies a bottle inside its own parameter group, and the
    same bottle reappears under a different group once its label comes off or its
    cap does. "identity" carries that across, as a name shared by every group the
    bottle shows up in:

        "identity": ["porter", "piast", "kasztelan", "okocim"]
        "identity": {"2": "piast"}

    The list form is positional — one name per bottle of the group, in index
    order, and it has to be exactly as long as the group has bottles, so that a
    later cut cannot silently shift every name onto the wrong bottle. The dict
    form is keyed by bottle number for naming only some of them. null, or a
    number left out, leaves that bottle unnamed.

    A name stands for one physical bottle, not a brand: two bottles of the same
    beer shot separately need two names.

    The mapping is empty when the names cannot be trusted, with the reason
    returned alongside it for the caller to report.
    """
    raw = rule.get("identity")
    if not raw:
        return {}, None

    if isinstance(raw, list):
        if len(raw) != run_count:
            return {}, f"{len(raw)} names for {run_count} bottles"
        pairs = list(enumerate(raw, 1))
    else:
        try:
            pairs = [(int(number), name) for number, name in raw.items()]
        except ValueError:
            return {}, "dict keys must be bottle numbers"

    named = {}
    for number, name in pairs:
        if name is None:
            continue
        if not 1 <= number <= run_count:
            return {}, f"bottle {number} named, but the group has {run_count}"
        named[number] = str(name)
    return named, None


def split_runs(names, indices, cuts):
    runs, current = [], [names[0]]
    for position in range(1, len(names)):
        if indices[position - 1] in cuts:
            runs.append(current)
            current = []
        current.append(names[position])
    runs.append(current)
    return runs


# --------------------------------------------------------------------------- #
# Indexing
# --------------------------------------------------------------------------- #

def collect_groups(images_dir=IMAGES_DIR):
    groups = {}
    for path, info in iter_images(images_dir):
        groups.setdefault(group_key(info), []).append((int(info["index"]), path.name))
    for key in groups:
        groups[key].sort()
    return groups


def build_index(images_dir=IMAGES_DIR, cache_file=CACHE_FILE, overrides_file=OVERRIDES_FILE):
    signatures = load_signatures(cache_file)
    overrides = load_overrides(overrides_file)
    groups = collect_groups(images_dir)

    assignments, diagnostics = {}, {}

    for group, members in sorted(groups.items()):
        members = [(index, name) for index, name in members if name in signatures]
        if not members:
            continue

        indices = [index for index, _ in members]
        names = [name for _, name in members]

        scores = gap_scores(signatures, names)
        detected = {indices[i] for i, score in enumerate(scores) if score >= CUT_THRESHOLD}

        rule = overrides.get(group, {})
        runs = split_runs(names, indices, apply_overrides(group, detected, overrides))
        if not rule.get("verified"):
            forced = {int(i) for i in rule.get("cut_after", [])}
            runs = merge_similar_runs(signatures, runs, protected=forced)

        for number, run in enumerate(runs, 1):
            for name in run:
                assignments[name] = f"{group}#{number:02d}"

        identities, complaint = resolve_identities(rule, len(runs))
        if complaint:
            print(f"Warning: {group}: identity ignored, {complaint}")

        diagnostics[group] = {
            "scores": {str(indices[i]): round(float(score), 3) for i, score in enumerate(scores)},
            "verified": bool(rule.get("verified")),
            "bottles": len(runs),
            "identity": {f"{number:02d}": name for number, name in sorted(identities.items())},
        }

    return assignments, diagnostics


def write_index(assignments, diagnostics, output_file=OUTPUT_FILE):
    runs = {}
    for name, bottle in assignments.items():
        runs.setdefault(bottle, []).append(name)

    bottles = []
    for bottle, files in sorted(runs.items()):
        group, _, number = bottle.partition("#")
        bottles.append({
            "bottle_id": bottle,
            "group": group,
            "identity": diagnostics.get(group, {}).get("identity", {}).get(number),
            "count": len(files),
            "images": sorted(files),
        })

    # One physical bottle, gathered from every group it was photographed in.
    identities = {}
    for entry in bottles:
        if not entry["identity"]:
            continue
        record = identities.setdefault(entry["identity"], {"count": 0, "bottles": []})
        record["count"] += entry["count"]
        record["bottles"].append(entry["bottle_id"])

    payload = {
        "settings": {
            "window": WINDOW,
            "cut_threshold": CUT_THRESHOLD,
            "merge_threshold": MERGE_THRESHOLD,
        },
        "verified_groups": sorted(g for g, d in diagnostics.items() if d["verified"]),
        "identities": {name: identities[name] for name in sorted(identities)},
        "bottles": bottles,
    }

    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    print(f"Bottle index written to: {output_file}")
    print(f"Images: {len(assignments)}  bottles: {len(bottles)}  "
          f"verified groups: {len(payload['verified_groups'])}/{len(diagnostics)}")
    named = sum(1 for b in bottles if b["identity"])
    spanning = sum(1 for r in identities.values() if len(r["bottles"]) > 1)
    print(f"Named bottles: {named}/{len(bottles)}  identities: {len(identities)}  "
          f"of which spanning several groups: {spanning}")
    if bottles:
        sizes = np.array([b["count"] for b in bottles])
        print(f"Images per bottle: mean {sizes.mean():.1f}  median {np.median(sizes):.0f}  "
              f"max {sizes.max()}  singletons {(sizes == 1).sum()}")


# --------------------------------------------------------------------------- #
# Review aids
# --------------------------------------------------------------------------- #

def print_report(diagnostics, images_dir=IMAGES_DIR, limit=12):
    groups = collect_groups(images_dir)

    print("Groups needing review (least confident first):\n")

    ranked = []
    for group, members in groups.items():
        if diagnostics.get(group, {}).get("verified"):
            continue
        scores = diagnostics.get(group, {}).get("scores", {})
        if not scores:
            continue
        # Gaps sitting near the threshold are the ones a human should look at.
        borderline = [(abs(score - CUT_THRESHOLD), int(index), score)
                      for index, score in scores.items()
                      if CUT_THRESHOLD - 1.5 <= score <= CUT_THRESHOLD + 1.5]
        ranked.append((len(borderline), group, sorted(borderline)[:5], len(members)))

    for _, group, borderline, size in sorted(ranked, reverse=True)[:limit]:
        bottles = diagnostics[group]["bottles"]
        print(f"{group}  ({size} images -> {bottles} bottles)")
        print("  uncertain gaps: " +
              ", ".join(f"after {index} (z={score:.2f})" for _, index, score in borderline))

    print(f"\nMark a group as checked in {OVERRIDES_FILE}, then re-run `index`.")

    total = sum(diagnostic["bottles"] for diagnostic in diagnostics.values())
    named = sum(len(diagnostic["identity"]) for diagnostic in diagnostics.values())
    print(f"\nIdentities: {named}/{total} bottles named across {len(diagnostics)} groups.")

    # A group settled by eye is the cheapest place to add names: the runs are
    # already right, so the list cannot drift onto the wrong bottle later.
    unnamed = sorted(group for group, diagnostic in diagnostics.items()
                     if diagnostic["verified"] and not diagnostic["identity"])
    if unnamed:
        print("Verified groups still unnamed: " + ", ".join(unnamed[:limit]))
        print(f'Add "identity" to them in {OVERRIDES_FILE} to join bottles across groups.')


def draw_sheet(runs, images_dir, output_path, tile=150):
    """Contact sheet for one group; each bottle run starts on a new row block."""
    tiles, boundaries = [], set()
    position = 0
    for number, run in enumerate(runs, 1):
        for name in run:
            tiles.append((name, number))
            position += 1
        boundaries.add(position)

    columns = min(len(tiles), 8)
    rows = (len(tiles) + columns - 1) // columns
    label_height = 16
    sheet = Image.new("RGB", (columns * tile, rows * (tile + label_height)), "white")
    draw = ImageDraw.Draw(sheet)

    for position, (name, number) in enumerate(tiles):
        image = Image.open(images_dir / name)
        image.draft("RGB", (image.size[0] // 8, image.size[1] // 8))
        image = image.convert("RGB")
        image.thumbnail((tile, tile))

        x = (position % columns) * tile
        y = (position // columns) * (tile + label_height)
        sheet.paste(image, (x + (tile - image.size[0]) // 2, y))
        index = name.rsplit("_", 1)[1].split(".")[0]
        draw.text((x + 3, y + tile + 2), f"{index}  #{number:02d}", fill="black")

        if position in boundaries and position:
            draw.rectangle([x, y, x + 3, y + tile + label_height], fill="red")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=85)


def build_sheets(assignments, images_dir=IMAGES_DIR, sheets_dir=SHEETS_DIR, only=None):
    groups = {}
    for name, bottle in assignments.items():
        groups.setdefault(bottle.split("#")[0], {}).setdefault(bottle, []).append(name)

    index_of = lambda n: int(n.rsplit("_", 1)[1].split(".")[0])

    written = 0
    for group, runs in sorted(groups.items()):
        if only and only not in group:
            continue
        ordered = [sorted(runs[bottle], key=index_of) for bottle in sorted(runs)]
        draw_sheet(ordered, images_dir, sheets_dir / f"{group}.jpg")
        written += 1

    print(f"Wrote {written} contact sheets to: {sheets_dir}")
    print("Red bars mark detected bottle boundaries; each tile shows index and bottle number.")


# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description="Index bottle images by physical bottle")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("signatures", help="Extract and cache visual signatures (slow)")
    subparsers.add_parser("index", help="Detect bottles and write annotations/bottles.json")
    subparsers.add_parser("report", help="List the groups and gaps most worth reviewing")

    sheets = subparsers.add_parser("sheets", help="Render contact sheets with cuts drawn")
    sheets.add_argument("--group", "-g", help="Only groups whose name contains this string")

    args = parser.parse_args()

    if args.command == "signatures":
        build_signatures()
        return

    if args.command is None:
        parser.print_help()
        return

    assignments, diagnostics = build_index()

    if args.command == "index":
        write_index(assignments, diagnostics)
    elif args.command == "report":
        print_report(diagnostics)
    elif args.command == "sheets":
        build_sheets(assignments, only=args.group)


if __name__ == "__main__":
    main()
