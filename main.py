#!/usr/bin/env python3
"""
Command-line interface for eBook Image Extractor.
"""

import argparse
import sys
import os
from src.epub_extractor import EPUBImageExtractor
from src.mobi_extractor import MobiImageExtractor


def main():
    """Main CLI function."""
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
        "--add-ignore-hash", help="Add a SHA256 hash to the ignore list"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found.")
        sys.exit(1)

    try:
        epub_files = None
        mobi_files = None

        if args.format in ["epub", "auto"]:
            epub_extractor = EPUBImageExtractor()

            if args.add_ignore_hash:
                epub_extractor.add_ignored_hash(args.add_ignore_hash)
                print(f"Hash added to EPUB ignore list: {args.add_ignore_hash}")

            epub_files = epub_extractor.find_epub_files(args.directory)
            if epub_files:
                print("=== PROCESSING EPUB FILES ===")
                epub_extractor.extract_from_directory(
                    args.directory, not args.all_images
                )
            elif args.format == "epub":
                print("No EPUB files found in the specified directory.")

        if args.format in ["mobi", "auto"]:
            mobi_extractor = MobiImageExtractor()

            if args.add_ignore_hash:
                mobi_extractor.add_ignored_hash(args.add_ignore_hash)
                print(f"Hash added to MOBI ignore list: {args.add_ignore_hash}")

            mobi_files = mobi_extractor.find_mobi_files(args.directory)
            if mobi_files:
                if args.format == "auto" and epub_files:
                    print("\n" + "=" * 50)
                print("=== PROCESSING MOBI FILES ===")
                mobi_extractor.extract_from_directory(args.directory)
            elif args.format == "mobi":
                print("No MOBI/AZW files found in the specified directory.")

        if args.format == "auto":
            epub_extractor = EPUBImageExtractor()
            mobi_extractor = MobiImageExtractor()
            epub_files = epub_extractor.find_epub_files(args.directory)
            mobi_files = mobi_extractor.find_mobi_files(args.directory)

            if not epub_files and not mobi_files:
                print(
                    "No supported eBook files (EPUB, MOBI, AZW) found in the specified directory."
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
