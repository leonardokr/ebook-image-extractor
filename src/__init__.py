"""
Image Extractor Package

A Python tool to extract images from files with advanced filtering and organization features.
"""

from .epub_extractor import EPUBImageExtractor
from .mobi_extractor import MobiImageExtractor

__all__ = ["EPUBImageExtractor", "MobiImageExtractor"]
