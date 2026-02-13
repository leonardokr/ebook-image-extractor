"""
Unit tests for eBook Image Extractors (EPUB and MOBI).
"""

import unittest
import tempfile
import os
import shutil
import struct
import zipfile
from src.epub_extractor import EPUBImageExtractor
from src.mobi_extractor import MobiImageExtractor
from src.image_analysis import parse_image_metrics, classify_image
from src.archive_exporter import export_directory_as_comic_archive
from src.pdf_exporter import export_directory_as_pdf


class TestEPUBImageExtractor(unittest.TestCase):
    """Tests for EPUBImageExtractor class."""

    def setUp(self):
        """Initial test setup."""
        self.extractor = EPUBImageExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup after tests."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test class initialization."""
        self.assertIsInstance(self.extractor.ignored_hashes, set)
        self.assertTrue(len(self.extractor.ignored_hashes) >= 3)

    def test_hash_bytes_sha256(self):
        """Test SHA256 hash calculation."""
        test_data = b"test data"
        expected_hash = (
            "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
        )
        result = self.extractor.hash_bytes_sha256(test_data)
        self.assertEqual(result, expected_hash)

    def test_normalize_path(self):
        """Test path normalization."""
        base_path = "OEBPS/chapter1.xhtml"
        relative_path = "../Images/image1.jpg"
        result = self.extractor.normalize_path(base_path, relative_path)
        expected = "Images/image1.jpg"
        self.assertEqual(result, expected)

    def test_add_ignored_hash(self):
        """Test adding hash to ignore list."""
        initial_count = len(self.extractor.ignored_hashes)
        test_hash = "test_hash_123"
        self.extractor.add_ignored_hash(test_hash)

        self.assertEqual(len(self.extractor.ignored_hashes), initial_count + 1)
        self.assertIn(test_hash, self.extractor.ignored_hashes)

    def test_remove_ignored_hash(self):
        """Test removing hash from ignore list."""
        test_hash = "test_hash_456"
        self.extractor.add_ignored_hash(test_hash)
        initial_count = len(self.extractor.ignored_hashes)

        self.extractor.remove_ignored_hash(test_hash)

        self.assertEqual(len(self.extractor.ignored_hashes), initial_count - 1)
        self.assertNotIn(test_hash, self.extractor.ignored_hashes)

    def test_find_epub_files_empty_directory(self):
        """Test searching for EPUB files in empty directory."""
        result = self.extractor.find_epub_files(self.temp_dir)
        self.assertEqual(result, [])

    def test_custom_ignored_hashes(self):
        """Test initialization with custom hashes."""
        custom_hashes = {"hash1", "hash2", "hash3"}
        extractor = EPUBImageExtractor(ignored_hashes=custom_hashes)

        self.assertEqual(extractor.ignored_hashes, custom_hashes)


