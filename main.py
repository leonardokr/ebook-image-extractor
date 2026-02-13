#!/usr/bin/env python3
"""Command-line interface for eBook image extraction."""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional

from src.epub_extractor import EPUBImageExtractor
from src.logging_utils import configure_json_logger
from src.mobi_extractor import MobiImageExtractor


def _configure_extractor_logging(extractor, json_logs: bool) -> None:
    """Configure extractor logging.

    :param extractor: Extractor instance.
    :param json_logs: JSON logs flag.
    """
    if json_logs:
        configure_json_logger(extractor.logger)


def _build_common_extractor_kwargs(args: argparse.Namespace) -> Dict:
    """Build shared constructor kwargs.

    :param args: Parsed arguments.
    :return: Constructor options.
    """
    return {
        "min_image_size": args.min_size,
        "min_width": args.min_width,
        "min_height": args.min_height,
        "max_aspect_ratio": args.max_aspect_ratio,
        "enable_deduplication": not args.no_dedup,
        "write_manifest": args.manifest,
        "write_debug_order": args.debug_order,
        "archive_format": args.archive_format,
        "hash_cache_path": args.hash_cache,
        "parallelism": args.parallelism,
    }


def _make_extractors(args: argparse.Namespace):
    """Create requested extractors.

    :param args: Parsed arguments.
    :return: Tuple with EPUB and MOBI extractors.
    """
    kwargs = _build_common_extractor_kwargs(args)
    epub = None
    mobi = None
    if args.format in {"epub", "auto"}:
        epub = EPUBImageExtractor(**kwargs)
    if args.format in {"mobi", "auto"}:
        mobi = MobiImageExtractor(**kwargs)
    log_level = logging.DEBUG if args.verbose else logging.INFO
    for extractor in [epub, mobi]:
        if extractor:
            extractor.set_log_level(log_level)
            _configure_extractor_logging(extractor, args.json_logs)
            if args.ignore_hashes:
                for hash_value in args.ignore_hashes:
                    extractor.add_ignored_hash(hash_value)
    return epub, mobi


def _collect_files(epub, mobi, directory: str, recursive: bool):
    """Collect files by format.

    :param epub: EPUB extractor.
    :param mobi: MOBI extractor.
    :param directory: Search directory.
    :param recursive: Recursive flag.
    :return: Tuple of EPUB and MOBI files.
    """
    epub_files = epub.find_files(directory, recursive) if epub else []
    mobi_files = mobi.find_files(directory, recursive) if mobi else []
    return epub_files, mobi_files


def _print_metadata(label: str, metadata) -> None:
    """Render metadata block.

    :param label: File label.
    :param metadata: Metadata object.
    """
    print(label)
    if metadata.title:
        print(f"  Title: {metadata.title}")
    if metadata.author:
        print(f"  Author: {metadata.author}")
    if metadata.publisher:
        print(f"  Publisher: {metadata.publisher}")
    if metadata.language:
        print(f"  Language: {metadata.language}")


def run_scan(args: argparse.Namespace) -> int:
    """Execute scan command.

    :param args: Parsed arguments.
    :return: Exit code.
    """
    epub, mobi = _make_extractors(args)
    epub_files, mobi_files = _collect_files(epub, mobi, args.directory, args.recursive)
    total = len(epub_files) + len(mobi_files)
    if total == 0:
        print("No supported files found.")
        return 0
    print(f"Found {total} ebook file(s).")
    for path in epub_files:
        print(f"EPUB: {path}")
    for path in mobi_files:
        print(f"MOBI: {path}")
    return 0


def run_inspect(args: argparse.Namespace) -> int:
    """Execute inspect command.

    :param args: Parsed arguments.
    :return: Exit code.
    """
    if not os.path.isfile(args.file):
        print(f"Error: file not found: {args.file}")
        return 1
    lower = args.file.lower()
    if lower.endswith(".epub"):
        extractor = EPUBImageExtractor(write_debug_order=args.debug_order)
    elif lower.endswith((".mobi", ".azw", ".azw3")):
        extractor = MobiImageExtractor(write_debug_order=args.debug_order)
    else:
        print("Unsupported file extension.")
        return 1
    extractor.set_log_level(logging.DEBUG if args.verbose else logging.INFO)
    _configure_extractor_logging(extractor, args.json_logs)
    metadata = extractor.extract_metadata(args.file)
    _print_metadata(f"\n{os.path.basename(args.file)}:", metadata)
    stats = extractor.extract_images(args.file, os.path.join(args.temp_dir, "_inspect"), dry_run=True)
    print("\nDry-run summary:")
    print(json.dumps(stats.to_dict(), indent=2))
    return 0


