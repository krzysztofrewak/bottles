import sys
from pathlib import Path

import cv2
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

IMAGES_TEMP_DIR = Path(__file__).resolve().parent.parent / "images_temp"

def convert_heic_validated(heic_path: Path, output_quality: int = 95) -> bool:
    """Convert HEIC to JPG and validate with OpenCV."""
    try:
        img = Image.open(heic_path)

        if img.mode != "RGB":
            img = img.convert("RGB")

        jpg_path = heic_path.with_suffix(".jpg")

        img.save(
            jpg_path,
            "JPEG",
            quality=output_quality,
            optimize=True,
            progressive=False,
            subsampling=0,
        )

        test_img = cv2.imread(str(jpg_path))

        if test_img is None:
            print(f"  failed: {heic_path.name} (OpenCV validation failed)")
            jpg_path.unlink(missing_ok=True)
            return False

        heic_path.unlink()
        print(f"  converted: {heic_path.name} -> {jpg_path.name}")
        return True

    except Exception as e:
        print(f"  error: {heic_path.name} ({e})")
        return False


def batch_convert_validated(directory: Path, quality: int = 95):
    """Batch convert all HEIC files with validation."""
    heic_files = []
    for ext in ["*.heic", "*.HEIC", "*.heif", "*.HEIF"]:
        heic_files.extend(directory.glob(ext))

    if not heic_files:
        print(f"No HEIC files found in {directory}")
        return

    print(f"Found {len(heic_files)} HEIC files (quality: {quality})")

    successful = 0
    failed = 0

    for heic_path in sorted(heic_files):
        if convert_heic_validated(heic_path, quality):
            successful += 1
        else:
            failed += 1

    print(f"Converted: {successful}, failed: {failed}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert HEIC to JPG with validation")
    parser.add_argument("--quality", type=int, default=95, help="JPG quality (1-100)")
    args = parser.parse_args()

    if not IMAGES_TEMP_DIR.exists():
        print(f"Directory not found: {IMAGES_TEMP_DIR}")
        sys.exit(1)

    batch_convert_validated(IMAGES_TEMP_DIR, args.quality)


if __name__ == "__main__":
    main()
