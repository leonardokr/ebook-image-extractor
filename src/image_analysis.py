"""Image analysis utilities.

This module provides image format detection, basic dimension parsing,
and image role classification used by extractors.
"""

from dataclasses import dataclass
import struct
from typing import Optional


@dataclass(frozen=True)
class ImageMetrics:
    """Computed metrics for a binary image payload.

    :param size_bytes: Payload size in bytes.
    :param width: Parsed width in pixels.
    :param height: Parsed height in pixels.
    :param extension: Canonical extension with leading dot.
    :param mime_type: MIME type when recognized.
    """

    size_bytes: int
    width: int
    height: int
    extension: str
    mime_type: str

    @property
    def aspect_ratio(self) -> float:
        """Return width/height ratio.

        :return: Aspect ratio or 0.0 when height is zero.
        """
        if self.height <= 0:
            return 0.0
        return self.width / self.height


def _detect_extension(data: bytes) -> str:
    """Detect extension from signature bytes.

    :param data: Binary payload.
    :return: Extension with leading dot.
    """
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return ".gif"
    if data.startswith(b"BM"):
        return ".bmp"
    if len(data) > 12 and data[8:12] == b"WEBP":
        return ".webp"
    if data.startswith(b"<svg") or b"<svg" in data[:512]:
        return ".svg"
    return ".jpg"


def _mime_for_extension(extension: str) -> str:
    """Map extension to MIME type.

    :param extension: Canonical extension.
    :return: MIME type string.
    """
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }.get(extension, "application/octet-stream")


def _parse_png_dimensions(data: bytes) -> Optional[tuple]:
    """Parse PNG dimensions.

    :param data: PNG bytes.
    :return: Width and height or ``None``.
    """
    if len(data) < 24:
        return None
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    return struct.unpack(">LL", data[16:24])


def _parse_gif_dimensions(data: bytes) -> Optional[tuple]:
    """Parse GIF dimensions.

    :param data: GIF bytes.
    :return: Width and height or ``None``.
    """
    if len(data) < 10:
        return None
    if not (data.startswith(b"GIF87a") or data.startswith(b"GIF89a")):
        return None
    return struct.unpack("<HH", data[6:10])


def _parse_bmp_dimensions(data: bytes) -> Optional[tuple]:
    """Parse BMP dimensions.

    :param data: BMP bytes.
    :return: Width and height or ``None``.
    """
    if len(data) < 26:
        return None
    if not data.startswith(b"BM"):
        return None
    width = struct.unpack("<I", data[18:22])[0]
    height = struct.unpack("<I", data[22:26])[0]
    return width, height


def _parse_webp_dimensions(data: bytes) -> Optional[tuple]:
    """Parse WEBP dimensions.

    :param data: WEBP bytes.
    :return: Width and height or ``None``.
    """
    if len(data) < 30:
        return None
    if not (data.startswith(b"RIFF") and data[8:12] == b"WEBP"):
        return None
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        w = 1 + int.from_bytes(data[24:27], "little")
        h = 1 + int.from_bytes(data[27:30], "little")
        return w, h
    if chunk == b"VP8L" and len(data) >= 25:
        b0, b1, b2, b3 = data[21], data[22], data[23], data[24]
        w = 1 + (((b1 & 0x3F) << 8) | b0)
        h = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
        return w, h
    return None


def _parse_jpeg_dimensions(data: bytes) -> Optional[tuple]:
    """Parse JPEG dimensions.

    :param data: JPEG bytes.
    :return: Width and height or ``None``.
    """
    if len(data) < 4 or not data.startswith(b"\xff\xd8"):
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in (0xD8, 0xD9):
            continue
        if i + 2 > len(data):
            break
        seg_len = struct.unpack(">H", data[i : i + 2])[0]
        if seg_len < 2 or i + seg_len > len(data):
            break
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            if i + 7 <= len(data):
                h, w = struct.unpack(">HH", data[i + 3 : i + 7])
                return w, h
            break
        i += seg_len
    return None


def parse_image_metrics(data: bytes) -> ImageMetrics:
    """Parse common metrics from binary image payload.

    :param data: Binary image payload.
    :return: Parsed metrics.
    """
    extension = _detect_extension(data)
    width, height = 0, 0
    parsed = (
        _parse_png_dimensions(data)
        or _parse_gif_dimensions(data)
        or _parse_bmp_dimensions(data)
        or _parse_webp_dimensions(data)
        or _parse_jpeg_dimensions(data)
    )
    if parsed:
        width, height = parsed
    return ImageMetrics(
        size_bytes=len(data),
        width=width,
        height=height,
        extension=extension,
        mime_type=_mime_for_extension(extension),
    )


def classify_image(metrics: ImageMetrics, is_cover: bool = False) -> str:
    """Classify image role for naming and filtering.

    :param metrics: Parsed metrics.
    :param is_cover: Whether payload is detected as cover.
    :return: One of ``cover``, ``thumbnail``, ``decoration`` or ``page``.
    """
    if is_cover:
        return "cover"
    if metrics.width > 0 and metrics.height > 0:
        if metrics.width <= 140 or metrics.height <= 140:
            return "thumbnail"
        if metrics.aspect_ratio >= 4.0 or metrics.aspect_ratio <= 0.25:
            return "decoration"
    if metrics.size_bytes < 4096:
        return "decoration"
    return "page"
