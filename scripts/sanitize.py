import sys
import argparse
from pathlib import Path

from PIL import Image, ExifTags
import cv2

IMAGES_DIR = Path("images")


def apply_exif_orientation(img: Image.Image) -> tuple[Image.Image, bool]:
    exif = img.getexif()
    if not exif:
        return img, False

    orientation_key = next(
        (t for t, n in ExifTags.TAGS.items() if n == "Orientation"), None
    )

    if orientation_key is None or orientation_key not in exif:
        return img, False

    orientation = exif[orientation_key]

    transforms = {
        2: (Image.FLIP_LEFT_RIGHT,),
        3: (Image.ROTATE_180,),
        4: (Image.FLIP_TOP_BOTTOM,),
        5: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_90),
        6: (Image.ROTATE_270,),
        7: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_270),
        8: (Image.ROTATE_90,),
    }

    if orientation not in transforms:
        return img, False

    for transform in transforms[orientation]:
        img = img.transpose(transform)

    return img, True


def sanitize_image(path: Path, output_quality: int = 95) -> tuple[bool, list[str]]:
    changes = []

    try:
        img = Image.open(path)
    except Exception as e:
        return False, [f"cannot open: {e}"]

    img, rotated = apply_exif_orientation(img)
    if rotated:
        changes.append("applied EXIF orientation")

    if img.mode != "RGB":
        changes.append(f"converted {img.mode} -> RGB")
        img = img.convert("RGB")

    original_suffix = path.suffix.lower()
    jpg_path = path.with_suffix(".jpg")

    img.save(
        jpg_path,
        "JPEG",
        quality=output_quality,
        optimize=True,
        progressive=False,
        subsampling=0,
        exif=b"",
        icc_profile=None,
    )

    if original_suffix not in (".jpg", ".jpeg"):
        changes.append(f"converted {original_suffix} -> .jpg")
        path.unlink()

    test_img = cv2.imread(str(jpg_path))
    if test_img is None:
        jpg_path.unlink(missing_ok=True)
        return False, ["OpenCV validation failed"]

    if not changes:
        changes.append("stripped metadata")

    return True, changes


def dry_run_report(files):
    has_exif = 0
    has_icc = 0
    needs_orientation = 0
    needs_conversion = 0

    orientation_key = next(
        (t for t, n in ExifTags.TAGS.items() if n == "Orientation"), None
    )

    for file in files:
        try:
            img = Image.open(file)

            exif = img.getexif()
            if exif:
                has_exif += 1

                if orientation_key and orientation_key in exif and exif[orientation_key] != 1:
                    needs_orientation += 1
                    print(f"  {file.name}: needs rotation (orientation={exif[orientation_key]})")

            if "icc_profile" in img.info:
                has_icc += 1

            if file.suffix.lower() not in (".jpg", ".jpeg"):
                needs_conversion += 1
                print(f"  {file.name}: needs conversion {file.suffix} -> .jpg")

        except Exception as e:
            print(f"  {file.name}: cannot open ({e})")

    print(f"\nSummary:")
    print(f"  Total files:            {len(files)}")
    print(f"  With EXIF metadata:     {has_exif}")
    print(f"  With ICC profile:       {has_icc}")
    print(f"  Need orientation fix:   {needs_orientation}")
    print(f"  Need format conversion: {needs_conversion}")


def main():
    parser = argparse.ArgumentParser(description="Sanitize dataset images")
    parser.add_argument("--dry", "-d", action="store_true", help="Dry run")
    parser.add_argument("--quality", "-q", type=int, default=95, help="JPG quality (1-100)")
    parser.add_argument("--verify", "-v", action="store_true", help="Verify no EXIF remains after processing")
    args = parser.parse_args()

    if not IMAGES_DIR.exists():
        print(f"Directory not found: {IMAGES_DIR}")
        sys.exit(1)

    files = sorted([
        f for f in IMAGES_DIR.iterdir()
        if not f.is_dir() and not f.name.startswith(".")
    ])

    if not files:
        print("No files found.")
        return

    print(f"\nSanitizing {len(files)} files in {IMAGES_DIR}/\n")

    if args.dry:
        print("Dry run — no files will be modified.\n")
        dry_run_report(files)
        return

    processed = 0
    errors = 0

    for file in files:
        ok, changes = sanitize_image(file, output_quality=args.quality)
        icon = "ok" if ok else "FAIL"
        print(f"  [{icon}] {file.name}: {', '.join(changes)}")

        if ok:
            processed += 1
        else:
            errors += 1

    print(f"\nDone: {processed} processed, {errors} errors")

    if args.verify:
        print("\nVerification:")
        issues = 0

        for file in sorted(IMAGES_DIR.glob("*.jpg")):
            img = Image.open(file)
            exif = img.getexif()
            if exif or "icc_profile" in img.info:
                issues += 1
                print(f"  {file.name}: residual metadata found")

        if issues == 0:
            print("  All files clean.")
        else:
            print(f"  {issues} files with residual metadata!")


if __name__ == "__main__":
    main()
