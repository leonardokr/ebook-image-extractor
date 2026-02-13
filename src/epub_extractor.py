"""
EPUB Image Extractor

Extracts images from EPUB files with proper reading order from OPF spine.
"""

import zipfile
import os
from typing import List, Set, Dict, Optional, Tuple
import logging
from bs4 import BeautifulSoup
from bs4.element import Tag

from .base_extractor import BaseExtractor, ExtractionStats, BookMetadata
from .exceptions import InvalidFileError, ExtractionError
from .image_analysis import parse_image_metrics, classify_image


class EPUBImageExtractor(BaseExtractor):
    """
    Extracts images from EPUB files with filtering and organization capabilities.
    """

    SUPPORTED_EXTENSIONS: Set[str] = {".epub"}

    IMAGE_EXTENSIONS: Set[str] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".bmp",
        ".svg",
    }

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
        super().__init__(
            ignored_hashes=ignored_hashes,
            min_image_size=min_image_size,
            min_width=min_width,
            min_height=min_height,
            max_aspect_ratio=max_aspect_ratio,
            enable_deduplication=enable_deduplication,
            logger=logger,
            show_progress=show_progress,
            write_manifest=write_manifest,
            write_debug_order=write_debug_order,
            archive_format=archive_format,
            hash_cache_path=hash_cache_path,
            parallelism=parallelism,
        )

    def find_files(self, directory: str, recursive: bool = False) -> List[str]:
        epub_files = []
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(".epub"):
                        epub_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                if file.lower().endswith(".epub"):
                    epub_files.append(os.path.join(directory, file))
        return sorted(epub_files)

    def find_epub_files(self, directory: str) -> List[str]:
        return self.find_files(directory, recursive=False)

    def normalize_path(self, base_path: str, relative_path: str) -> str:
        base_dir = os.path.dirname(base_path)
        return os.path.normpath(os.path.join(base_dir, relative_path)).replace("\\", "/")

    def get_reading_order(
        self, zipf: zipfile.ZipFile, all_files: List[str]
    ) -> List[str]:
        try:
            opf_files = [f for f in all_files if f.endswith(".opf")]

            container_opf = None
            try:
                with zipf.open("META-INF/container.xml") as f:
                    container_soup = BeautifulSoup(f.read(), "xml")
                    rootfile = container_soup.find("rootfile")
                    if rootfile and isinstance(rootfile, Tag):
                        container_opf = rootfile.get("full-path")
            except Exception:
                pass

            opf_path = (
                container_opf
                if container_opf
                else (opf_files[0] if opf_files else None)
            )

            if opf_path:
                with zipf.open(str(opf_path)) as f:
                    opf_soup = BeautifulSoup(f.read(), "xml")

                manifest = opf_soup.find("manifest")
                id_to_href = {}
                if manifest and isinstance(manifest, Tag):
                    for item in manifest.find_all("item"):
                        if isinstance(item, Tag):
                            item_id = item.get("id")
                            item_href = item.get("href")
                            if item_id and item_href:
                                id_to_href[str(item_id)] = str(item_href)

                spine = opf_soup.find("spine")
                ordered_files = []
                if spine and isinstance(spine, Tag):
                    opf_dir = os.path.dirname(str(opf_path))
                    for itemref in spine.find_all("itemref"):
                        if isinstance(itemref, Tag):
                            idref = itemref.get("idref")
                            if idref and str(idref) in id_to_href:
                                href = id_to_href[str(idref)]
                                if opf_dir and opf_dir != ".":
                                    full_path = f"{opf_dir}/{href}".replace("//", "/")
                                else:
                                    full_path = href

                                if full_path in all_files and full_path.endswith(
                                    (".xhtml", ".html")
                                ):
                                    ordered_files.append(full_path)

                html_files = [f for f in all_files if f.endswith((".xhtml", ".html"))]
                for html_file in html_files:
                    if html_file not in ordered_files:
                        ordered_files.append(html_file)

                if ordered_files:
                    return ordered_files

        except Exception as e:
            self.logger.warning(f"Could not read reading order from OPF: {e}")

        html_files = [f for f in all_files if f.endswith((".xhtml", ".html"))]
        return sorted(html_files)

    def extract_image_references(
        self, zipf: zipfile.ZipFile, all_files: List[str]
    ) -> Tuple[List[str], List[str]]:
        html_files = self.get_reading_order(zipf, all_files)
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
                                if resolved in all_files and resolved not in image_paths:
                                    image_paths.append(resolved)
                                elif resolved not in all_files:
                                    missing_images.append(resolved)
            except Exception as e:
                self.logger.warning(f"Error processing {html_file}: {e}")

        return image_paths, missing_images

    def extract_metadata(self, file_path: str) -> BookMetadata:
        metadata = BookMetadata()

        try:
            with zipfile.ZipFile(file_path, "r") as zipf:
                all_files = zipf.namelist()
                opf_files = [f for f in all_files if f.endswith(".opf")]

                opf_path = None
                try:
                    with zipf.open("META-INF/container.xml") as f:
                        container_soup = BeautifulSoup(f.read(), "xml")
                        rootfile = container_soup.find("rootfile")
                        if rootfile and isinstance(rootfile, Tag):
                            opf_path = rootfile.get("full-path")
                except Exception:
                    pass

                if not opf_path and opf_files:
                    opf_path = opf_files[0]

                if opf_path:
                    with zipf.open(str(opf_path)) as f:
                        opf_soup = BeautifulSoup(f.read(), "xml")

                    title_tag = opf_soup.find("dc:title")
                    if title_tag:
                        metadata.title = title_tag.get_text()

                    creator_tag = opf_soup.find("dc:creator")
                    if creator_tag:
                        metadata.author = creator_tag.get_text()

                    publisher_tag = opf_soup.find("dc:publisher")
                    if publisher_tag:
                        metadata.publisher = publisher_tag.get_text()

                    language_tag = opf_soup.find("dc:language")
                    if language_tag:
                        metadata.language = language_tag.get_text()

                    manifest = opf_soup.find("manifest")
                    if manifest and isinstance(manifest, Tag):
                        for item in manifest.find_all("item"):
                            if isinstance(item, Tag):
                                properties = item.get("properties", "")
                                if "cover-image" in str(properties):
                                    href = item.get("href")
                                    if href:
                                        opf_dir = os.path.dirname(str(opf_path))
                                        if opf_dir:
                                            cover_path = f"{opf_dir}/{href}".replace("//", "/")
                                        else:
                                            cover_path = str(href)
                                        try:
                                            metadata.cover_image = zipf.read(cover_path)
                                        except Exception:
                                            pass
                                    break

        except Exception as e:
            self.logger.warning(f"Could not extract metadata from {file_path}: {e}")

        return metadata

    def extract_images(
        self, file_path: str, output_dir: str, dry_run: bool = False, use_html_refs: bool = True
    ) -> ExtractionStats:
        stats = ExtractionStats()
        manifest = None
        debug_order = {
            "mode": "epub",
            "use_html_refs": use_html_refs,
            "ordered_html_files": [],
            "image_references": [],
            "saved_mappings": [],
        }

        try:
            with zipfile.ZipFile(file_path, "r") as zipf:
                all_files = zipf.namelist()
                if not dry_run and (self.write_manifest or self.write_debug_order or self.archive_format):
                    manifest = self.build_manifest(file_path, output_dir)

                if use_html_refs:
                    debug_order["ordered_html_files"] = self.get_reading_order(zipf, all_files)
                    image_paths, missing_images = self.extract_image_references(zipf, all_files)
                    debug_order["image_references"] = image_paths.copy()
                    if not image_paths:
                        image_paths = [
                            f for f in all_files
                            if os.path.splitext(f)[1].lower() in self.IMAGE_EXTENSIONS
                        ]
                        self.logger.info(
                            f"No valid HTML images found. Using {len(image_paths)} images from ZIP."
                        )
                    else:
                        self.logger.info(f"{len(image_paths)} image(s) found via HTML.")
                else:
                    image_paths = [
                        f for f in all_files
                        if os.path.splitext(f)[1].lower() in self.IMAGE_EXTENSIONS
                    ]
                    missing_images = []
                    self.logger.info(f"Extracting all {len(image_paths)} images found in ZIP.")

                if dry_run:
                    for img_path in image_paths:
                        try:
                            img_data = zipf.read(img_path)
                            metrics = parse_image_metrics(img_data)
                            img_hash = self.hash_bytes_sha256(img_data)
                            should_skip, reason = self.should_skip_image(img_data, img_hash, metrics)
                            if not should_skip:
                                stats.saved += 1
                            elif reason == "ignored_hash":
                                stats.ignored += 1
                            elif reason in {"duplicate", "duplicate_cache"}:
                                stats.duplicates += 1
                            elif reason == "too_small":
                                stats.filtered_by_size += 1
                            elif reason in {"too_narrow", "too_short"}:
                                stats.filtered_by_dimensions += 1
                            elif reason == "extreme_aspect_ratio":
                                stats.filtered_by_aspect_ratio += 1
                        except Exception:
                            stats.missing += 1
                    return stats

                self.prepare_output_directory(output_dir)

                for img_path in image_paths:
                    try:
                        img_data = zipf.read(img_path)
                        metrics = parse_image_metrics(img_data)
                        img_hash = self.hash_bytes_sha256(img_data)
                        should_skip, reason = self.should_skip_image(img_data, img_hash, metrics)

                        if should_skip:
                            if reason == "ignored_hash":
                                stats.ignored += 1
                            elif reason in {"duplicate", "duplicate_cache"}:
                                stats.duplicates += 1
                            elif reason == "too_small":
                                stats.filtered_by_size += 1
                            elif reason in {"too_narrow", "too_short"}:
                                stats.filtered_by_dimensions += 1
                            elif reason == "extreme_aspect_ratio":
                                stats.filtered_by_aspect_ratio += 1
                            continue

                        ext = os.path.splitext(img_path)[1].lower()
                        classification = classify_image(metrics, is_cover=("cover" in img_path.lower()))
                        output_path = self.save_image(
                            img_data,
                            output_dir,
                            stats.saved,
                            ext,
                            classification=classification,
                        )
                        if manifest:
                            self.add_manifest_item(
                                manifest=manifest,
                                index=stats.saved,
                                filename=os.path.basename(output_path),
                                source_ref=img_path,
                                image_hash=img_hash,
                                metrics=metrics,
                                classification=classification,
                            )
                        debug_order["saved_mappings"].append(
                            {
                                "source_ref": img_path,
                                "output_index": stats.saved,
                                "output_file": os.path.basename(output_path),
                            }
                        )
                        stats.saved += 1

                    except Exception:
                        missing_images.append(img_path)

                stats.missing = len(set(missing_images))
                self.finalize_book_output(output_dir, manifest, debug_order)

        except zipfile.BadZipFile:
            raise InvalidFileError(file_path, "EPUB", "Invalid or corrupted ZIP file")
        except Exception as e:
            raise ExtractionError(file_path, str(e))

        return stats

    def extract_images_from_epub(
        self, epub_path: str, output_dir: str, use_html_refs: bool = True
    ) -> Dict[str, int]:
        stats = self.extract_images(epub_path, output_dir, dry_run=False, use_html_refs=use_html_refs)
        return stats.to_dict()

    def extract_from_directory(
        self,
        directory: str,
        use_html_refs: bool = True,
        recursive: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, ExtractionStats]:
        files = self.find_files(directory, recursive)

        if not files:
            self.logger.info("No EPUB files found.")
            return {}

        self.logger.info(f"{len(files)} EPUB file(s) found")
        for f in files:
            self.logger.info(f"  - {os.path.basename(f)}")

        results: Dict[str, ExtractionStats] = {}
        total_stats = ExtractionStats()

        for file_path in files:
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = os.path.join(directory, file_name)

            self.logger.info(f"Processing: {os.path.basename(file_path)}")

            if dry_run:
                print(f"[DRY RUN] Would extract to: {output_dir}")

            self.reset_extraction_state()

            stats = self.extract_images(file_path, output_dir, dry_run, use_html_refs)
            results[file_path] = stats

            total_stats.saved += stats.saved
            total_stats.ignored += stats.ignored
            total_stats.missing += stats.missing
            total_stats.duplicates += stats.duplicates
            total_stats.filtered_by_size += stats.filtered_by_size

            self.print_stats(stats, prefix="  ")
            print(f"  Extraction completed for: {output_dir}")

        print(f"\n=== TOTAL STATISTICS ===")
        print(f"EPUB files processed: {len(files)}")
        self.print_stats(total_stats)

        return results


def main():
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
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Search for EPUB files recursively",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be extracted without extracting",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=0,
        help="Minimum image size in bytes to extract",
    )

    args = parser.parse_args()

    extractor = EPUBImageExtractor(min_image_size=args.min_size)

    if args.add_ignore_hash:
        extractor.add_ignored_hash(args.add_ignore_hash)
        print(f"Hash added to ignore list: {args.add_ignore_hash}")

    extractor.extract_from_directory(
        args.directory,
        use_html_refs=not args.all_images,
        recursive=args.recursive,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
