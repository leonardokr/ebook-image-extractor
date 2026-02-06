"""
Base extractor class with common functionality for all ebook formats.
"""

import os
import shutil
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from .exceptions import OutputDirectoryError


@dataclass
class ExtractionStats:
    """Statistics for image extraction."""

    saved: int = 0
    ignored: int = 0
    missing: int = 0
    duplicates: int = 0
    filtered_by_size: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "saved": self.saved,
            "ignored": self.ignored,
            "missing": self.missing,
            "duplicates": self.duplicates,
            "filtered_by_size": self.filtered_by_size,
        }


@dataclass
class ImageInfo:
    """Information about an extracted image."""

    data: bytes
    extension: str
    original_path: str = ""
    hash: str = ""
    width: int = 0
    height: int = 0


@dataclass
class BookMetadata:
    """Metadata extracted from an ebook."""

    title: str = ""
    author: str = ""
    publisher: str = ""
    language: str = ""
    cover_image: Optional[bytes] = None


class BaseExtractor(ABC):
    """
    Abstract base class for ebook image extractors.
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

    DEFAULT_MIN_IMAGE_SIZE: int = 1024

    def __init__(
        self,
        ignored_hashes: Optional[Set[str]] = None,
        min_image_size: int = 0,
        enable_deduplication: bool = True,
        logger: Optional[logging.Logger] = None,
        show_progress: bool = True,
    ):
        self.ignored_hashes = ignored_hashes or self.DEFAULT_IGNORED_HASHES.copy()
        self.min_image_size = min_image_size
        self.enable_deduplication = enable_deduplication
        self._extracted_hashes: Set[str] = set()
        self.logger = logger or self._setup_logger()
        self.show_progress = show_progress and TQDM_AVAILABLE

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def set_log_level(self, level: int) -> None:
        self.logger.setLevel(level)

    def hash_bytes_sha256(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def add_ignored_hash(self, hash_value: str) -> None:
        self.ignored_hashes.add(hash_value)
        self.logger.debug(f"Added hash to ignore list: {hash_value[:16]}...")

    def remove_ignored_hash(self, hash_value: str) -> None:
        self.ignored_hashes.discard(hash_value)
        self.logger.debug(f"Removed hash from ignore list: {hash_value[:16]}...")

    def should_skip_image(
        self, data: bytes, img_hash: Optional[str] = None
    ) -> Tuple[bool, str]:
        if self.min_image_size > 0 and len(data) < self.min_image_size:
            return True, "too_small"

        if img_hash is None:
            img_hash = self.hash_bytes_sha256(data)

        if img_hash in self.ignored_hashes:
            return True, "ignored_hash"

        if self.enable_deduplication and img_hash in self._extracted_hashes:
            return True, "duplicate"

        return False, ""

    def prepare_output_directory(self, output_dir: str, clean: bool = True) -> None:
        try:
            if clean and os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            self.logger.debug(f"Prepared output directory: {output_dir}")
        except OSError as e:
            raise OutputDirectoryError(output_dir, str(e))

    def save_image(
        self,
        data: bytes,
        output_dir: str,
        index: int,
        extension: str,
    ) -> str:
        filename = f"{index:04}{extension}"
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "wb") as f:
            f.write(data)

        img_hash = self.hash_bytes_sha256(data)
        self._extracted_hashes.add(img_hash)

        self.logger.debug(f"Saved: {filename} ({len(data)} bytes)")
        return output_path

    def reset_extraction_state(self) -> None:
        self._extracted_hashes.clear()

    def print_stats(self, stats: ExtractionStats, prefix: str = "") -> None:
        print(f"{prefix}Total images extracted: {stats.saved}")
        if stats.ignored > 0:
            print(f"{prefix}{stats.ignored} image(s) ignored by hash.")
        if stats.duplicates > 0:
            print(f"{prefix}{stats.duplicates} duplicate image(s) skipped.")
        if stats.filtered_by_size > 0:
            print(f"{prefix}{stats.filtered_by_size} image(s) filtered by size.")
        if stats.missing > 0:
            print(f"{prefix}{stats.missing} image(s) not found.")
        else:
            print(f"{prefix}No missing images.")

    @abstractmethod
    def find_files(self, directory: str, recursive: bool = False) -> List[str]:
        pass

    @abstractmethod
    def extract_images(
        self,
        file_path: str,
        output_dir: str,
        dry_run: bool = False,
    ) -> ExtractionStats:
        pass

    @abstractmethod
    def extract_metadata(self, file_path: str) -> BookMetadata:
        pass

    def _get_progress_iterator(self, iterable, total: int, desc: str):
        if self.show_progress:
            return tqdm(iterable, total=total, desc=desc, unit="file")
        return iterable

    def extract_from_directory(
        self,
        directory: str,
        recursive: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, ExtractionStats]:
        files = self.find_files(directory, recursive)

        if not files:
            self.logger.info("No supported files found.")
            return {}

        self.logger.info(f"{len(files)} file(s) found")
        for f in files:
            self.logger.info(f"  - {os.path.basename(f)}")

        results: Dict[str, ExtractionStats] = {}
        total_stats = ExtractionStats()

        file_iterator = self._get_progress_iterator(files, len(files), "Extracting")

        for file_path in file_iterator:
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = os.path.join(directory, file_name)

            if not self.show_progress:
                self.logger.info(f"Processing: {os.path.basename(file_path)}")

            if dry_run:
                print(f"[DRY RUN] Would extract to: {output_dir}")

            self.reset_extraction_state()

            stats = self.extract_images(file_path, output_dir, dry_run)
            results[file_path] = stats

            total_stats.saved += stats.saved
            total_stats.ignored += stats.ignored
            total_stats.missing += stats.missing
            total_stats.duplicates += stats.duplicates
            total_stats.filtered_by_size += stats.filtered_by_size

            if not self.show_progress:
                self.print_stats(stats, prefix="  ")
                print(f"  Extraction completed for: {output_dir}")

        print(f"\n=== TOTAL STATISTICS ===")
        print(f"Files processed: {len(files)}")
        self.print_stats(total_stats)

        return results
