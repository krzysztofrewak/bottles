from PIL import Image
from PIL.ExifTags import Base

from scripts import sanitize


def test_sanitize_strips_exif(tmp_path):
    path = tmp_path / "test.jpg"

    img = Image.new("RGB", (100, 100), color="red")
    exif = img.getexif()
    exif[Base.Make] = "TestCamera"
    img.save(path, "JPEG", exif=exif.tobytes())

    ok, changes = sanitize.sanitize_image(path)
    assert ok is True

    result = Image.open(path)
    assert len(result.getexif()) == 0


def test_sanitize_applies_orientation(tmp_path):
    path = tmp_path / "rotated.jpg"

    img = Image.new("RGB", (200, 100), color="blue")
    exif = img.getexif()
    exif[Base.Orientation] = 6
    img.save(path, "JPEG", exif=exif.tobytes())

    ok, changes = sanitize.sanitize_image(path)
    assert ok is True
    assert any("orientation" in c for c in changes)

    result = Image.open(path)
    assert result.size == (100, 200)


def test_sanitize_converts_png(tmp_path):
    png_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), color="green")
    img.save(png_path, "PNG")

    ok, changes = sanitize.sanitize_image(png_path)
    assert ok is True
    assert any(".png" in c for c in changes)
    assert not png_path.exists()
    assert (tmp_path / "test.jpg").exists()


def test_sanitize_converts_rgba(tmp_path):
    png_path = tmp_path / "rgba.png"
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    img.save(png_path, "PNG")

    ok, changes = sanitize.sanitize_image(png_path)
    assert ok is True
    assert any("RGBA" in c for c in changes)


def test_sanitize_invalid_file(tmp_path):
    bad_path = tmp_path / "corrupted.jpg"
    bad_path.write_bytes(b"NOT A VALID IMAGE")

    ok, changes = sanitize.sanitize_image(bad_path)
    assert ok is False
    assert any("cannot open" in c for c in changes)


def test_apply_orientation_no_exif():
    img = Image.new("RGB", (200, 100), color="red")
    result, rotated = sanitize.apply_exif_orientation(img)
    assert rotated is False
    assert result.size == (200, 100)
