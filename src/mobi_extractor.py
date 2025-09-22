"""
MOBI Image Extractor

A Python tool to extract images from MOBI/AZW files with advanced filtering and organization features.
Compatible with the epub-extract-images project structure.
"""

import struct
import os
import shutil
import hashlib
from typing import List, Set, Dict, Optional, Tuple


class MobiImageExtractor:
    """
    Extracts images from MOBI files with filtering and organization capabilities.
    """

    IMAGE_EXTENSIONS: Set[str] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".bmp",
    }

    DEFAULT_IGNORED_HASHES: Set[str] = {
        "1fcf4c601de84ae1d66e36f93b83b33b453f77aeb345be830f1fc66439fdb50d",
        "933f630f9a34dd68d5047813ec3272b8b3634011e5ed90be50dfd765a1303263",
        "ff1e53b8a020868ad267555daf1091ddafdb103a6364a87275bbf34a78ba7c84",
    }

    def __init__(self, ignored_hashes: Optional[Set[str]] = None):
        """
        Initialize the MOBI image extractor.

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

    def hash_bytes_sha256(self, data: bytes) -> str:
        """
        Calculate SHA256 hash of byte data.

        Args:
            data: Byte data to hash

        Returns:
            SHA256 hash as hexadecimal string
        """
        return hashlib.sha256(data).hexdigest()

    def find_mobi_files(self, directory: str) -> List[str]:
        """
        Find all MOBI files in the specified directory.

        Args:
            directory: Directory to search for MOBI files

        Returns:
            List of MOBI file paths
        """
        mobi_files = []
        for file in os.listdir(directory):
            if file.lower().endswith((".mobi", ".azw", ".azw3")):
                mobi_files.append(os.path.join(directory, file))
        return mobi_files

    def _is_image_data(self, data: bytes) -> bool:
        """
        Check if data represents an image based on magic bytes.

        Args:
            data: Byte data to check

        Returns:
            True if data appears to be an image
        """
        if len(data) < 8:
            return False

        # JPEG
        if data.startswith(b"\xff\xd8\xff"):
            return True
        # PNG
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return True
        # GIF
        if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
            return True
        # BMP
        if data.startswith(b"BM"):
            return True
        # WebP
        if len(data) > 12 and data[8:12] == b"WEBP":
            return True

        return False

    def _get_image_extension(self, data: bytes) -> str:
        """
        Determine image extension from data.

        Args:
            data: Image byte data

        Returns:
            File extension string
        """
        if data.startswith(b"\xff\xd8\xff"):
            return ".jpg"
        elif data.startswith(b"\x89PNG"):
            return ".png"
        elif data.startswith(b"GIF8"):
            return ".gif"
        elif data.startswith(b"BM"):
            return ".bmp"
        elif len(data) > 12 and data[8:12] == b"WEBP":
            return ".webp"
        else:
            return ".jpg"  # Default fallback

    def _read_pdb_records(self, data: bytes) -> List[Tuple[int, int]]:
        """
        Read PDB record offsets from MOBI file.

        Args:
            data: MOBI file data

        Returns:
            List of (start_offset, end_offset) tuples
        """
        if len(data) < 78:
            return []

        num_records = struct.unpack(">H", data[76:78])[0]

        record_offsets = []
        for i in range(num_records):
            offset_pos = 78 + (i * 8)
            if offset_pos + 4 <= len(data):
                offset = struct.unpack(">L", data[offset_pos : offset_pos + 4])[0]
                record_offsets.append(offset)

        records = []
        for i in range(len(record_offsets)):
            start = record_offsets[i]
            end = record_offsets[i + 1] if i + 1 < len(record_offsets) else len(data)
            if start < end and start < len(data):
                records.append((start, end))

        return records

    def extract_images_from_mobi(
        self, mobi_path: str, output_dir: str
    ) -> Dict[str, int]:
        """
        Extract images from a single MOBI file.

        Args:
            mobi_path: Path to the MOBI file
            output_dir: Output directory for extracted images

        Returns:
            Dictionary with extraction statistics
        """
        stats = {"saved": 0, "ignored": 0, "missing": 0}

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        try:
            with open(mobi_path, "rb") as f:
                data = f.read()

            if b"BOOKMOBI" not in data[:100]:
                print(f"Warning: {mobi_path} may not be a valid MOBI file")
                return stats

            records = self._read_pdb_records(data)
            print(f"Found {len(records)} records in MOBI file")

            for start, end in records:
                if start >= len(data) or end > len(data):
                    continue

                record_data = data[start:end]

                if self._is_image_data(record_data):
                    img_hash = self.hash_bytes_sha256(record_data)

                    if img_hash in self.ignored_hashes:
                        stats["ignored"] += 1
                        continue

                    ext = self._get_image_extension(record_data)
                    filename = f"{stats['saved']:04}{ext}"

                    output_path = os.path.join(output_dir, filename)
                    with open(output_path, "wb") as img_file:
                        img_file.write(record_data)

                    stats["saved"] += 1

        except Exception as e:
            print(f"Error processing {mobi_path}: {e}")
            return stats

        return stats

    def extract_from_directory(self, directory: str) -> None:
        """
        Extract images from all MOBI files in a directory.

        Args:
            directory: Directory containing MOBI files
        """
        mobi_files = self.find_mobi_files(directory)

        if not mobi_files:
            print("No .mobi/.azw/.azw3 files found.")
            return

        print(f"{len(mobi_files)} MOBI file(s) found:")
        for mobi_file in mobi_files:
            print(f"  - {os.path.basename(mobi_file)}")

        total_stats = {"saved": 0, "ignored": 0, "missing": 0}

        for mobi_path in mobi_files:
            mobi_name = os.path.splitext(os.path.basename(mobi_path))[0]
            output_dir = os.path.join(directory, mobi_name)

            print(f"\nProcessing: {os.path.basename(mobi_path)}")

            stats = self.extract_images_from_mobi(mobi_path, output_dir)

            for key in total_stats:
                total_stats[key] += stats[key]

            print(f"  Total images extracted: {stats['saved']}")
            print(f"  {stats['ignored']} image(s) ignored by hash.")
            if stats["missing"] > 0:
                print(f"  {stats['missing']} image(s) not found.")
            else:
                print("  No missing images.")

            print(f"  Extraction completed for: {output_dir}")

        print("\n=== TOTAL STATISTICS ===")
        print(f"MOBI files processed: {len(mobi_files)}")
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
