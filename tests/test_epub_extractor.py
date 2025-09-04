"""
Unit tests for EPUB Image Extractor.
"""

import unittest
import tempfile
import os
import shutil
from src.epub_extractor import EPUBImageExtractor


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
        expected_hash = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
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


if __name__ == "__main__":
    unittest.main()
