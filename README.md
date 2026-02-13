# eBook Image Extractor

Extract images from `EPUB`, `MOBI`, `AZW`, and `AZW3` with reading-order support, filtering, manifest output, and comic archive export.

## Highlights

- Reading-order-aware extraction for EPUB and MOBI
- Image role classification (`cover`, `page`, `thumbnail`, `decoration`)
- Filtering by size, width, height, and aspect ratio
- Incremental deduplication with persistent hash cache
- Optional `manifest.json` and `debug-order` output
- Export formats: `CBZ`, `CBR`, and `PDF` (PDF requires Pillow)
- Parallel extraction by file
- Subcommand-based CLI: `scan`, `extract`, `inspect`, `verify`
- Optional JSON logs

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## CLI

### Scan

```bash
ebook-extract scan /path/to/books -r --format auto
```

### Extract

```bash
ebook-extract extract /path/to/books \
  --format auto \
  --recursive \
  --manifest \
  --debug-order \
  --archive-format cbz \
  --hash-cache .cache/image_hashes.json \
  --parallelism 4
```

### Inspect

```bash
ebook-extract inspect /path/to/book.mobi --debug-order --verbose
```

### Verify

```bash
ebook-extract verify /path/to/books -r --format auto
```

## Common Extraction Flags

- `--min-size <bytes>`
- `--min-width <px>`
- `--min-height <px>`
- `--max-aspect-ratio <float>`
- `--no-dedup`
- `--add-ignore-hash <sha256>` (repeatable)
- `--all-images` (EPUB only)
- `--manifest`
- `--debug-order`
- `--archive-format cbz|cbr|pdf`
- `--hash-cache <path>`
- `--parallelism <n>`
- `--json-logs`
- `--dry-run`

## Programmatic Usage

```python
from src import EPUBImageExtractor, MobiImageExtractor

epub = EPUBImageExtractor(
    min_image_size=2048,
    min_width=300,
    min_height=300,
    max_aspect_ratio=3.5,
    write_manifest=True,
    write_debug_order=True,
    archive_format="cbz",
    hash_cache_path=".cache/hashes.json",
    parallelism=2,
)

epub.extract_from_directory("books", recursive=True)

mobi = MobiImageExtractor(write_manifest=True, archive_format="cbr")
mobi.extract_from_directory("books", recursive=True)
```

## Output

For each book, the extractor creates a folder with files named like:

```text
0000_cover.jpg
0001_page.jpg
0002_page.jpg
```

When enabled:

- `manifest.json` is created in the output folder
- `debug_order` payload is embedded in manifest
- archive is generated next to the folder (`.cbz`, `.cbr`, or `.pdf`)

## Notes

- DRM-protected files are not supported.
- `PDF` export requires Pillow:

```bash
pip install Pillow
```

## License

MIT