class TestMobiImageExtractor(unittest.TestCase):
    """Tests for MobiImageExtractor class."""

    def setUp(self):
        """Initial test setup."""
        self.extractor = MobiImageExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup after tests."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test class initialization."""
        self.assertIsInstance(self.extractor.ignored_hashes, set)
        self.assertTrue(len(self.extractor.ignored_hashes) >= 3)

    def test_hash_bytes_sha256(self):
        """Test SHA256 hash calculation."""
        test_data = b"test data"
        expected_hash = (
            "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
        )
        result = self.extractor.hash_bytes_sha256(test_data)
        self.assertEqual(result, expected_hash)

    def test_add_ignored_hash(self):
        """Test adding hash to ignore list."""
        initial_count = len(self.extractor.ignored_hashes)
        test_hash = "test_hash_mobi_123"
        self.extractor.add_ignored_hash(test_hash)

        self.assertEqual(len(self.extractor.ignored_hashes), initial_count + 1)
        self.assertIn(test_hash, self.extractor.ignored_hashes)

    def test_remove_ignored_hash(self):
        """Test removing hash from ignore list."""
        test_hash = "test_hash_mobi_456"
        self.extractor.add_ignored_hash(test_hash)
        initial_count = len(self.extractor.ignored_hashes)

        self.extractor.remove_ignored_hash(test_hash)

        self.assertEqual(len(self.extractor.ignored_hashes), initial_count - 1)
        self.assertNotIn(test_hash, self.extractor.ignored_hashes)

    def test_find_mobi_files_empty_directory(self):
        """Test searching for MOBI files in empty directory."""
        result = self.extractor.find_mobi_files(self.temp_dir)
        self.assertEqual(result, [])

    def test_custom_ignored_hashes(self):
        """Test initialization with custom hashes."""
        custom_hashes = {"mobi_hash1", "mobi_hash2", "mobi_hash3"}
        extractor = MobiImageExtractor(ignored_hashes=custom_hashes)

        self.assertEqual(extractor.ignored_hashes, custom_hashes)

    def test_is_image_data_jpeg(self):
        """Test JPEG image detection."""
        jpeg_data = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        result = self.extractor._is_image_data(jpeg_data)
        self.assertTrue(result)

    def test_is_image_data_png(self):
        """Test PNG image detection."""
        png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        result = self.extractor._is_image_data(png_data)
        self.assertTrue(result)

    def test_is_image_data_gif(self):
        """Test GIF image detection."""
        gif_data = b"GIF87a\x01\x00\x01\x00"
        result = self.extractor._is_image_data(gif_data)
        self.assertTrue(result)

    def test_is_image_data_bmp(self):
        """Test BMP image detection."""
        bmp_data = b"BM\x36\x00\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00"
        result = self.extractor._is_image_data(bmp_data)
        self.assertTrue(result)

    def test_is_image_data_webp(self):
        """Test WebP image detection."""
        webp_data = b"RIFF\x00\x00\x00\x00WEBPVP8 "
        result = self.extractor._is_image_data(webp_data)
        self.assertTrue(result)

    def test_is_image_data_invalid(self):
        """Test non-image data detection."""
        text_data = b"This is not an image"
        result = self.extractor._is_image_data(text_data)
        self.assertFalse(result)

    def test_is_image_data_too_short(self):
        """Test image detection with insufficient data."""
        short_data = b"abc"
        result = self.extractor._is_image_data(short_data)
        self.assertFalse(result)

    def test_get_image_extension_jpeg(self):
        """Test JPEG extension detection."""
        jpeg_data = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        result = self.extractor._get_image_extension(jpeg_data)
        self.assertEqual(result, ".jpg")

    def test_get_image_extension_png(self):
        """Test PNG extension detection."""
        png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        result = self.extractor._get_image_extension(png_data)
        self.assertEqual(result, ".png")

    def test_get_image_extension_gif(self):
        """Test GIF extension detection."""
        gif_data = b"GIF87a\x01\x00\x01\x00"
        result = self.extractor._get_image_extension(gif_data)
        self.assertEqual(result, ".gif")

    def test_get_image_extension_webp(self):
        """Test WebP extension detection."""
        webp_data = b"RIFF\x00\x00\x00\x00WEBPVP8 "
        result = self.extractor._get_image_extension(webp_data)
        self.assertEqual(result, ".webp")

    def test_get_image_extension_default(self):
        """Test default extension for unknown format."""
        unknown_data = b"unknown image format"
        result = self.extractor._get_image_extension(unknown_data)
        self.assertEqual(result, ".jpg")

    def test_extract_image_order_from_html_mixed_sources(self):
        """Test reading order extraction with mixed MOBI img source formats."""
        html = (
            b'<img src="Images/image0003.jpg" />'
            b'<img src="kindle:embed:0001?mime=image/jpeg" />'
            b'<img recindex="0002" />'
        )
        result = self.extractor._extract_image_order_from_html(html)
        self.assertEqual(result, [3, 1, 2])

    def test_get_image_records_in_order_maps_relative_indices(self):
        """Test relative image references are mapped using first_image_index."""
        jpeg1 = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00"
        jpeg2 = b"\xff\xd8\xff\xe0\x00\x10JFIF\x01"
        jpeg3 = b"\xff\xd8\xff\xe0\x00\x10JFIF\x02"

        chunks = [b"HEAD", b"TEXT", jpeg1, jpeg2, jpeg3]
        offsets = []
        cursor = 0
        for chunk in chunks:
            start = cursor
            end = start + len(chunk)
            offsets.append((start, end))
            cursor = end
        data = b"".join(chunks)

        image_records = self.extractor._get_image_records_in_order(
            data, offsets, [0, 1, 2], first_image_index=2
        )
        self.assertEqual([idx for idx, _ in image_records], [2, 3, 4])

    def test_get_image_records_in_order_fallback_without_html(self):
        """Test fallback to sequential image records when no HTML order is available."""
        jpeg1 = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00"
        jpeg2 = b"\xff\xd8\xff\xe0\x00\x10JFIF\x01"

        chunks = [b"HEAD", jpeg1, b"TEXT", jpeg2]
        offsets = []
        cursor = 0
        for chunk in chunks:
            start = cursor
            end = start + len(chunk)
            offsets.append((start, end))
            cursor = end
        data = b"".join(chunks)

        image_records = self.extractor._get_image_records_in_order(
            data, offsets, html_order=None, first_image_index=1
        )
        self.assertEqual([idx for idx, _ in image_records], [1, 3])

    def test_get_image_records_in_order_infers_relative_one_based(self):
        """Test 1-based relative refs when header first_image_index is missing."""
        jpeg = lambda n: b"\xff\xd8\xff\xe0\x00\x10JFIF" + bytes([n])
        chunks = [b"HEAD", b"TEXT", jpeg(0), jpeg(1), jpeg(2), jpeg(3)]
        offsets = []
        cursor = 0
        for chunk in chunks:
            start = cursor
            end = start + len(chunk)
            offsets.append((start, end))
            cursor = end
        data = b"".join(chunks)

        image_records = self.extractor._get_image_records_in_order(
            data, offsets, html_order=[1, 4, 2], first_image_index=0
        )
        self.assertEqual([idx for idx, _ in image_records], [2, 5, 3, 4])

    def test_read_pdb_records_empty_data(self):
        """Test PDB record reading with empty data."""
        result = self.extractor._read_pdb_records(b"")
        self.assertEqual(result, [])

    def test_read_pdb_records_insufficient_data(self):
        """Test PDB record reading with insufficient data."""
        short_data = b"TPZ" + b"\x00" * 70
        result = self.extractor._read_pdb_records(short_data)
        self.assertEqual(result, [])

    def create_mock_mobi_file(self, filename):
        """Create a mock MOBI file for testing."""
        mock_data = b"TPZ"
        mock_data += b"\x00" * 73
        mock_data += struct.pack(">H", 2)
        mock_data += struct.pack(">L", 100)
        mock_data += b"\x00" * 4
        mock_data += struct.pack(">L", 200)
        mock_data += b"\x00" * 4
        mock_data += b"\x00" * 22
        mock_data += b"MOBI header data" + b"\x00" * 84
        mock_data += (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb"
        )

        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "wb") as f:
            f.write(mock_data)
        return filepath

    def test_find_mobi_files_with_files(self):
        """Test finding MOBI files when they exist."""
        self.create_mock_mobi_file("test1.mobi")
        self.create_mock_mobi_file("test2.azw")
        self.create_mock_mobi_file("test3.azw3")

        with open(os.path.join(self.temp_dir, "test.txt"), "w") as f:
            f.write("not a mobi file")

        result = self.extractor.find_mobi_files(self.temp_dir)

        self.assertEqual(len(result), 3)

        extensions = [os.path.splitext(f)[1] for f in result]
        self.assertIn(".mobi", extensions)
        self.assertIn(".azw", extensions)
        self.assertIn(".azw3", extensions)


