#!/usr/bin/env python3
"""Create a smaller WebP copy of the local console fallback gallery.

Source files are never modified. Point ``--output`` at a separate directory
and switch the gallery only after reviewing the generated images.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError

ImageFile.LOAD_TRUNCATED_IMAGES = True


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Existing fallback image directory")
    parser.add_argument("--output", required=True, type=Path, help="Separate directory for optimized WebP files")
    parser.add_argument("--max-dimension", type=int, default=1200, help="Maximum width or height (default: 1200)")
    parser.add_argument("--quality", type=int, default=86, help="WebP quality from 0-100 (default: 86)")
    parser.add_argument("--check", action="store_true", help="Print the planned work without writing files")
    return parser.parse_args()


def image_files(source: Path) -> list[Path]:
    return sorted(
        (path for path in source.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS),
        key=lambda path: str(path).lower(),
    )


def output_path(source: Path, output: Path, image: Path) -> Path:
    return output / image.relative_to(source).with_suffix(".webp")


def validate_arguments(args: argparse.Namespace) -> tuple[Path, Path]:
    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_dir():
        raise ValueError(f"Source directory does not exist: {source}")
    if args.max_dimension <= 0:
        raise ValueError("--max-dimension must be greater than zero")
    if not 0 <= args.quality <= 100:
        raise ValueError("--quality must be between 0 and 100")
    if output == source or source in output.parents:
        raise ValueError("--output must be outside --source to keep generated files out of the gallery")
    return source, output


def optimize_image(source: Path, destination: Path, max_dimension: int, quality: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        normalized = ImageOps.exif_transpose(image)
        normalized.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        if normalized.mode not in {"RGB", "RGBA"}:
            normalized = normalized.convert("RGBA" if "transparency" in normalized.info else "RGB")
        normalized.save(destination, format="WEBP", quality=quality, method=6)


def main() -> int:
    args = parse_args()
    try:
        source, output = validate_arguments(args)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    files = image_files(source)
    action = "would convert" if args.check else "converting"
    print(f"{len(files)} image{'s' if len(files) != 1 else ''} {action} from {source}")
    if args.check:
        for image in files:
            print(f"  {image.relative_to(source)} -> {output_path(source, output, image).relative_to(output)}")
        return 0

    failures: list[str] = []
    for image in files:
        destination = output_path(source, output, image)
        try:
            optimize_image(image, destination, args.max_dimension, args.quality)
            print(f"  {image.relative_to(source)} -> {destination.relative_to(output)}")
        except (OSError, UnidentifiedImageError) as error:
            failures.append(f"{image}: {error}")

    if failures:
        print("Some images could not be converted:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(f"Completed. Original files remain in {source}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
