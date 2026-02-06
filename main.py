#!/usr/bin/env python3
"""
Command-line interface for eBook Image Extractor.
"""

import argparse
import sys
import os
import logging
from src.epub_extractor import EPUBImageExtractor
from src.mobi_extractor import MobiImageExtractor


def main():
    parser = argparse.ArgumentParser(
        description="Extract images from EPUB and MOBI files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Extract from current directory (auto-detect formats)
  %(prog)s /path/to/ebook/files      # Extract from specific directory
  %(prog)s --format epub             # Extract only from EPUB files
  %(prog)s --format mobi             # Extract only from MOBI/AZW files
  %(prog)s --all-images              # Extract all images, not just HTML-referenced (EPUB only)
  %(prog)s --add-ignore-hash abc123  # Add hash to ignore list
  %(prog)s --recursive               # Search subdirectories for ebooks
  %(prog)s --dry-run                 # Show what would be extracted without extracting
  %(prog)s --min-size 5000           # Only extract images larger than 5KB
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing eBook files (default: current directory)",
    )

    parser.add_argument(
        "--format",
        choices=["epub", "mobi", "auto"],
        default="auto",
        help="File format to process (default: auto-detect both)",
    )

    parser.add_argument(
        "--all-images",
        action="store_true",
        help="Extract all images, not just those referenced in HTML (EPUB only)",
    )

    parser.add_argument(
        "--add-ignore-hash",
        action="append",
        dest="ignore_hashes",
        help="Add a SHA256 hash to the ignore list (can be used multiple times)",
    )

    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Search for ebook files recursively in subdirectories",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be extracted without actually extracting",
    )

    parser.add_argument(
        "--min-size",
        type=int,
        default=0,
        help="Minimum image size in bytes to extract (filters small icons)",
    )

    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable duplicate image detection",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--show-metadata",
        action="store_true",
        help="Show book metadata before extraction",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found.")
        sys.exit(1)

    log_level = logging.DEBUG if args.verbose else logging.INFO

    try:
        epub_extractor = None
        mobi_extractor = None

        if args.format in ["epub", "auto"]:
            epub_extractor = EPUBImageExtractor(
                min_image_size=args.min_size,
                enable_deduplication=not args.no_dedup,
            )
            epub_extractor.set_log_level(log_level)

            if args.ignore_hashes:
                for hash_value in args.ignore_hashes:
                    epub_extractor.add_ignored_hash(hash_value)
                    print(f"Hash added to EPUB ignore list: {hash_value}")

        if args.format in ["mobi", "auto"]:
            mobi_extractor = MobiImageExtractor(
                min_image_size=args.min_size,
                enable_deduplication=not args.no_dedup,
            )
            mobi_extractor.set_log_level(log_level)

            if args.ignore_hashes:
                for hash_value in args.ignore_hashes:
                    mobi_extractor.add_ignored_hash(hash_value)
                    print(f"Hash added to MOBI ignore list: {hash_value}")

        epub_files = []
        mobi_files = []

        if epub_extractor:
            epub_files = epub_extractor.find_files(args.directory, args.recursive)

        if mobi_extractor:
            mobi_files = mobi_extractor.find_files(args.directory, args.recursive)

        if not epub_files and not mobi_files:
            print("No supported eBook files (EPUB, MOBI, AZW) found in the specified directory.")
            sys.exit(0)

        if args.show_metadata:
            print("\n=== BOOK METADATA ===")
            for epub_file in epub_files:
                metadata = epub_extractor.extract_metadata(epub_file)
                print(f"\n{os.path.basename(epub_file)}:")
                if metadata.title:
                    print(f"  Title: {metadata.title}")
                if metadata.author:
                    print(f"  Author: {metadata.author}")
                if metadata.publisher:
                    print(f"  Publisher: {metadata.publisher}")
                if metadata.language:
                    print(f"  Language: {metadata.language}")

            for mobi_file in mobi_files:
                metadata = mobi_extractor.extract_metadata(mobi_file)
                print(f"\n{os.path.basename(mobi_file)}:")
                if metadata.title:
                    print(f"  Title: {metadata.title}")
                if metadata.author:
                    print(f"  Author: {metadata.author}")
                if metadata.publisher:
                    print(f"  Publisher: {metadata.publisher}")
            print()

        if epub_files and epub_extractor:
            print("=== PROCESSING EPUB FILES ===")
            epub_extractor.extract_from_directory(
                args.directory,
                use_html_refs=not args.all_images,
                recursive=args.recursive,
                dry_run=args.dry_run,
            )

        if mobi_files and mobi_extractor:
            if epub_files:
                print("\n" + "=" * 50)
            print("=== PROCESSING MOBI FILES ===")
            mobi_extractor.extract_from_directory(
                args.directory,
                recursive=args.recursive,
                dry_run=args.dry_run,
            )

    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during extraction: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
