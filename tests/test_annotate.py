import json
from scripts import annotate


def test_annotation_generation(temp_images, monkeypatch, tmp_path):
    out_dir = tmp_path / "annotations"
    monkeypatch.setattr("scripts.annotate.IMAGES_DIR", temp_images)
    monkeypatch.setattr("scripts.annotate.OUTPUT_DIR", out_dir)
    monkeypatch.setattr("scripts.annotate.OUTPUT_FILE", out_dir / "annotations.json")

    annotate.generate_annotations()

    assert (out_dir / "annotations.json").exists()

    data = json.loads((out_dir / "annotations.json").read_text())
    assert "images" in data
    assert len(data["images"]) == 8  # invalid_name.jpg excluded
