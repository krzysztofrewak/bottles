import shutil
import pytest
from pathlib import Path


@pytest.fixture
def temp_images(tmp_path):
    """
    Creates a temporary images/ directory filled with synthetic test images.
    This isolates tests from the real dataset.
    """
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    synthetic_files = {
        "euro_brown_filled_light_labeled_open_001.jpg": b"FAKEIMAGE1",
        "euro_brown_filled_light_labeled_open_002.jpg": b"FAKEIMAGE1",  # intentional duplicate content
        "vichy_brown_filled_dark_labeled_open_001.jpg": b"FAKEIMAGE2",
        "vichy_brown_filled_dark_labeled_open_002.jpg": b"FAKEIMAGE3",
        "vichy_brown_filled_dark_labeled_open_003.jpg": b"FAKEIMAGE4",
        "vichy_brown_filled_dark_labeled_open_004.jpg": b"FAKEIMAGE5",
        "vichy_brown_filled_dark_labeled_open_005.HEIC": b"FAKEIMAGE6",
        "vichy_brown_filled_dark_labeled_open_006.HEIC": b"FAKEIMAGE7",
        "invalid_name.jpg": b"FAKEIMAGE8",
    }

    for name, content in synthetic_files.items():
        (images_dir / name).write_bytes(content)

    return images_dir