class TestExtractorCompatibility(unittest.TestCase):
    """Tests for compatibility between EPUB and MOBI extractors."""

    def setUp(self):
        """Initial test setup."""
        self.epub_extractor = EPUBImageExtractor()
        self.mobi_extractor = MobiImageExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup after tests."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_same_default_hashes(self):
        """Test that both extractors use the same default ignored hashes."""
        self.assertEqual(
            self.epub_extractor.DEFAULT_IGNORED_HASHES,
            self.mobi_extractor.DEFAULT_IGNORED_HASHES,
        )

    def test_same_hash_function(self):
        """Test that both extractors use the same hash function."""
        test_data = b"compatibility test data"

        epub_hash = self.epub_extractor.hash_bytes_sha256(test_data)
        mobi_hash = self.mobi_extractor.hash_bytes_sha256(test_data)

        self.assertEqual(epub_hash, mobi_hash)

    def test_hash_management_compatibility(self):
        """Test that hash management works the same way."""
        test_hash = "compatibility_test_hash"

        self.epub_extractor.add_ignored_hash(test_hash)
        self.mobi_extractor.add_ignored_hash(test_hash)

        self.assertIn(test_hash, self.epub_extractor.ignored_hashes)
        self.assertIn(test_hash, self.mobi_extractor.ignored_hashes)

        self.epub_extractor.remove_ignored_hash(test_hash)
        self.mobi_extractor.remove_ignored_hash(test_hash)

        self.assertNotIn(test_hash, self.epub_extractor.ignored_hashes)
        self.assertNotIn(test_hash, self.mobi_extractor.ignored_hashes)

    def test_extraction_stats_structure(self):
        """Test that ExtractionStats has all required fields."""
        from src.base_extractor import ExtractionStats
        stats = ExtractionStats()
        stats_dict = stats.to_dict()

        required_keys = {
            "saved",
            "ignored",
            "missing",
            "duplicates",
            "filtered_by_size",
            "filtered_by_dimensions",
            "filtered_by_aspect_ratio",
        }
        self.assertEqual(set(stats_dict.keys()), required_keys)

    def test_image_extensions_compatibility(self):
        """Test that both extractors support compatible image extensions."""
        epub_extensions = self.epub_extractor.IMAGE_EXTENSIONS
        mobi_extensions = self.mobi_extractor.IMAGE_EXTENSIONS

        common_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

        for ext in common_extensions:
            self.assertIn(ext, epub_extensions)
            self.assertIn(ext, mobi_extensions)

    def test_image_analysis_metrics_png(self):
        """Test metric parser for PNG dimensions."""
        png_data = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x01\x00"
            b"\x00\x00\x02\x00"
            b"\x08\x02\x00\x00\x00"
        )
        metrics = parse_image_metrics(png_data)
        self.assertEqual(metrics.width, 256)
        self.assertEqual(metrics.height, 512)
        self.assertEqual(metrics.extension, ".png")

    def test_image_classification_cover(self):
        """Test image role classification for cover images."""
        png_data = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x01\x00"
            b"\x00\x00\x02\x00"
            b"\x08\x02\x00\x00\x00"
        )
        metrics = parse_image_metrics(png_data)
        role = classify_image(metrics, is_cover=True)
        self.assertEqual(role, "cover")

    def test_archive_export_cbz_and_cbr(self):
        """Test CBZ and CBR archive creation."""
        output_dir = os.path.join(self.temp_dir, "book")
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "0000_page.jpg"), "wb") as handle:
            handle.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00")

        cbz = export_directory_as_comic_archive(output_dir, "cbz")
        cbr = export_directory_as_comic_archive(output_dir, "cbr")

        self.assertTrue(os.path.exists(cbz))
        self.assertTrue(os.path.exists(cbr))

        with zipfile.ZipFile(cbz, "r") as zipf:
            self.assertIn("0000_page.jpg", zipf.namelist())

    def test_pdf_export(self):
        """Test PDF export behavior."""
        output_dir = os.path.join(self.temp_dir, "book_pdf")
        os.makedirs(output_dir, exist_ok=True)
        try:
            from PIL import Image
        except ImportError:
            with open(os.path.join(output_dir, "0000_page.jpg"), "wb") as handle:
                handle.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00")
            with self.assertRaises(RuntimeError):
                export_directory_as_pdf(output_dir)
            return

        image = Image.new("RGB", (64, 64), color=(255, 255, 255))
        image.save(os.path.join(output_dir, "0000_page.jpg"), "JPEG")
        image.close()
        pdf_path = export_directory_as_pdf(output_dir)
        self.assertTrue(os.path.exists(pdf_path))


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestEPUBImageExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestMobiImageExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestExtractorCompatibility))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    exit(0 if result.wasSuccessful() else 1)
