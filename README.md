# EPUB Image Extractor

🖼️ **Python tool to extract images from EPUB files with intelligent filtering and automatic organization.**

## ✨ Features

- **Smart extraction**: Detects images referenced in HTML/XHTML files
- **Hash filtering**: Automatically ignores common decorative elements
- **Automatic organization**: Creates separate directories for each EPUB
- **Multiple format support**: JPG, PNG, WebP, GIF, BMP, SVG
- **Detailed statistics**: Complete extraction reports
- **Command-line interface**: Easy to use and automate
- **Batch processing**: Processes multiple EPUBs at once

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
- beautifulsoup4 >= 4.12.0
- lxml >= 4.9.0

## 🔧 Usage

### Quick Method (Windows)

```batch
# Run the batch file for easy use
run_extractor.bat
```

### Command Line Interface

```bash
# Extract images from current directory
python main.py

# Extract from a specific directory
python main.py /path/to/epubs

# Extract ALL images (not just HTML-referenced ones)
python main.py --all-images

# Add hash to ignore list
python main.py --add-ignore-hash abc123def456

# Verbose mode
python main.py --verbose
```

### Programmatic Usage

```python
from src.epub_extractor import EPUBImageExtractor

# Create extractor
extractor = EPUBImageExtractor()

# Extract from a directory
extractor.extract_from_directory("/path/to/epubs")

# Extract from a specific file
stats = extractor.extract_images_from_epub(
    "book.epub",
    "output_folder",
    use_html_refs=True
)

# Add hash to ignore list
extractor.add_ignored_hash("unwanted_image_hash")
```

> 📖 **For more detailed usage examples, see [examples/usage_examples.py](examples/usage_examples.py)**

## 📁 Output Structure

```
source_directory/
├── book1.epub
├── book2.epub
├── book1/              # Automatically created folder
│   ├── 0000.jpg
│   ├── 0001.png
│   └── 0002.webp
└── book2/              # Automatically created folder
    ├── 0000.jpg
    └── 0001.gif
```

## 🎯 Advanced Features

### Smart Filtering

- Automatically removes common decorative elements
- SHA256 hash system for precise identification
- Configurable ignore hash list

### Image Detection

- **HTML mode** (default): Extracts only images referenced in content
- **Complete mode**: Extracts all images found in the file

### Detailed Statistics

```
=== TOTAL STATISTICS ===
EPUB files processed: 3
Total images extracted: 127
Total images ignored: 8
Total missing images: 2
```

## 🛠️ Suggested Improvements

### Proposed Features

1. **Graphical Interface (GUI)**

   - Drag & drop EPUB files
   - Image preview before extraction
   - Manual image selection

2. **Advanced Filters**

   - Filter by minimum/maximum size
   - Filter by dimensions (width/height)
   - Filter by file type

3. **Format Conversion**

   - Automatic conversion to specific formats
   - Image resizing
   - Quality optimization

4. **Better Organization**

   - Preserve original filenames
   - Organization by chapters
   - Image metadata

5. **Additional Features**
   - Preview mode (list without extracting)
   - Automatic backup
   - Detailed operation logs
   - Support for more ebook formats (MOBI, AZW)

## 📂 Project Structure

```
epub-extract-images/
├── src/
│   └── epub_extractor.py    # Main class
├── tests/                   # Unit tests
├── examples/               # Usage examples
├── main.py                 # CLI interface
├── run_extractor.bat       # Windows script (easy use)
├── setup.py               # Installation configuration
├── requirements.txt       # Dependencies
└── README.md             # This documentation
```

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📝 License

This project is under the MIT license. See the `LICENSE` file for more details.

## 🐛 Known Issues

- Some EPUBs with non-standard structure may have undetected images
- Complex SVG images may not be processed correctly
- Paths with special characters may cause issues on Windows

## 💡 Usage Tips

- Use `--all-images` if many images are not being detected
- Add hashes of unwanted decorative images with `--add-ignore-hash`
- For better performance with many files, process in smaller batches

## 📞 Support

Found a bug or have a suggestion? Open an [issue](https://github.com/your-username/epub-extract-images/issues) on GitHub!
