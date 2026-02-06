"""
eBook Image Extractor Package

A Python tool to extract images from EPUB and MOBI/AZW files with advanced
filtering, deduplication, and organization features.
"""

from .base_extractor import BaseExtractor, ExtractionStats, BookMetadata, ImageInfo
from .epub_extractor import EPUBImageExtractor
from .mobi_extractor import MobiImageExtractor
from .exceptions import (
    EbookExtractorError,
    InvalidFileError,
    ExtractionError,
    CorruptedFileError,
    NoImagesFoundError,
    OutputDirectoryError,
)

__version__ = "3.0.0"

__all__ = [
    "BaseExtractor",
    "EPUBImageExtractor",
    "MobiImageExtractor",
    "ExtractionStats",
    "BookMetadata",
    "ImageInfo",
    "EbookExtractorError",
    "InvalidFileError",
    "ExtractionError",
    "CorruptedFileError",
    "NoImagesFoundError",
    "OutputDirectoryError",
]
