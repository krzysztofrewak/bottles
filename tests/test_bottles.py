import json

import numpy as np
import pytest
from PIL import Image

from scripts import bottles


@pytest.fixture
def bottle_images(tmp_path):
    """Two parameter groups whose runs are obvious: a clear visual break sits
    between index 8 and 9, and nowhere else."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    rng = np.random.default_rng(0)

    def write(name, base):
        noise = rng.normal(0, 4, (96, 96, 3))
        pixels = np.clip(np.array(base, dtype=float) + noise, 0, 255).astype(np.uint8)
        Image.fromarray(pixels).save(images_dir / name, quality=95)

    for index in range(1, 17):
        base = (30, 30, 30) if index <= 8 else (220, 210, 60)
        write(f"euro_brown_filled_light_labeled_opened_{index:03d}.jpg", base)

    for index in range(1, 5):
        write(f"vichy_green_empty_empty_unlabeled_crowned_{index:03d}.jpg", (120, 120, 120))

    (images_dir / "invalid_name.jpg").write_bytes(b"not an image")

    return images_dir


@pytest.fixture
def cached(bottle_images, tmp_path):
    cache = tmp_path / "signatures.npz"
    bottles.build_signatures(images_dir=bottle_images, cache_file=cache)
    return cache


def test_iter_images_skips_invalid_names(bottle_images):
    names = [path.name for path, _ in bottles.iter_images(bottle_images)]
    assert "invalid_name.jpg" not in names
    assert len(names) == 20


def test_iter_images_is_ordered_by_group_then_index(bottle_images):
    entries = bottles.iter_images(bottle_images)
    euro = [int(info["index"]) for _, info in entries
            if bottles.group_key(info).startswith("euro")]
    assert euro == sorted(euro)


def test_signatures_round_trip(cached):
    signatures = bottles.load_signatures(cached)
    assert len(signatures) == 20
    sample = signatures["euro_brown_filled_light_labeled_opened_001.jpg"]
    assert sample["gray"].shape == (bottles.THUMB * bottles.THUMB,)
    assert sample["background"].shape == (3,)


def test_load_signatures_without_cache(tmp_path):
    with pytest.raises(SystemExit):
        bottles.load_signatures(tmp_path / "missing.npz")


def test_detects_the_single_real_boundary(bottle_images, cached, tmp_path):
    assignments, diagnostics = bottles.build_index(
        images_dir=bottle_images, cache_file=cached, overrides_file=tmp_path / "none.json"
    )

    group = "euro_brown_filled_light_labeled_opened"
    first = {assignments[f"{group}_{i:03d}.jpg"] for i in range(1, 9)}
    second = {assignments[f"{group}_{i:03d}.jpg"] for i in range(9, 17)}

    assert len(first) == 1 and len(second) == 1
    assert first != second
    assert diagnostics[group]["bottles"] == 2


def test_short_group_stays_one_bottle(bottle_images, cached, tmp_path):
    assignments, _ = bottles.build_index(
        images_dir=bottle_images, cache_file=cached, overrides_file=tmp_path / "none.json"
    )
    group = "vichy_green_empty_empty_unlabeled_crowned"
    assert len({assignments[f"{group}_{i:03d}.jpg"] for i in range(1, 5)}) == 1


def test_verified_override_replaces_detection(bottle_images, cached, tmp_path):
    group = "euro_brown_filled_light_labeled_opened"
    overrides = tmp_path / "overrides.json"
    overrides.write_text(json.dumps({group: {"verified": True, "cut_after": [4, 12]}}))

    assignments, diagnostics = bottles.build_index(
        images_dir=bottle_images, cache_file=cached, overrides_file=overrides
    )

    assert diagnostics[group]["verified"] is True
    assert diagnostics[group]["bottles"] == 3
    assert assignments[f"{group}_004.jpg"] != assignments[f"{group}_005.jpg"]
    assert assignments[f"{group}_012.jpg"] != assignments[f"{group}_013.jpg"]


def test_keep_together_removes_a_detected_cut(bottle_images, cached, tmp_path):
    group = "euro_brown_filled_light_labeled_opened"
    overrides = tmp_path / "overrides.json"
    overrides.write_text(json.dumps({group: {"keep_together": [8]}}))

    assignments, _ = bottles.build_index(
        images_dir=bottle_images, cache_file=cached, overrides_file=overrides
    )
    assert assignments[f"{group}_008.jpg"] == assignments[f"{group}_009.jpg"]


def test_identity_list_names_every_bottle(bottle_images, cached, tmp_path):
    group = "euro_brown_filled_light_labeled_opened"
    overrides = tmp_path / "overrides.json"
    overrides.write_text(json.dumps(
        {group: {"verified": True, "cut_after": [8], "identity": ["porter", "piast"]}}
    ))

    _, diagnostics = bottles.build_index(
        images_dir=bottle_images, cache_file=cached, overrides_file=overrides
    )
    assert diagnostics[group]["identity"] == {"01": "porter", "02": "piast"}


def test_identity_dict_names_one_bottle_and_null_names_none():
    assert bottles.resolve_identities({"identity": {"2": "piast"}}, 3) == ({2: "piast"}, None)
    assert bottles.resolve_identities({"identity": ["porter", None]}, 2) == ({1: "porter"}, None)
    assert bottles.resolve_identities({}, 2) == ({}, None)


def test_identity_list_of_the_wrong_length_is_refused():
    named, complaint = bottles.resolve_identities({"identity": ["porter"]}, 3)
    assert named == {}
    assert "3 bottles" in complaint


def test_identity_out_of_range_is_refused():
    named, complaint = bottles.resolve_identities({"identity": {"4": "porter"}}, 2)
    assert named == {}
    assert complaint


def test_identity_joins_bottles_across_groups(bottle_images, cached, tmp_path):
    """The point of the layer: one name covering two parameter groups."""
    overrides = tmp_path / "overrides.json"
    overrides.write_text(json.dumps({
        "euro_brown_filled_light_labeled_opened": {
            "verified": True, "cut_after": [8], "identity": ["porter", "piast"],
        },
        "vichy_green_empty_empty_unlabeled_crowned": {
            "verified": True, "cut_after": [], "identity": ["porter"],
        },
    }))

    assignments, diagnostics = bottles.build_index(
        images_dir=bottle_images, cache_file=cached, overrides_file=overrides
    )
    output = tmp_path / "bottles.json"
    bottles.write_index(assignments, diagnostics, output_file=output)

    identities = json.loads(output.read_text())["identities"]
    assert sorted(identities) == ["piast", "porter"]
    assert identities["porter"]["bottles"] == [
        "euro_brown_filled_light_labeled_opened#01",
        "vichy_green_empty_empty_unlabeled_crowned#01",
    ]
    assert identities["porter"]["count"] == 12
    assert identities["piast"]["count"] == 8


def test_unnamed_bottles_carry_a_null_identity(bottle_images, cached, tmp_path):
    assignments, diagnostics = bottles.build_index(
        images_dir=bottle_images, cache_file=cached, overrides_file=tmp_path / "none.json"
    )
    output = tmp_path / "bottles.json"
    bottles.write_index(assignments, diagnostics, output_file=output)

    payload = json.loads(output.read_text())
    assert payload["identities"] == {}
    assert all(entry["identity"] is None for entry in payload["bottles"])


def test_write_index_output_shape(bottle_images, cached, tmp_path):
    assignments, diagnostics = bottles.build_index(
        images_dir=bottle_images, cache_file=cached, overrides_file=tmp_path / "none.json"
    )
    output = tmp_path / "bottles.json"
    bottles.write_index(assignments, diagnostics, output_file=output)

    payload = json.loads(output.read_text())
    assert payload["settings"]["cut_threshold"] == bottles.CUT_THRESHOLD
    assert sum(entry["count"] for entry in payload["bottles"]) == len(assignments)
    for entry in payload["bottles"]:
        assert entry["bottle_id"].startswith(entry["group"] + "#")
        assert len(entry["images"]) == entry["count"]


def test_sheets_are_written_per_group(bottle_images, cached, tmp_path):
    assignments, _ = bottles.build_index(
        images_dir=bottle_images, cache_file=cached, overrides_file=tmp_path / "none.json"
    )
    sheets = tmp_path / "sheets"
    bottles.build_sheets(assignments, images_dir=bottle_images, sheets_dir=sheets)

    written = sorted(path.name for path in sheets.iterdir())
    assert written == [
        "euro_brown_filled_light_labeled_opened.jpg",
        "vichy_green_empty_empty_unlabeled_crowned.jpg",
    ]
