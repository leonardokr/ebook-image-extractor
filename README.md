# eBook Image Extractor

🖼️ **Python tool to extract images from eBook files (EPUB and MOBI/AZW) with intelligent filtering and automatic organization.**

## ✨ Features

- **Multi-format support**: EPUB, MOBI, AZW, and AZW3 files
- **Smart extraction**: Detects images referenced in HTML/XHTML files (EPUB) or embedded in binary records (MOBI)
- **Hash filtering**: Automatically ignores common decorative elements using SHA256
- **Automatic organization**: Creates separate directories for each eBook
- **Multiple image formats**: JPG, PNG, WebP, GIF, BMP, SVG (EPUB only)
- **Detailed statistics**: Complete extraction reports for both formats
- **Unified interface**: Single tool for both EPUB and MOBI processing
- **Batch processing**: Processes multiple eBooks at once with format auto-detection

## 🚀 Installation

### Method 1: Direct installation

```bash
pip install -r requirements.txt
```

### Method 2: Package installation

```bash
pip install -e .
```

## 📋 Requirements

- Python 3.8 or higher
- beautifulsoup4 >= 4.12.0 (for EPUB HTML parsing)
- Standard library modules for MOBI processing (struct, hashlib)

## 🔧 Usage

### Quick Method (Windows)

```batch
# Run the batch file for easy use
extract_images.bat
```

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

# Add hash to ignore list
ebook-extract --add-ignore-hash abc123def456

# Verbose mode
ebook-extract --verbose
```

### Programmatic Usage

```python
from src.epub_extractor import EPUBImageExtractor
from src.mobi_extractor import MobiImageExtractor

# EPUB extraction
epub_extractor = EPUBImageExtractor()
epub_extractor.extract_from_directory("/path/to/epubs")

# MOBI extraction
mobi_extractor = MobiImageExtractor()
mobi_extractor.extract_from_directory("/path/to/mobis")

# Single file extraction
epub_stats = epub_extractor.extract_images_from_epub("book.epub", "output_folder")
mobi_stats = mobi_extractor.extract_images_from_mobi("book.mobi", "output_folder")

# Add hash to ignore list (both formats)
epub_extractor.add_ignored_hash("unwanted_image_hash")
mobi_extractor.add_ignored_hash("unwanted_image_hash")
```

> 📖 **For more detailed usage examples, see [usage_examples.py](usage_examples.py)**

## 📁 Output Structure

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

## 🎯 Format-Specific Features

### EPUB Processing

- **HTML mode** (default): Extracts only images referenced in content files
- **Complete mode** (`--all-images`): Extracts all images found in the ZIP archive
- **SVG support**: Preserves vector graphics
- **Path resolution**: Handles complex relative paths in EPUB structure

### MOBI/AZW Processing

- **Binary extraction**: Reads PDB (Palm Database) record structure
- **Magic byte detection**: Identifies images by file signatures
- **Multiple formats**: Supports .mobi, .azw, .azw3 files
- **Direct access**: Extracts images without intermediate parsing

## 📊 Advanced Statistics

```
=== PROCESSING EPUB FILES ===
3 EPUB file(s) found:
  - manga_volume_1.epub
  - manga_volume_2.epub
  - comic_book.epub

Processing: manga_volume_1.epub
  Total images extracted: 45
  8 image(s) ignored by hash.

==================================================
=== PROCESSING MOBI FILES ===
2 MOBI file(s) found:
  - light_novel.mobi
  - manga_digital.azw3

Processing: light_novel.mobi
  Total images extracted: 23
  2 image(s) ignored by hash.

