"""
EPUB Image Extractor

A Python tool to extract images from EPUB files with advanced filtering and organization features.
"""

import zipfile
import os
import shutil
import hashlib
from typing import List, Set, Dict, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag


class EPUBImageExtractor:
    """
    Extracts images from EPUB files with filtering and organization capabilities.
    """

    IMAGE_EXTENSIONS: Set[str] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".bmp",
        ".svg",
    }

    DEFAULT_IGNORED_HASHES: Set[str] = {
        "1fcf4c601de84ae1d66e36f93b83b33b453f77aeb345be830f1fc66439fdb50d",
        "933f630f9a34dd68d5047813ec3272b8b3634011e5ed90be50dfd765a1303263",
        "ff1e53b8a020868ad267555daf1091ddafdb103a6364a87275bbf34a78ba7c84",
    }

    def __init__(self, ignored_hashes: Optional[Set[str]] = None):
        """
        Initialize the EPUB image extractor.

        Args:
            ignored_hashes: Set of SHA256 hashes to ignore during extraction
        """
        self.ignored_hashes = ignored_hashes or self.DEFAULT_IGNORED_HASHES.copy()
        self.stats: Dict[str, int] = {
            "processed_files": 0,
            "extracted_images": 0,
            "ignored_images": 0,
            "missing_images": 0,
        }

    def normalize_path(self, base_path: str, relative_path: str) -> str:
        """
        Normalize relative paths in EPUB files.

        Args:
            base_path: Base file path
            relative_path: Relative path to normalize

        Returns:
            Normalized path string
        """
        base_dir = os.path.dirname(base_path)
        return os.path.normpath(os.path.join(base_dir, relative_path)).replace(
            "\\", "/"
        )

    def hash_bytes_sha256(self, data: bytes) -> str:
        """
        Calculate SHA256 hash of byte data.

        Args:
            data: Byte data to hash

        Returns:
            SHA256 hash as hexadecimal string
        """
        return hashlib.sha256(data).hexdigest()

    def find_epub_files(self, directory: str) -> List[str]:
        """
        Find all EPUB files in the specified directory.

        Args:
            directory: Directory to search for EPUB files

        Returns:
            List of EPUB file paths
        """
        epub_files = []
        for file in os.listdir(directory):
            if file.lower().endswith(".epub"):
                epub_files.append(os.path.join(directory, file))
        return epub_files

    def extract_image_references(
        self, zipf: zipfile.ZipFile, all_files: List[str]
    ) -> tuple[List[str], List[str]]:
        """
        Extract image references from HTML/XHTML files in the EPUB.

        Args:
            zipf: Open ZipFile object
            all_files: List of all files in the EPUB

        Returns:
            Tuple of (found_images, missing_images)
        """
        html_files = [f for f in all_files if f.endswith((".xhtml", ".html"))]
        image_paths = []
        missing_images = []

        for html_file in html_files:
            try:
                with zipf.open(html_file) as f:
                    soup = BeautifulSoup(f.read(), "html.parser")
                    for img_tag in soup.find_all("img"):
                        if isinstance(img_tag, Tag):
                            raw_src = img_tag.get("src")
                            if raw_src and isinstance(raw_src, str):
                                resolved = self.normalize_path(html_file, raw_src)
                                if (
                                    resolved in all_files
                                    and resolved not in image_paths
                                ):
                                    image_paths.append(resolved)
                                elif resolved not in all_files:
                                    missing_images.append(resolved)
            except Exception as e:
                print(f"Error processing {html_file}: {e}")

        return image_paths, missing_images

    def extract_images_from_epub(
        self, epub_path: str, output_dir: str, use_html_refs: bool = True
    ) -> Dict[str, int]:
        """
        Extract images from a single EPUB file.

        Args:
            epub_path: Path to the EPUB file
            output_dir: Output directory for extracted images
            use_html_refs: Whether to use HTML references or extract all images

        Returns:
            Dictionary with extraction statistics
        """
        stats = {"saved": 0, "ignored": 0, "missing": 0}

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        with zipfile.ZipFile(epub_path, "r") as zipf:
            all_files = zipf.namelist()

            if use_html_refs:
                image_paths, missing_images = self.extract_image_references(
                    zipf, all_files
                )
                if not image_paths:
                    image_paths = [
                        f
                        for f in all_files
                        if os.path.splitext(f)[1].lower() in self.IMAGE_EXTENSIONS
                    ]
                    print(
                        f"No valid HTML images found. Using {len(image_paths)} images from ZIP."
                    )
                else:
                    print(f"{len(image_paths)} image(s) found via HTML.")
            else:
                image_paths = [
                    f
                    for f in all_files
                    if os.path.splitext(f)[1].lower() in self.IMAGE_EXTENSIONS
                ]
                missing_images = []
                print(f"Extracting all {len(image_paths)} images found in ZIP.")

            for img_path in image_paths:
                try:
                    img_data = zipf.read(img_path)
                    img_hash = self.hash_bytes_sha256(img_data)

                    if img_hash in self.ignored_hashes:
                        stats["ignored"] += 1
                        continue

                    ext = os.path.splitext(img_path)[1].lower()
                    filename = f"{stats['saved']:04}{ext}"

                    with open(os.path.join(output_dir, filename), "wb") as out_file:
                        out_file.write(img_data)
                    stats["saved"] += 1

                except Exception:
                    missing_images.append(img_path)

            stats["missing"] = len(set(missing_images))

        return stats

    def extract_from_directory(
        self, directory: str, use_html_refs: bool = True
    ) -> None:
        """
        Extract images from all EPUB files in a directory.

        Args:
            directory: Directory containing EPUB files
            use_html_refs: Whether to use HTML references or extract all images
        """
        epub_files = self.find_epub_files(directory)

        if not epub_files:
            print("No .epub files found.")
            return

        print(f"{len(epub_files)} EPUB file(s) found:")
        for epub_file in epub_files:
            print(f"  - {os.path.basename(epub_file)}")

        total_stats = {"saved": 0, "ignored": 0, "missing": 0}

        for epub_path in epub_files:
            epub_name = os.path.splitext(os.path.basename(epub_path))[0]
            output_dir = os.path.join(directory, epub_name)

            print(f"\nProcessing: {os.path.basename(epub_path)}")

            stats = self.extract_images_from_epub(epub_path, output_dir, use_html_refs)

            for key in total_stats:
                total_stats[key] += stats[key]

            print(f"  Total images extracted: {stats['saved']}")
            print(f"  {stats['ignored']} image(s) ignored by hash.")
            if stats["missing"] > 0:
                print(
                    f"  {stats['missing']} image(s) not found (referenced but missing)."
                )
            else:
                print("  No missing referenced images.")

            print(f"  Extraction completed for: {output_dir}")

        print("\n=== TOTAL STATISTICS ===")
        print(f"EPUB files processed: {len(epub_files)}")
        print(f"Total images extracted: {total_stats['saved']}")
        print(f"Total images ignored: {total_stats['ignored']}")
        print(f"Total missing images: {total_stats['missing']}")

    def add_ignored_hash(self, hash_value: str) -> None:
        """
        Add a hash to the ignored list.

        Args:
            hash_value: SHA256 hash to ignore
        """
        self.ignored_hashes.add(hash_value)

    def remove_ignored_hash(self, hash_value: str) -> None:
        """
        Remove a hash from the ignored list.

        Args:
            hash_value: SHA256 hash to remove from ignored list
        """
        self.ignored_hashes.discard(hash_value)


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract images from EPUB files")
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing EPUB files (default: current directory)",
    )
    parser.add_argument(
        "--all-images",
        action="store_true",
        help="Extract all images, not just those referenced in HTML",
    )
    parser.add_argument(
        "--add-ignore-hash", help="Add a SHA256 hash to the ignore list"
    )

    args = parser.parse_args()

    extractor = EPUBImageExtractor()

    if args.add_ignore_hash:
        extractor.add_ignored_hash(args.add_ignore_hash)
        print(f"Hash added to ignore list: {args.add_ignore_hash}")

    extractor.extract_from_directory(args.directory, not args.all_images)


if __name__ == "__main__":
    main()
