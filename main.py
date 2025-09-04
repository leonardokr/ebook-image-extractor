#!/usr/bin/env python3
"""
Command-line interface for EPUB Image Extractor.
"""

import argparse
import sys
import os
from src.epub_extractor import EPUBImageExtractor


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Extract images from EPUB files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Extract from current directory
  %(prog)s /path/to/epub/files       # Extract from specific directory
  %(prog)s --all-images              # Extract all images, not just HTML-referenced
  %(prog)s --add-ignore-hash abc123  # Add hash to ignore list
        """
    )
    
    parser.add_argument(
        "directory", 
        nargs="?", 
        default=".", 
        help="Directory containing EPUB files (default: current directory)"
    )
    
    parser.add_argument(
        "--all-images", 
        action="store_true",
        help="Extract all images, not just those referenced in HTML"
    )
    
    parser.add_argument(
        "--add-ignore-hash", 
        help="Add a SHA256 hash to the ignore list"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found.")
        sys.exit(1)
    
    extractor = EPUBImageExtractor()
    
    if args.add_ignore_hash:
        extractor.add_ignored_hash(args.add_ignore_hash)
        print(f"Hash added to ignore list: {args.add_ignore_hash}")
    
    try:
        extractor.extract_from_directory(args.directory, not args.all_images)
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
