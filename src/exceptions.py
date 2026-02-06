"""
Custom exceptions for eBook Image Extractor.
"""


class EbookExtractorError(Exception):
    """Base exception for all ebook extractor errors."""

    pass


class InvalidFileError(EbookExtractorError):
    """Raised when file is not a valid ebook format."""

    def __init__(self, filepath: str, expected_format: str, message: str = None):
        self.filepath = filepath
        self.expected_format = expected_format
        self.message = message or f"'{filepath}' is not a valid {expected_format} file"
        super().__init__(self.message)


class ExtractionError(EbookExtractorError):
    """Raised when image extraction fails."""

    def __init__(self, filepath: str, reason: str):
        self.filepath = filepath
        self.reason = reason
        self.message = f"Failed to extract images from '{filepath}': {reason}"
        super().__init__(self.message)


class CorruptedFileError(EbookExtractorError):
    """Raised when ebook file appears to be corrupted."""

    def __init__(self, filepath: str, details: str = None):
        self.filepath = filepath
        self.details = details
        self.message = f"File '{filepath}' appears to be corrupted"
        if details:
            self.message += f": {details}"
        super().__init__(self.message)


class NoImagesFoundError(EbookExtractorError):
    """Raised when no images are found in the ebook."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.message = f"No images found in '{filepath}'"
        super().__init__(self.message)


class OutputDirectoryError(EbookExtractorError):
    """Raised when there's an issue with the output directory."""

    def __init__(self, directory: str, reason: str):
        self.directory = directory
        self.reason = reason
        self.message = f"Output directory error '{directory}': {reason}"
        super().__init__(self.message)
