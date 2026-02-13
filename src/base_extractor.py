"""
Base extractor class with common functionality for all ebook formats.
"""

import os
import shutil
import hashlib
import logging
import threading
from abc import ABC, abstractmethod
from typing import List, Set, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from .exceptions import OutputDirectoryError
from .archive_exporter import export_directory_as_comic_archive
from .hash_cache import HashCache
from .image_analysis import ImageMetrics, parse_image_metrics
from .manifest import ExtractionManifest, ImageManifestItem, save_manifest
from .pdf_exporter import export_directory_as_pdf


@dataclass
class ExtractionStats:
    """Statistics for image extraction."""

    saved: int = 0
    ignored: int = 0
    missing: int = 0
    duplicates: int = 0
    filtered_by_size: int = 0
    filtered_by_dimensions: int = 0
    filtered_by_aspect_ratio: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "saved": self.saved,
            "ignored": self.ignored,
            "missing": self.missing,
            "duplicates": self.duplicates,
            "filtered_by_size": self.filtered_by_size,
            "filtered_by_dimensions": self.filtered_by_dimensions,
            "filtered_by_aspect_ratio": self.filtered_by_aspect_ratio,
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
        min_width: int = 0,
        min_height: int = 0,
        max_aspect_ratio: float = 0.0,
        enable_deduplication: bool = True,
        logger: Optional[logging.Logger] = None,
        show_progress: bool = True,
        write_manifest: bool = False,
        write_debug_order: bool = False,
        archive_format: Optional[str] = None,
        hash_cache_path: Optional[str] = None,
        parallelism: int = 1,
    ):
        self.ignored_hashes = ignored_hashes or self.DEFAULT_IGNORED_HASHES.copy()
        self.min_image_size = min_image_size
        self.min_width = min_width
        self.min_height = min_height
        self.max_aspect_ratio = max_aspect_ratio
        self.enable_deduplication = enable_deduplication
        self._thread_state = threading.local()
        self.logger = logger or self._setup_logger()
        self.show_progress = show_progress and TQDM_AVAILABLE
        self.write_manifest = write_manifest
        self.write_debug_order = write_debug_order
        self.archive_format = archive_format.lower() if archive_format else None
        self.parallelism = max(1, int(parallelism))
        self.hash_cache = HashCache(hash_cache_path) if hash_cache_path else None
        if self.hash_cache:
            self.hash_cache.load()

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
        self, data: bytes, img_hash: Optional[str] = None, metrics: Optional[ImageMetrics] = None
    ) -> Tuple[bool, str]:
        if self.min_image_size > 0 and len(data) < self.min_image_size:
            return True, "too_small"

        if metrics is None:
            metrics = parse_image_metrics(data)

        if self.min_width > 0 and metrics.width > 0 and metrics.width < self.min_width:
            return True, "too_narrow"

        if self.min_height > 0 and metrics.height > 0 and metrics.height < self.min_height:
            return True, "too_short"

        if self.max_aspect_ratio > 0 and metrics.aspect_ratio > 0:
            if metrics.aspect_ratio > self.max_aspect_ratio:
                return True, "extreme_aspect_ratio"

        if img_hash is None:
            img_hash = self.hash_bytes_sha256(data)

        if self.hash_cache and self.hash_cache.contains(img_hash):
            return True, "duplicate_cache"

        if img_hash in self.ignored_hashes:
            return True, "ignored_hash"

        if self.enable_deduplication and img_hash in self._get_extracted_hashes():
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
        classification: str = "page",
    ) -> str:
        filename = f"{index:04}_{classification}{extension}"
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "wb") as f:
            f.write(data)

        img_hash = self.hash_bytes_sha256(data)
        self._get_extracted_hashes().add(img_hash)
        if self.hash_cache:
            self.hash_cache.add(img_hash)

        self.logger.debug(f"Saved: {filename} ({len(data)} bytes)")
        return output_path

    def reset_extraction_state(self) -> None:
        self._thread_state.extracted_hashes = set()

    def _get_extracted_hashes(self) -> Set[str]:
        """Get per-thread extracted hash set.

        :return: Mutable set for current thread.
        """
        hashes = getattr(self._thread_state, "extracted_hashes", None)
        if hashes is None:
            hashes = set()
            self._thread_state.extracted_hashes = hashes
        return hashes

    def print_stats(self, stats: ExtractionStats, prefix: str = "") -> None:
        print(f"{prefix}Total images extracted: {stats.saved}")
        if stats.ignored > 0:
            print(f"{prefix}{stats.ignored} image(s) ignored by hash.")
        if stats.duplicates > 0:
            print(f"{prefix}{stats.duplicates} duplicate image(s) skipped.")
        if stats.filtered_by_size > 0:
            print(f"{prefix}{stats.filtered_by_size} image(s) filtered by size.")
        if stats.filtered_by_dimensions > 0:
            print(f"{prefix}{stats.filtered_by_dimensions} image(s) filtered by dimensions.")
        if stats.filtered_by_aspect_ratio > 0:
            print(f"{prefix}{stats.filtered_by_aspect_ratio} image(s) filtered by aspect ratio.")
        if stats.missing > 0:
            print(f"{prefix}{stats.missing} image(s) not found.")
        else:
            print(f"{prefix}No missing images.")

    def build_manifest(self, file_path: str, output_dir: str) -> ExtractionManifest:
        """Build an extraction manifest.

        :param file_path: Source ebook path.
        :param output_dir: Output directory path.
        :return: Manifest instance.
        """
        metadata = self.extract_metadata(file_path)
        manifest = ExtractionManifest.create(file_path, output_dir)
        manifest.title = metadata.title
        manifest.author = metadata.author
        manifest.publisher = metadata.publisher
        manifest.language = metadata.language
        return manifest

    def add_manifest_item(
        self,
        manifest: ExtractionManifest,
        index: int,
        filename: str,
        source_ref: str,
        image_hash: str,
        metrics: ImageMetrics,
        classification: str,
    ) -> None:
        """Append image item to manifest.

        :param manifest: Manifest object.
        :param index: Sequential output index.
        :param filename: Output filename.
        :param source_ref: Source path or record.
        :param image_hash: SHA256 hash.
        :param metrics: Parsed metrics.
        :param classification: Image role.
        """
        manifest.add_item(
            ImageManifestItem(
                index=index,
                filename=filename,
                source_ref=source_ref,
                image_hash=image_hash,
                bytes_size=metrics.size_bytes,
                width=metrics.width,
                height=metrics.height,
                classification=classification,
                mime_type=metrics.mime_type,
            )
        )

    def finalize_book_output(
        self,
        output_dir: str,
        manifest: Optional[ExtractionManifest],
        debug_order: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Finalize output files for a single book.

        :param output_dir: Output directory.
        :param manifest: Manifest payload.
        :param debug_order: Optional order debug payload.
        """
        if manifest and self.write_debug_order:
            manifest.debug_order = debug_order or {}
        if manifest and self.write_manifest:
            save_manifest(manifest, output_dir)
        if self.archive_format:
            if self.archive_format in {"cbz", "cbr"}:
                export_directory_as_comic_archive(output_dir, self.archive_format)
            elif self.archive_format == "pdf":
                export_directory_as_pdf(output_dir)

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

        if self.parallelism > 1:
            futures = {}
            with ThreadPoolExecutor(max_workers=self.parallelism) as executor:
                for file_path in files:
                    futures[executor.submit(self._extract_single_file, directory, file_path, dry_run)] = file_path
                for future in as_completed(futures):
                    file_path, stats = future.result()
                    results[file_path] = stats
                    total_stats.saved += stats.saved
                    total_stats.ignored += stats.ignored
                    total_stats.missing += stats.missing
                    total_stats.duplicates += stats.duplicates
                    total_stats.filtered_by_size += stats.filtered_by_size
                    total_stats.filtered_by_dimensions += stats.filtered_by_dimensions
                    total_stats.filtered_by_aspect_ratio += stats.filtered_by_aspect_ratio
        else:
            file_iterator = self._get_progress_iterator(files, len(files), "Extracting")
            for file_path in file_iterator:
                _, stats = self._extract_single_file(directory, file_path, dry_run)
                results[file_path] = stats

                total_stats.saved += stats.saved
                total_stats.ignored += stats.ignored
                total_stats.missing += stats.missing
                total_stats.duplicates += stats.duplicates
                total_stats.filtered_by_size += stats.filtered_by_size
                total_stats.filtered_by_dimensions += stats.filtered_by_dimensions
                total_stats.filtered_by_aspect_ratio += stats.filtered_by_aspect_ratio

                if not self.show_progress:
                    self.print_stats(stats, prefix="  ")
                    print(f"  Extraction completed for: {os.path.join(directory, os.path.splitext(os.path.basename(file_path))[0])}")

        print(f"\n=== TOTAL STATISTICS ===")
        print(f"Files processed: {len(files)}")
        self.print_stats(total_stats)

        if self.hash_cache:
            self.hash_cache.save()

        return results

    def _extract_single_file(
        self, directory: str, file_path: str, dry_run: bool
    ) -> Tuple[str, ExtractionStats]:
        """Extract one file and return stats.

        :param directory: Output base directory.
        :param file_path: Ebook path.
        :param dry_run: Dry run flag.
        :return: File path and extraction statistics.
        """
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(directory, file_name)

        if not self.show_progress:
            self.logger.info(f"Processing: {os.path.basename(file_path)}")

        if dry_run:
            print(f"[DRY RUN] Would extract to: {output_dir}")

        self.reset_extraction_state()

        stats = self.extract_images(file_path, output_dir, dry_run)
        return file_path, stats
