# eBook Image Extractor

Python tool to extract images from eBook files (EPUB and MOBI/AZW) with intelligent filtering and automatic organization.

## Features

- **Multi-format support**: EPUB, MOBI, AZW, and AZW3 files
- **Smart extraction**: Respects reading order from OPF spine (EPUB) and MOBI header
- **Metadata extraction**: Extracts title, author, publisher, and cover image
- **Hash filtering**: Automatically ignores common decorative elements using SHA256
- **Image deduplication**: Skips duplicate images within each ebook
- **Size filtering**: Filter out small images (icons, decorations)
- **Automatic organization**: Creates separate directories for each eBook
- **Multiple image formats**: JPG, PNG, WebP, GIF, BMP, SVG (EPUB only)
- **Progress bars**: Visual progress indication with tqdm
- **Dry-run mode**: Preview what would be extracted without extracting
- **Recursive search**: Find ebooks in subdirectories
- **Detailed statistics**: Complete extraction reports

## Installation

### Method 1: Direct installation

```bash
pip install -r requirements.txt
```

### Method 2: Package installation

```bash
pip install -e .
```

## Requirements

- Python 3.8 or higher
- beautifulsoup4 >= 4.12.0
- lxml >= 4.9.0
- tqdm >= 4.65.0 (optional, for progress bars)

## Usage

### Command Line Interface

```bash
# Auto-detect and extract from both EPUB and MOBI files
ebook-extract

# Extract from a specific directory
ebook-extract /path/to/ebooks

# Extract only EPUB files
ebook-extract --format epub

# Extract only MOBI/AZW files
ebook-extract --format mobi

# Extract ALL images from EPUB (not just HTML-referenced ones)
ebook-extract --all-images

# Search subdirectories recursively
ebook-extract --recursive

# Preview what would be extracted (dry-run)
ebook-extract --dry-run

# Filter small images (e.g., icons smaller than 5KB)
ebook-extract --min-size 5000

# Show book metadata before extraction
ebook-extract --show-metadata

# Disable duplicate detection
ebook-extract --no-dedup

# Add hash to ignore list (can be used multiple times)
ebook-extract --add-ignore-hash abc123 --add-ignore-hash def456

# Verbose mode
ebook-extract --verbose
```

### Programmatic Usage

```python
from src import EPUBImageExtractor, MobiImageExtractor

# EPUB extraction with options
epub_extractor = EPUBImageExtractor(
    min_image_size=1024,        # Skip images smaller than 1KB
    enable_deduplication=True,  # Skip duplicate images
    show_progress=True,         # Show progress bar
)
epub_extractor.extract_from_directory("/path/to/epubs", recursive=True)

# MOBI extraction
mobi_extractor = MobiImageExtractor()
mobi_extractor.extract_from_directory("/path/to/mobis")

# Single file extraction
stats = epub_extractor.extract_images("book.epub", "output_folder")
print(f"Extracted: {stats.saved}, Ignored: {stats.ignored}")

# Extract metadata
metadata = epub_extractor.extract_metadata("book.epub")
print(f"Title: {metadata.title}")
print(f"Author: {metadata.author}")

# Dry-run mode
stats = epub_extractor.extract_images("book.epub", "output", dry_run=True)
print(f"Would extract: {stats.saved} images")

# Add/remove hashes from ignore list
epub_extractor.add_ignored_hash("unwanted_image_hash")
epub_extractor.remove_ignored_hash("wanted_image_hash")
```

### Using Custom Exceptions

```python
from src import EPUBImageExtractor, InvalidFileError, ExtractionError

extractor = EPUBImageExtractor()

try:
    extractor.extract_images("corrupted.epub", "output")
except InvalidFileError as e:
    print(f"Invalid file: {e.filepath}")
except ExtractionError as e:
    print(f"Extraction failed: {e.reason}")
```

## Output Structure

```
source_directory/
├── manga1.epub
├── manga2.mobi
├── comic.azw3
├── manga1/              # EPUB extraction
│   ├── 0000.jpg
│   ├── 0001.png
│   └── 0002.webp
├── manga2/              # MOBI extraction
│   ├── 0000.jpg
│   ├── 0001.jpg
│   └── 0002.jpg
└── comic/               # AZW3 extraction
    ├── 0000.png
    └── 0001.png
```

