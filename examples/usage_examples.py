"""
Usage examples for eBook Image Extractor library (EPUB and MOBI support).
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.epub_extractor import EPUBImageExtractor
from src.mobi_extractor import MobiImageExtractor


def basic_epub_example():
    """Basic EPUB image extraction example."""
    print("=== BASIC EPUB EXAMPLE ===")

    extractor = EPUBImageExtractor()
    extractor.extract_from_directory(".")


def basic_mobi_example():
    """Basic MOBI image extraction example."""
    print("=== BASIC MOBI EXAMPLE ===")

    extractor = MobiImageExtractor()
    extractor.extract_from_directory(".")


def unified_extraction_example():
    """Example of processing both EPUB and MOBI files."""
    print("=== UNIFIED EXTRACTION EXAMPLE ===")

    epub_extractor = EPUBImageExtractor()
    mobi_extractor = MobiImageExtractor()

    directory = "."

    # Check for EPUB files
    epub_files = epub_extractor.find_epub_files(directory)
    if epub_files:
        print(f"Processing {len(epub_files)} EPUB file(s)...")
        epub_extractor.extract_from_directory(directory)

    # Check for MOBI files
    mobi_files = mobi_extractor.find_mobi_files(directory)
    if mobi_files:
        print(f"Processing {len(mobi_files)} MOBI file(s)...")
        mobi_extractor.extract_from_directory(directory)

    if not epub_files and not mobi_files:
        print("No eBook files found in the current directory.")


def advanced_epub_example():
    """Example with advanced EPUB configurations."""
    print("=== ADVANCED EPUB EXAMPLE ===")

    # Custom ignored hashes
    ignored_hashes = {
        "1fcf4c601de84ae1d66e36f93b83b33b453f77aeb345be830f1fc66439fdb50d",
        "933f630f9a34dd68d5047813ec3272b8b3634011e5ed90be50dfd765a1303263",
        "custom_epub_hash_here",
    }

    extractor = EPUBImageExtractor(ignored_hashes=ignored_hashes)

    if os.path.exists("example.epub"):
        # Extract all images (not just HTML-referenced)
        stats = extractor.extract_images_from_epub(
            "example.epub",
            "example_epub_output",
            use_html_refs=False,  # Extract all images
        )

        print("EPUB extraction statistics:")
        print(f"  Images saved: {stats['saved']}")
        print(f"  Images ignored: {stats['ignored']}")
        print(f"  Images missing: {stats['missing']}")
    else:
        print("File example.epub not found!")


def advanced_mobi_example():
    """Example with advanced MOBI configurations."""
    print("=== ADVANCED MOBI EXAMPLE ===")

    # Custom ignored hashes
    ignored_hashes = {
        "1fcf4c601de84ae1d66e36f93b83b33b453f77aeb345be830f1fc66439fdb50d",
        "933f630f9a34dd68d5047813ec3272b8b3634011e5ed90be50dfd765a1303263",
        "custom_mobi_hash_here",
    }

    extractor = MobiImageExtractor(ignored_hashes=ignored_hashes)

    # Try different MOBI extensions
    test_files = ["example.mobi", "example.azw", "example.azw3"]

    for test_file in test_files:
        if os.path.exists(test_file):
            stats = extractor.extract_images_from_mobi(
                test_file, f"{os.path.splitext(test_file)[0]}_output"
            )

            print(f"MOBI extraction statistics for {test_file}:")
            print(f"  Images saved: {stats['saved']}")
            print(f"  Images ignored: {stats['ignored']}")
            print(f"  Images missing: {stats['missing']}")
            break
    else:
        print("No MOBI files found (example.mobi, example.azw, example.azw3)!")


def hash_management_example():
    """Example of hash management for both formats."""
    print("=== HASH MANAGEMENT EXAMPLE ===")

    epub_extractor = EPUBImageExtractor()
    mobi_extractor = MobiImageExtractor()

    # Add custom hash to both extractors
    new_hash = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz567890abcdef12"

    epub_extractor.add_ignored_hash(new_hash)
    mobi_extractor.add_ignored_hash(new_hash)

    print(f"Hash added to both extractors: {new_hash}")
    print(f"EPUB ignored hashes: {len(epub_extractor.ignored_hashes)}")
    print(f"MOBI ignored hashes: {len(mobi_extractor.ignored_hashes)}")

    # Remove a hash
    epub_extractor.remove_ignored_hash(new_hash)
    mobi_extractor.remove_ignored_hash(new_hash)

    print("Hash removed from both extractors")
    print(f"EPUB ignored hashes: {len(epub_extractor.ignored_hashes)}")
    print(f"MOBI ignored hashes: {len(mobi_extractor.ignored_hashes)}")


def file_discovery_example():
    """Example of discovering eBook files."""
    print("=== FILE DISCOVERY EXAMPLE ===")

    epub_extractor = EPUBImageExtractor()
    mobi_extractor = MobiImageExtractor()

    directory = "."

    # Find all supported files
    epub_files = epub_extractor.find_epub_files(directory)
    mobi_files = mobi_extractor.find_mobi_files(directory)

    print("Found files:")
    if epub_files:
        print("  EPUB files:")
        for file in epub_files:
            print(f"    - {os.path.basename(file)}")

    if mobi_files:
        print("  MOBI/AZW files:")
        for file in mobi_files:
            print(f"    - {os.path.basename(file)}")

    if not epub_files and not mobi_files:
        print("  No supported eBook files found.")

    total_files = len(epub_files) + len(mobi_files)
    print(f"  Total: {total_files} eBook file(s)")


def batch_processing_example():
    """Example of batch processing with statistics."""
    print("=== BATCH PROCESSING EXAMPLE ===")

    epub_extractor = EPUBImageExtractor()
    mobi_extractor = MobiImageExtractor()

    directory = "."

    total_stats = {"epub": {"files": 0, "images": 0}, "mobi": {"files": 0, "images": 0}}

    # Process EPUB files
    epub_files = epub_extractor.find_epub_files(directory)
    if epub_files:
        total_stats["epub"]["files"] = len(epub_files)
        print(f"Processing {len(epub_files)} EPUB file(s)...")

        for epub_file in epub_files:
            filename = os.path.splitext(os.path.basename(epub_file))[0]
            output_dir = os.path.join(directory, filename)

            stats = epub_extractor.extract_images_from_epub(
                epub_file, output_dir, use_html_refs=True
            )
            total_stats["epub"]["images"] += stats["saved"]

    # Process MOBI files
    mobi_files = mobi_extractor.find_mobi_files(directory)
    if mobi_files:
        total_stats["mobi"]["files"] = len(mobi_files)
        print(f"Processing {len(mobi_files)} MOBI file(s)...")

        for mobi_file in mobi_files:
            filename = os.path.splitext(os.path.basename(mobi_file))[0]
            output_dir = os.path.join(directory, filename)

            stats = mobi_extractor.extract_images_from_mobi(mobi_file, output_dir)
            total_stats["mobi"]["images"] += stats["saved"]

    # Print summary
    print("\n=== BATCH PROCESSING SUMMARY ===")
    print(f"EPUB files processed: {total_stats['epub']['files']}")
    print(f"EPUB images extracted: {total_stats['epub']['images']}")
    print(f"MOBI files processed: {total_stats['mobi']['files']}")
    print(f"MOBI images extracted: {total_stats['mobi']['images']}")

    total_files = total_stats["epub"]["files"] + total_stats["mobi"]["files"]
    total_images = total_stats["epub"]["images"] + total_stats["mobi"]["images"]
    print(f"Total files: {total_files}")
    print(f"Total images: {total_images}")


def main():
    """Main function for examples."""
    print("eBook Image Extractor - Usage Examples")
    print("Supports EPUB, MOBI, AZW, and AZW3 formats\n")

    # Basic examples
    basic_epub_example()
    print()
    basic_mobi_example()
    print()

    # Unified processing
    unified_extraction_example()
    print()

    # Advanced examples
    advanced_epub_example()
    print()
    advanced_mobi_example()
    print()

    # Utility examples
    hash_management_example()
    print()
    file_discovery_example()
    print()
    batch_processing_example()


if __name__ == "__main__":
    main()
