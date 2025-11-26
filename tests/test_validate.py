import scripts.validate as validate
from scripts.utils import parse_filename


def test_semantic_rule_liquid_empty():
    attrs = {
        "type": "euro",
        "color": "brown",
        "fill": "empty",
        "liquid": "transparent",
        "label": "labeled",
        "cap": "open",
        "index": "001",
    }
    errs = validate.validate_attributes(attrs)
    assert any("liquid" in e for e in errs)


def test_validate_missing_indices():
    errors = validate.validate_group_indices(["1", "2", "4"])
    assert any("missing" in e for e in errors)


def test_validate_starting_indices():
    errors = validate.validate_group_indices(["3", "4", "5"])
    assert any("missing" in e for e in errors)


def test_sha256_duplicates(temp_images, monkeypatch):
    monkeypatch.setattr("scripts.validate.IMAGES_DIR", temp_images)
    result = validate.main(return_success=True)
    # FAKEIMAGE1 appears twice → should detect duplicates → return False
    assert result is False
