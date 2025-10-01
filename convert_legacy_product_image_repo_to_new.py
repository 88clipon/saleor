#!/usr/bin/env python3
"""Convert product-image-repo folder structure.

This script:
1. Scans product-image-repo for SKU folders with -B and -S suffixes
2. Extracts JPG images from -B folders to product-image-repo-new/{SKU}/B/images/
3. Compares -S folder images with -B images using perceptual hashing
4. Only creates -S folder if images are different from -B
5. Keeps original folder intact
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional

try:
    import imagehash
    from PIL import Image
except ImportError:
    print("Error: Required libraries not installed.")
    print("Please run: pip install pillow imagehash")
    exit(1)


def find_jpg_images(folder: Path) -> List[Path]:
    """Recursively find JPG images named img01-img05 in a folder."""
    valid_names = {'img01', 'img02', 'img03', 'img04', 'img05'}
    jpg_files = []

    for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
        for img_path in folder.rglob(ext):
            # Get filename without extension
            filename_without_ext = img_path.stem.lower()
            if filename_without_ext in valid_names:
                jpg_files.append(img_path)

    return sorted(jpg_files)


def calculate_image_hash(image_path: Path) -> Optional[imagehash.ImageHash]:
    """Calculate perceptual hash of an image."""
    try:
        with Image.open(image_path) as img:
            return imagehash.average_hash(img)
    except Exception as e:
        print(f"Warning: Could not hash {image_path}: {e}")
        return None


def images_are_similar(img1_path: Path, img2_path: Path, threshold: int = 5) -> bool:
    """Compare two images using perceptual hashing.

    Returns True if images are similar (hash difference <= threshold).
    """
    hash1 = calculate_image_hash(img1_path)
    hash2 = calculate_image_hash(img2_path)

    if hash1 is None or hash2 is None:
        return False

    difference = hash1 - hash2
    return difference <= threshold


def group_sku_folders(repo_path: Path) -> Dict[str, Dict[str, Path]]:
    """Group folders by SKU base name.

    Returns: {SKU: {'B': path, 'S': path}}
    """
    sku_groups = defaultdict(dict)

    for folder in repo_path.iterdir():
        if not folder.is_dir():
            continue

        folder_name = folder.name

        # Check if folder ends with -B or -S
        if folder_name.endswith('-B'):
            sku = folder_name[:-2]  # Remove -B suffix
            sku_groups[sku]['B'] = folder
        elif folder_name.endswith('-S'):
            sku = folder_name[:-2]  # Remove -S suffix
            sku_groups[sku]['S'] = folder

    # Filter to only include SKUs that have both -B and -S folders
    complete_skus = {
        sku: folders
        for sku, folders in sku_groups.items()
        if 'B' in folders and 'S' in folders
    }

    return complete_skus


def compare_image_sets(b_images: List[Path], s_images: List[Path]) -> bool:
    """Compare image sets from -B and -S folders.

    Returns True if all images are similar (folders are identical).
    """
    if len(b_images) != len(s_images):
        return False

    if len(b_images) == 0:
        return True  # Both empty, consider them the same

    # Create mapping by filename
    b_by_name = {img.name: img for img in b_images}
    s_by_name = {img.name: img for img in s_images}

    # Check if filenames match
    if set(b_by_name.keys()) != set(s_by_name.keys()):
        return False

    # Compare each pair of images
    for filename in b_by_name.keys():
        b_img = b_by_name[filename]
        s_img = s_by_name[filename]

        if not images_are_similar(b_img, s_img):
            return False

    return True


def copy_images(source_images: List[Path], dest_folder: Path) -> int:
    """Copy images to destination folder.

    Returns number of images copied.
    """
    dest_folder.mkdir(parents=True, exist_ok=True)

    copied = 0
    for img in source_images:
        dest_path = dest_folder / img.name
        try:
            shutil.copy2(img, dest_path)
            copied += 1
        except Exception as e:
            print(f"Warning: Could not copy {img} to {dest_path}: {e}")

    return copied


def convert_repo(source_repo: Path, dest_repo: Path):
    """Convert product-image-repo to new structure."""

    print(f"Scanning {source_repo}...")
    sku_groups = group_sku_folders(source_repo)

    print(f"Found {len(sku_groups)} SKUs with both -B and -S folders\n")

    if not sku_groups:
        print("No SKU folders found with both -B and -S suffixes.")
        return

    # Create destination folder
    dest_repo.mkdir(parents=True, exist_ok=True)

    stats = {
        'total_skus': len(sku_groups),
        'skus_with_b_only': 0,
        'skus_with_b_and_s': 0,
        'total_b_images': 0,
        'total_s_images': 0,
    }

    for sku, folders in sorted(sku_groups.items()):
        print(f"Processing {sku}...")

        # Find images in -B folder
        b_folder = folders['B']
        b_images = find_jpg_images(b_folder)

        if not b_images:
            print(f"  Warning: No JPG images found in {b_folder.name}")
            continue

        # Find images in -S folder
        s_folder = folders['S']
        s_images = find_jpg_images(s_folder)

        # Copy B images
        b_dest = dest_repo / sku / 'B' / 'images'
        copied_b = copy_images(b_images, b_dest)
        stats['total_b_images'] += copied_b
        print(f"  ✓ Copied {copied_b} images to {sku}/B/images/")

        # Compare S images with B images
        if s_images:
            images_identical = compare_image_sets(b_images, s_images)

            if images_identical:
                print(f"  ℹ S images identical to B images - skipping S folder")
                stats['skus_with_b_only'] += 1
            else:
                # Copy S images
                s_dest = dest_repo / sku / 'S' / 'images'
                copied_s = copy_images(s_images, s_dest)
                stats['total_s_images'] += copied_s
                print(f"  ✓ Copied {copied_s} images to {sku}/S/images/")
                stats['skus_with_b_and_s'] += 1
        else:
            print(f"  ℹ No images in S folder - skipping S folder")
            stats['skus_with_b_only'] += 1

        print()

    # Print summary
    print("=" * 60)
    print("Conversion Summary:")
    print("=" * 60)
    print(f"Total SKUs processed: {stats['total_skus']}")
    print(f"SKUs with B only: {stats['skus_with_b_only']}")
    print(f"SKUs with B and S: {stats['skus_with_b_and_s']}")
    print(f"Total B images copied: {stats['total_b_images']}")
    print(f"Total S images copied: {stats['total_s_images']}")
    print(f"\nNew structure created at: {dest_repo}")


def main():
    # Assuming script is in saleor/ folder
    script_dir = Path(__file__).parent
    source_repo = script_dir.parent / 'product-image-repo'
    dest_repo = script_dir.parent / 'product-image-repo-new1'

    # Also check in storefront/public
    if not source_repo.exists():
        source_repo = script_dir.parent / 'storefront' / 'public' / 'product-image-repo'

    if not source_repo.exists():
        print(f"Error: product-image-repo not found at {source_repo}")
        print("Please ensure the folder exists.")
        return

    print("Product Image Repository Converter")
    print("=" * 60)
    print(f"Source: {source_repo}")
    print(f"Destination: {dest_repo}")
    print()

    if dest_repo.exists():
        response = input(f"{dest_repo} already exists. Remove it? (y/N): ")
        if response.lower() == 'y':
            shutil.rmtree(dest_repo)
            print(f"Removed {dest_repo}\n")
        else:
            print("Aborting.")
            return

    convert_repo(source_repo, dest_repo)


if __name__ == '__main__':
    main()
