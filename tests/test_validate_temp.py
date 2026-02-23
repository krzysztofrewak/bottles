import csv
from pathlib import Path
import scripts.validate_temp as validate_temp


def test_validate_attributes_empty_liquid():
    attrs = {
        "type": "euro",
        "color": "brown",
        "fill": "empty",
        "liquid": "transparent",
        "label": "labeled",
        "cap": "open",
    }
    errs = validate_temp.validate_attributes(attrs)
    assert any("liquid" in e for e in errs)


def test_validate_attributes_invalid_value():
    attrs = {
        "type": "invalid_type",
        "color": "brown",
        "fill": "filled",
        "liquid": "transparent",
        "label": "labeled",
        "cap": "open",
    }
    errs = validate_temp.validate_attributes(attrs)
    assert any("type" in e and "invalid_type" in e for e in errs)


def test_validate_attributes_missing_field():
    attrs = {
        "type": "euro",
        "color": "",
        "fill": "filled",
        "liquid": "transparent",
        "label": "labeled",
        "cap": "open",
    }
    errs = validate_temp.validate_attributes(attrs)
    assert any("Missing" in e and "color" in e for e in errs)


def test_main_no_metadata(tmp_path, monkeypatch):
    fake_dir = tmp_path / "fake_temp"
    monkeypatch.setattr("scripts.validate_temp.TEMP_DIR", fake_dir)
    monkeypatch.setattr("scripts.validate_temp.METADATA_FILE", fake_dir / "metadata.csv")

    result = validate_temp.main(return_success=True)
    assert result is False


def test_main_missing_files(tmp_path, monkeypatch):
    temp_dir = tmp_path / "images_temp"
    temp_dir.mkdir()
    metadata_file = temp_dir / "metadata.csv"
    
    # Create metadata without actual image files
    with open(metadata_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Filename", "Bottle type", "Glass color", "Fill level", 
                        "Liquid color", "Label presence", "Cap presence", "Note"])
        writer.writerow(["IMG_0001.JPG", "euro", "brown", "filled", "transparent", "labeled", "opened", ""])
    
    monkeypatch.setattr("scripts.validate_temp.TEMP_DIR", temp_dir)
    monkeypatch.setattr("scripts.validate_temp.METADATA_FILE", metadata_file)
    
    result = validate_temp.main(return_success=True)
    assert result is False


def test_main_orphaned_files(tmp_path, monkeypatch):
    temp_dir = tmp_path / "images_temp"
    temp_dir.mkdir()
    metadata_file = temp_dir / "metadata.csv"
    
    # Create metadata file (empty)
    with open(metadata_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Filename", "Bottle type", "Glass color", "Fill level",
                        "Liquid color", "Label presence", "Cap presence", "Note"])
    
    # Create orphaned image file
    orphan = temp_dir / "IMG_9999.JPG"
    orphan.write_text("fake image")
    
    monkeypatch.setattr("scripts.validate_temp.TEMP_DIR", temp_dir)
    monkeypatch.setattr("scripts.validate_temp.METADATA_FILE", metadata_file)
    
    result = validate_temp.main(return_success=True)
    assert result is False


def test_main_duplicate_content(tmp_path, monkeypatch):
    temp_dir = tmp_path / "images_temp"
    temp_dir.mkdir()
    metadata_file = temp_dir / "metadata.csv"
    
    # Create two files with identical content
    img1 = temp_dir / "IMG_0001.JPG"
    img2 = temp_dir / "IMG_0002.JPG"
    img1.write_bytes(b"FAKEIMAGE")
    img2.write_bytes(b"FAKEIMAGE")
    
    with open(metadata_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Filename", "Bottle type", "Glass color", "Fill level",
                        "Liquid color", "Label presence", "Cap presence", "Note"])
        writer.writerow(["IMG_0001.JPG", "euro", "brown", "filled", "transparent", "labeled", "opened", ""])
        writer.writerow(["IMG_0002.JPG", "euro", "brown", "filled", "transparent", "labeled", "open", ""])
    
    monkeypatch.setattr("scripts.validate_temp.TEMP_DIR", temp_dir)
    monkeypatch.setattr("scripts.validate_temp.METADATA_FILE", metadata_file)
    
    result = validate_temp.main(return_success=True)
    assert result is False


def test_main_success(tmp_path, monkeypatch):
    temp_dir = tmp_path / "images_temp"
    temp_dir.mkdir()
    metadata_file = temp_dir / "metadata.csv"
    
    # Create valid setup
    img1 = temp_dir / "IMG_0001.JPG"
    img1.write_bytes(b"FAKEIMAGE1")
    
    with open(metadata_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Filename", "Bottle type", "Glass color", "Fill level",
                        "Liquid color", "Label presence", "Cap presence", "Note"])
        writer.writerow(["IMG_0001.JPG", "euro", "brown", "filled", "transparent", "labeled", "opened", ""])
    
    monkeypatch.setattr("scripts.validate_temp.TEMP_DIR", temp_dir)
    monkeypatch.setattr("scripts.validate_temp.METADATA_FILE", metadata_file)
    
    result = validate_temp.main(return_success=True)
    assert result is True
