"""Manifest models and serialization helpers."""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
import json
import os
from typing import Dict, List, Optional


@dataclass
class ImageManifestItem:
    """Manifest entry for one extracted image.

    :param index: Sequential output index.
    :param filename: Saved filename.
    :param source_ref: Source reference path or record index string.
    :param image_hash: SHA256 hash.
    :param bytes_size: File size in bytes.
    :param width: Parsed width.
    :param height: Parsed height.
    :param classification: Image role.
    :param mime_type: MIME type.
    """

    index: int
    filename: str
    source_ref: str
    image_hash: str
    bytes_size: int
    width: int
    height: int
    classification: str
    mime_type: str


@dataclass
class ExtractionManifest:
    """Manifest for a single extracted book.

    :param source_file: Source ebook path.
    :param extracted_at: ISO timestamp.
    :param title: Optional title metadata.
    :param author: Optional author metadata.
    :param publisher: Optional publisher metadata.
    :param language: Optional language metadata.
    :param total_images: Total saved images.
    :param output_dir: Output directory.
    :param debug_order: Optional order debug payload.
    :param images: Extracted images list.
    """

    source_file: str
    extracted_at: str
    title: str = ""
    author: str = ""
    publisher: str = ""
    language: str = ""
    total_images: int = 0
    output_dir: str = ""
    debug_order: Optional[Dict] = None
    images: List[ImageManifestItem] = field(default_factory=list)

    @classmethod
    def create(cls, source_file: str, output_dir: str) -> "ExtractionManifest":
        """Build an empty manifest with timestamp.

        :param source_file: Source ebook path.
        :param output_dir: Output directory.
        :return: Manifest instance.
        """
        return cls(
            source_file=source_file,
            extracted_at=datetime.now(timezone.utc).isoformat(),
            output_dir=output_dir,
        )

    def add_item(self, item: ImageManifestItem) -> None:
        """Append an image entry.

        :param item: Item to append.
        """
        self.images.append(item)
        self.total_images = len(self.images)

    def to_dict(self) -> Dict:
        """Convert to serializable dictionary.

        :return: Dictionary representation.
        """
        return asdict(self)


def save_manifest(manifest: ExtractionManifest, output_dir: str) -> str:
    """Persist extraction manifest JSON.

    :param manifest: Manifest payload.
    :param output_dir: Directory where file is saved.
    :return: Output file path.
    """
    output_path = os.path.join(output_dir, "manifest.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(manifest.to_dict(), handle, indent=2, ensure_ascii=False)
    return output_path