def run_verify(args: argparse.Namespace) -> int:
    """Execute verify command.

    :param args: Parsed arguments.
    :return: Exit code.
    """
    epub, mobi = _make_extractors(args)
    epub_files, mobi_files = _collect_files(epub, mobi, args.directory, args.recursive)
    failures: List[str] = []
    for extractor, files in [(epub, epub_files), (mobi, mobi_files)]:
        if not extractor:
            continue
        for path in files:
            try:
                stats = extractor.extract_images(path, os.path.join(args.directory, "_verify"), dry_run=True)
                if stats.saved == 0:
                    failures.append(path)
            except Exception:
                failures.append(path)
    if failures:
        print("Verification failed for:")
        for path in failures:
            print(path)
        return 1
    print("Verification passed.")
    return 0


def run_extract(args: argparse.Namespace) -> int:
    """Execute extract command.

    :param args: Parsed arguments.
    :return: Exit code.
    """
    epub, mobi = _make_extractors(args)
    epub_files, mobi_files = _collect_files(epub, mobi, args.directory, args.recursive)
    if not epub_files and not mobi_files:
        print("No supported eBook files (EPUB, MOBI, AZW) found in the specified directory.")
        return 0

    if args.show_metadata:
        print("\n=== BOOK METADATA ===")
        for path in epub_files:
            _print_metadata(f"\n{os.path.basename(path)}:", epub.extract_metadata(path))
        for path in mobi_files:
            _print_metadata(f"\n{os.path.basename(path)}:", mobi.extract_metadata(path))
        print()

    if epub_files and epub:
        print("=== PROCESSING EPUB FILES ===")
        epub.extract_from_directory(
            args.directory,
            use_html_refs=not args.all_images,
            recursive=args.recursive,
            dry_run=args.dry_run,
        )

    if mobi_files and mobi:
        if epub_files:
            print("\n" + "=" * 50)
        print("=== PROCESSING MOBI FILES ===")
        mobi.extract_from_directory(
            args.directory,
            recursive=args.recursive,
            dry_run=args.dry_run,
        )
    return 0


def _add_common_flags(parser: argparse.ArgumentParser) -> None:
    """Add common extractor options.

    :param parser: Parser object.
    """
    parser.add_argument("--format", choices=["epub", "mobi", "auto"], default="auto")
    parser.add_argument("--recursive", "-r", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--all-images", action="store_true")
    parser.add_argument("--show-metadata", action="store_true")
    parser.add_argument("--add-ignore-hash", action="append", dest="ignore_hashes")
    parser.add_argument("--min-size", type=int, default=0)
    parser.add_argument("--min-width", type=int, default=0)
    parser.add_argument("--min-height", type=int, default=0)
    parser.add_argument("--max-aspect-ratio", type=float, default=0.0)
    parser.add_argument("--no-dedup", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--debug-order", action="store_true")
    parser.add_argument("--archive-format", choices=["cbz", "cbr", "pdf"])
    parser.add_argument("--hash-cache")
    parser.add_argument("--parallelism", type=int, default=1)
    parser.add_argument("--json-logs", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Extract images from EPUB and MOBI files")
    subparsers = parser.add_subparsers(dest="command")

    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("directory", nargs="?", default=".")
    _add_common_flags(extract_parser)

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("directory", nargs="?", default=".")
    scan_parser.add_argument("--format", choices=["epub", "mobi", "auto"], default="auto")
    scan_parser.add_argument("--recursive", "-r", action="store_true")
    scan_parser.add_argument("--verbose", "-v", action="store_true")
    scan_parser.add_argument("--json-logs", action="store_true")
    scan_parser.add_argument("--add-ignore-hash", action="append", dest="ignore_hashes")
    scan_parser.set_defaults(ignore_hashes=None)
    scan_parser.set_defaults(
        min_size=0,
        min_width=0,
        min_height=0,
        max_aspect_ratio=0.0,
        no_dedup=False,
        manifest=False,
        debug_order=False,
        archive_format=None,
        hash_cache=None,
        parallelism=1,
        dry_run=True,
        all_images=False,
        show_metadata=False,
    )

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("file")
    inspect_parser.add_argument("--temp-dir", default=".")
    inspect_parser.add_argument("--debug-order", action="store_true")
    inspect_parser.add_argument("--json-logs", action="store_true")
    inspect_parser.add_argument("--verbose", "-v", action="store_true")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("directory", nargs="?", default=".")
    _add_common_flags(verify_parser)

    args = parser.parse_args()
    if args.command is None:
        compatibility_args = ["extract"] + sys.argv[1:]
        args = parser.parse_args(compatibility_args)

    if getattr(args, "directory", None) and not os.path.isdir(args.directory):
        print(f"Error: directory '{args.directory}' not found.")
        sys.exit(1)

    try:
        if args.command == "scan":
            code = run_scan(args)
        elif args.command == "inspect":
            code = run_inspect(args)
        elif args.command == "verify":
            code = run_verify(args)
        else:
            code = run_extract(args)
        sys.exit(code)
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
