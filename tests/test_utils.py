from scripts.utils import parse_filename, build_filename
from pathlib import Path


def test_parse_filename_valid():
    info = parse_filename(Path("vichy_brown_filled_dark_labeled_open_012.jpg"))
    assert info["type"] == "vichy"
    assert info["color"] == "brown"
    assert info["fill"] == "filled"
    assert info["liquid"] == "dark"
    assert info["label"] == "labeled"
    assert info["cap"] == "open"
    assert info["index"] == "012"


def test_parse_filename_invalid():
    assert parse_filename(Path("badfilename.jpg")) is None


def test_build_filename_roundtrip():
    entry = {
        "type": "euro",
        "color": "brown",
        "fill": "empty",
        "liquid": "empty",
        "label": "labeled",
        "cap": "open",
    }
    result = build_filename(entry, 7)
    assert result == "euro_brown_empty_empty_labeled_open_007.jpg"