## Format-Specific Features

### EPUB Processing

- **HTML mode** (default): Extracts only images referenced in content files
- **Complete mode** (`--all-images`): Extracts all images found in the ZIP archive
- **Reading order**: Respects OPF spine for correct image sequence
- **SVG support**: Preserves vector graphics
- **Metadata**: Extracts title, author, publisher, language, cover image

### MOBI/AZW Processing

- **Header parsing**: Reads MOBI header for correct first_image_index
- **EXTH parsing**: Extracts metadata from EXTH header
- **Binary extraction**: Reads PDB (Palm Database) record structure
- **Magic byte detection**: Identifies images by file signatures
- **Cover detection**: Identifies cover image from EXTH cover_offset

## Advanced Statistics

```
=== PROCESSING EPUB FILES ===
Extracting: 100%|####################| 3/3 [00:05<00:00,  1.67s/file]

=== TOTAL STATISTICS ===
Files processed: 3
Total images extracted: 145
8 image(s) ignored by hash.
3 duplicate image(s) skipped.
2 image(s) filtered by size.
No missing images.
```

## Technical Details

### How It Works

#### EPUB Files

1. Opens EPUB as ZIP archive
2. Reads `META-INF/container.xml` to locate OPF file
3. Parses OPF manifest and spine for reading order
4. Extracts image references from HTML files in order
5. Filters by hash, size, and deduplication
6. Saves images with sequential naming

#### MOBI Files

1. Validates BOOKMOBI signature
2. Reads PDB header for record locations
3. Parses MOBI header to find `first_image_index`
4. Reads EXTH header for metadata and cover offset
5. Extracts images starting from first_image_index
6. Identifies images using magic bytes

### Supported Formats

| Input Format | Extension | Description                       |
| ------------ | --------- | --------------------------------- |
| EPUB         | `.epub`   | Standard eBook format (ZIP-based) |
| MOBI         | `.mobi`   | Amazon Kindle format (PDB-based)  |
| AZW          | `.azw`    | Amazon Kindle format              |
| AZW3         | `.azw3`   | Amazon Kindle format (KF8)        |

| Output Format | Extensions      | Support      |
| ------------- | --------------- | ------------ |
| JPEG          | `.jpg`, `.jpeg` | Both formats |
| PNG           | `.png`          | Both formats |
| GIF           | `.gif`          | Both formats |
| BMP           | `.bmp`          | Both formats |
| WebP          | `.webp`         | Both formats |
| SVG           | `.svg`          | EPUB only    |

## Project Structure

```
ebook-image-extractor/
├── src/
│   ├── __init__.py          # Package exports
│   ├── base_extractor.py    # Base class with common functionality
│   ├── epub_extractor.py    # EPUB extraction logic
│   ├── mobi_extractor.py    # MOBI extraction logic
│   └── exceptions.py        # Custom exceptions
├── tests/
│   └── test_extractors.py   # Test suite
├── main.py                  # CLI interface
├── setup.py                 # Package configuration
├── requirements.txt         # Python dependencies
└── README.md                # Documentation
```

## Known Issues

### EPUB-specific

- Some EPUBs with non-standard structure may have undetected images
- Complex SVG images may not be processed correctly

### MOBI-specific

- DRM-protected files cannot be processed
- Some older MOBI formats may not extract images in correct order
- KF8 (AZW3) files with complex structures may have limited support

### General

- Large files may consume significant memory during processing

## Changelog

### Version 3.0.0

- Added base extractor class for code reuse
- Added proper MOBI header parsing for correct image order
- Added metadata extraction (title, author, cover)
- Added image deduplication
- Added size-based filtering
- Added progress bars with tqdm
- Added dry-run mode
- Added recursive directory search
- Added custom exceptions
- Added logging support
- Fixed MOBI image extraction order

### Version 2.0.0

- Added MOBI, AZW, AZW3 support
- Unified command-line interface
- Enhanced error handling

### Version 1.0.0

- Initial EPUB support
- Hash-based image filtering
- Batch processing capabilities

## License

This project is under the MIT license.