=== TOTAL STATISTICS ===
EPUB files processed: 3
MOBI files processed: 2
Total images extracted: 195
Total images ignored: 15
Total missing images: 1
```

## 🛠️ Technical Details

### How It Works

#### EPUB Files

1. Opens EPUB as ZIP archive
2. Parses HTML/XHTML files using BeautifulSoup
3. Extracts image references from `<img>` tags
4. Resolves relative paths within EPUB structure
5. Filters duplicates using SHA256 hashes

#### MOBI Files

1. Reads PDB header to locate record offsets
2. Scans each binary record for image data
3. Identifies images using magic bytes:
   - JPEG: `\xff\xd8\xff`
   - PNG: `\x89PNG\r\n\x1a\n`
   - GIF: `GIF87a` or `GIF89a`
   - BMP: `BM`
   - WebP: `WEBP` at offset 8
4. Extracts and saves images with sequential naming

### Supported Formats

| Input Format | Extension | Description                       |
| ------------ | --------- | --------------------------------- |
| EPUB         | `.epub`   | Standard eBook format (ZIP-based) |
| MOBI         | `.mobi`   | Amazon Kindle format (PDB-based)  |
| AZW          | `.azw`    | Amazon Kindle format              |
| AZW3         | `.azw3`   | Amazon Kindle format (newer)      |

| Output Format | Extensions      | Support      |
| ------------- | --------------- | ------------ |
| JPEG          | `.jpg`, `.jpeg` | Both formats |
| PNG           | `.png`          | Both formats |
| GIF           | `.gif`          | Both formats |
| BMP           | `.bmp`          | Both formats |
| WebP          | `.webp`         | Both formats |
| SVG           | `.svg`          | EPUB only    |

## 🛠️ Future Improvements

### Proposed Features

1. **Enhanced MOBI Support**

   - DRM removal capabilities
   - Better metadata extraction
   - Chapter-based organization

2. **Graphical Interface (GUI)**

   - Drag & drop eBook files
   - Image preview before extraction
   - Format selection and filtering

3. **Advanced Processing**

   - Image deduplication across files
   - Automatic format conversion
   - Size and quality optimization
   - Batch renaming options

4. **Additional Formats**

   - PDF image extraction
   - CBR/CBZ comic support
   - FB2 format support

5. **Cloud Integration**
   - Direct extraction from cloud storage
   - Automatic backup to cloud services

## 📂 Project Structure

```
ebook-extract-images/
├── src/
│   ├── epub_extractor.py    # EPUB extraction logic
│   └── mobi_extractor.py    # MOBI extraction logic
├── tests/
│   └── test_extractors.py   # Comprehensive test suite
├── main.py                  # Unified CLI interface
├── usage_examples.py        # Detailed usage examples
├── extract_images.bat       # Windows batch script
├── setup.py                # Package configuration
├── requirements.txt        # Python dependencies
└── README.md              # This documentation
```

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/mobi-improvements`)
3. Commit your changes (`git commit -am 'Add MOBI DRM support'`)
4. Push to the branch (`git push origin feature/mobi-improvements`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/ebook-extract-images.git
cd ebook-extract-images

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_extractors.py

# Test CLI
python main.py --help
```

## 📝 License

This project is under the MIT license. See the `LICENSE` file for more details.

## 🐛 Known Issues

### EPUB-specific

- Some EPUBs with non-standard structure may have undetected images
- Complex SVG images may not be processed correctly
- Paths with special characters may cause issues on Windows

### MOBI-specific

- DRM-protected files cannot be processed
- Some AZW3 files with complex structures may not extract all images
- Very old MOBI formats (PalmDOC) have limited support

### General

- Large files may consume significant memory during processing
- Network-mounted drives may have slower extraction speeds

## 💡 Usage Tips

### For EPUB Files

- Use `--all-images` if many images are not being detected in HTML mode
- Check for images in unusual locations within the EPUB structure
- Some comics/manga may store images outside standard directories

### For MOBI Files

- MOBI extraction works best with newer format files
- If extraction fails, try converting MOBI to EPUB first using Calibre
- Sequential manga pages are typically extracted in correct order

### General Tips

- Add hashes of unwanted decorative images with `--add-ignore-hash`
- For better performance with many files, process in smaller batches
- Use `--verbose` flag for detailed debugging information

## 📞 Support

- **Bug reports**: Open an [issue](https://github.com/your-username/ebook-extract-images/issues) on GitHub
- **Feature requests**: Use GitHub discussions
- **Questions**: Check existing issues or create a new one

## 🏆 Acknowledgments

- BeautifulSoup team for excellent HTML parsing
- Amazon for MOBI format documentation
- Open-source community for testing and feedback

## 📈 Changelog

### Version 2.0.0

- ✅ Added MOBI, AZW, AZW3 support
- ✅ Unified command-line interface
- ✅ Enhanced error handling and reporting
- ✅ Comprehensive test suite
- ✅ Improved Windows batch script

### Version 1.0.0

- ✅ Initial EPUB support
- ✅ Hash-based image filtering
- ✅ Batch processing capabilities
- ✅ Command-line interface
