"""
Usage examples for EPUB Image Extractor library.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.epub_extractor import EPUBImageExtractor


def basic_example():
    """Basic image extraction example."""
    print("=== BASIC EXAMPLE ===")
    
    extractor = EPUBImageExtractor()
    
    extractor.extract_from_directory(".")


def advanced_example():
    """Example with advanced configurations."""
    print("=== ADVANCED EXAMPLE ===")
    
    ignored_hashes = {
        "1fcf4c601de84ae1d66e36f93b83b33b453f77aeb345be830f1fc66439fdb50d",
        "933f630f9a34dd68d5047813ec3272b8b3634011e5ed90be50dfd765a1303263",
        "custom_hash_here"
    }
    
    extractor = EPUBImageExtractor(ignored_hashes=ignored_hashes)
    
    if os.path.exists("example.epub"):
        stats = extractor.extract_images_from_epub(
            "example.epub",
            "example_output_folder",
            use_html_refs=False
        )
        
        print("Extraction statistics:")
        print(f"  Images saved: {stats['saved']}")
        print(f"  Images ignored: {stats['ignored']}")
        print(f"  Images missing: {stats['missing']}")
    else:
        print("File example.epub not found!")


def add_hash_example():
    """Example of how to add hash to ignore list."""
    print("=== ADD HASH EXAMPLE ===")
    
    extractor = EPUBImageExtractor()
    
    new_hash = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz567890abcdef12"
    extractor.add_ignored_hash(new_hash)
    
    print(f"Hash added: {new_hash}")
    print(f"Total ignored hashes: {len(extractor.ignored_hashes)}")


def main():
    """Main function for examples."""
    print("EPUB Image Extractor - Usage Examples\n")
    
    basic_example()
    print()
    advanced_example()
    print()
    add_hash_example()


if __name__ == "__main__":
    main()
