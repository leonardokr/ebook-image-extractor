"""
MOBI Image Extractor

Extracts images from MOBI/AZW files with proper reading order support.
"""

import struct
import os
import re
from typing import List, Set, Dict, Optional, Tuple
import logging

from .base_extractor import BaseExtractor, ExtractionStats, BookMetadata
from .exceptions import InvalidFileError, CorruptedFileError, ExtractionError


class MobiImageExtractor(BaseExtractor):
    """
    Extracts images from MOBI files with filtering and organization capabilities.
    """

    SUPPORTED_EXTENSIONS: Set[str] = {".mobi", ".azw", ".azw3"}

    IMAGE_EXTENSIONS: Set[str] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".bmp",
    }

    MOBI_MAGIC = b"BOOKMOBI"
    PALMDOC_MAGIC = b"TEXtREAd"

    COMPRESSION_NONE = 1
    COMPRESSION_PALMDOC = 2
    COMPRESSION_HUFF = 17480

    EXTH_TYPES = {
        100: "author",
        101: "publisher",
        103: "description",
        104: "isbn",
        105: "subject",
        106: "publishdate",
        109: "rights",
        201: "cover_offset",
        202: "thumb_offset",
        503: "title",
    }

    def __init__(
        self,
        ignored_hashes: Optional[Set[str]] = None,
        min_image_size: int = 0,
        enable_deduplication: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(ignored_hashes, min_image_size, enable_deduplication, logger)
        self._mobi_header: Dict = {}
        self._exth_data: Dict = {}

    def find_files(self, directory: str, recursive: bool = False) -> List[str]:
        mobi_files = []
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in self.SUPPORTED_EXTENSIONS):
                        mobi_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                if any(file.lower().endswith(ext) for ext in self.SUPPORTED_EXTENSIONS):
                    mobi_files.append(os.path.join(directory, file))
        return sorted(mobi_files)

    def find_mobi_files(self, directory: str) -> List[str]:
        return self.find_files(directory, recursive=False)

    def _is_image_data(self, data: bytes) -> bool:
        if len(data) < 8:
            return False

        if data.startswith(b"\xff\xd8\xff"):
            return True
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return True
        if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
            return True
        if data.startswith(b"BM") and len(data) > 14:
            return True
        if len(data) > 12 and data[8:12] == b"WEBP":
            return True

        return False

    def _get_image_extension(self, data: bytes) -> str:
        if data.startswith(b"\xff\xd8\xff"):
            return ".jpg"
        elif data.startswith(b"\x89PNG"):
            return ".png"
        elif data.startswith(b"GIF8"):
            return ".gif"
        elif data.startswith(b"BM"):
            return ".bmp"
        elif len(data) > 12 and data[8:12] == b"WEBP":
            return ".webp"
        else:
            return ".jpg"

    def _read_pdb_header(self, data: bytes) -> Dict:
        if len(data) < 78:
            raise CorruptedFileError("", "File too small for PDB header")

        header = {
            "name": data[0:32].rstrip(b"\x00").decode("latin-1", errors="ignore"),
            "attributes": struct.unpack(">H", data[32:34])[0],
            "version": struct.unpack(">H", data[34:36])[0],
            "creation_time": struct.unpack(">L", data[36:40])[0],
            "modification_time": struct.unpack(">L", data[40:44])[0],
            "backup_time": struct.unpack(">L", data[44:48])[0],
            "modification_number": struct.unpack(">L", data[48:52])[0],
            "app_info_offset": struct.unpack(">L", data[52:56])[0],
            "sort_info_offset": struct.unpack(">L", data[56:60])[0],
            "type": data[60:64],
            "creator": data[64:68],
            "unique_id_seed": struct.unpack(">L", data[68:72])[0],
            "next_record_list": struct.unpack(">L", data[72:76])[0],
            "num_records": struct.unpack(">H", data[76:78])[0],
        }
        return header

    def _read_pdb_records(self, data: bytes) -> List[Tuple[int, int]]:
        if len(data) < 78:
            return []

        num_records = struct.unpack(">H", data[76:78])[0]

        record_offsets = []
        for i in range(num_records):
            offset_pos = 78 + (i * 8)
            if offset_pos + 4 <= len(data):
                offset = struct.unpack(">L", data[offset_pos : offset_pos + 4])[0]
                record_offsets.append(offset)

        records = []
        for i in range(len(record_offsets)):
            start = record_offsets[i]
            end = record_offsets[i + 1] if i + 1 < len(record_offsets) else len(data)
            if start < end and start < len(data):
                records.append((start, end))

        return records

    def _read_palmdoc_header(self, data: bytes, record0_start: int) -> Dict:
        if len(data) < record0_start + 16:
            return {}

        header = {
            "compression": struct.unpack(">H", data[record0_start:record0_start + 2])[0],
            "text_length": struct.unpack(">L", data[record0_start + 4:record0_start + 8])[0],
            "record_count": struct.unpack(">H", data[record0_start + 8:record0_start + 10])[0],
            "record_size": struct.unpack(">H", data[record0_start + 10:record0_start + 12])[0],
            "encryption_type": struct.unpack(">H", data[record0_start + 12:record0_start + 14])[0],
        }
        return header

    def _read_mobi_header(self, data: bytes, record0_start: int) -> Dict:
        mobi_start = record0_start + 16

        if len(data) < mobi_start + 132:
            return {}

        if data[mobi_start:mobi_start + 4] != b"MOBI":
            return {}

        header = {
            "identifier": data[mobi_start:mobi_start + 4],
            "header_length": struct.unpack(">L", data[mobi_start + 4:mobi_start + 8])[0],
            "mobi_type": struct.unpack(">L", data[mobi_start + 8:mobi_start + 12])[0],
            "text_encoding": struct.unpack(">L", data[mobi_start + 12:mobi_start + 16])[0],
            "unique_id": struct.unpack(">L", data[mobi_start + 16:mobi_start + 20])[0],
            "file_version": struct.unpack(">L", data[mobi_start + 20:mobi_start + 24])[0],
            "first_non_book_index": struct.unpack(">L", data[mobi_start + 80:mobi_start + 84])[0],
            "full_name_offset": struct.unpack(">L", data[mobi_start + 84:mobi_start + 88])[0],
            "full_name_length": struct.unpack(">L", data[mobi_start + 88:mobi_start + 92])[0],
            "language": struct.unpack(">L", data[mobi_start + 92:mobi_start + 96])[0],
            "first_image_index": struct.unpack(">L", data[mobi_start + 108:mobi_start + 112])[0],
        }

        if header["header_length"] >= 244:
            header["exth_flags"] = struct.unpack(">L", data[mobi_start + 128:mobi_start + 132])[0]

        return header

    def _read_exth_header(self, data: bytes, record0_start: int, mobi_header_length: int) -> Dict:
        exth_start = record0_start + 16 + mobi_header_length

        if len(data) < exth_start + 12:
            return {}

        if data[exth_start:exth_start + 4] != b"EXTH":
            return {}

        exth_count = struct.unpack(">L", data[exth_start + 8:exth_start + 12])[0]

        exth_data = {}
        pos = exth_start + 12

        for _ in range(exth_count):
            if pos + 8 > len(data):
                break

            record_type = struct.unpack(">L", data[pos:pos + 4])[0]
            record_length = struct.unpack(">L", data[pos + 4:pos + 8])[0]

            if record_length < 8:
                break

            value_data = data[pos + 8:pos + record_length]

            if record_type in self.EXTH_TYPES:
                field_name = self.EXTH_TYPES[record_type]
                if record_type in (201, 202):
                    if len(value_data) >= 4:
                        exth_data[field_name] = struct.unpack(">L", value_data[:4])[0]
                else:
                    exth_data[field_name] = value_data.decode("utf-8", errors="ignore")

            pos += record_length

        return exth_data

    def _decompress_palmdoc(self, data: bytes) -> bytes:
        result = bytearray()
        i = 0
        while i < len(data):
            byte = data[i]
            i += 1

            if byte == 0:
                result.append(byte)
            elif 1 <= byte <= 8:
                result.extend(data[i:i + byte])
                i += byte
            elif byte <= 0x7F:
                result.append(byte)
            elif byte <= 0xBF:
                if i >= len(data):
                    break
                next_byte = data[i]
                i += 1
                distance = ((byte << 8) | next_byte) >> 3 & 0x7FF
                length = (next_byte & 0x07) + 3
                for _ in range(length):
                    if len(result) >= distance:
                        result.append(result[-distance])
                    else:
                        break
            else:
                result.append(ord(' '))
                result.append(byte ^ 0x80)

        return bytes(result)

    def _find_first_image_record(self, data: bytes, records: List[Tuple[int, int]]) -> int:
        for i, (start, end) in enumerate(records):
            if start < len(data) and end <= len(data):
                if self._is_image_data(data[start:end]):
                    return i
        return len(records)

    def _extract_text_content(
        self, data: bytes, records: List[Tuple[int, int]], palmdoc_header: Dict, mobi_header: Dict
    ) -> bytes:
        compression = palmdoc_header.get("compression", 1)
        record_count = palmdoc_header.get("record_count", 0)

        text_content = bytearray()

        # Prefer official text record count from PalmDOC header.
        # Fallback to first detected image record for malformed files.
        if isinstance(record_count, int) and record_count > 0:
            text_record_end = min(1 + record_count, len(records))
        else:
            text_record_end = self._find_first_image_record(data, records)

        for i in range(1, text_record_end):
            if i >= len(records):
                break

            start, end = records[i]
            if start >= len(data) or end > len(data):
                continue

            record_data = data[start:end]

            if compression == self.COMPRESSION_PALMDOC:
                try:
                    decompressed = self._decompress_palmdoc(record_data)
                    text_content.extend(decompressed)
                except Exception:
                    text_content.extend(record_data)
            elif compression == self.COMPRESSION_NONE:
                text_content.extend(record_data)

        return bytes(text_content)

    def _extract_image_order_from_html(
        self, html_content: bytes
    ) -> List[int]:
        """
        Extract image record indices from HTML content in reading order.

        The HTML contains <img src="Images/imageXXXXX.jpeg"> tags where XXXXX
        is the PDB record number. This order defines the reading sequence.
        """
        image_order = []
        seen = set()
        tag_pattern = rb"<img\b[^>]*>"
        value_patterns = [
            # Common MOBI path pattern: Images/image00012.jpg
            rb'src=["\']?[^"\'>]*?(?:image|cover|thumb)0*(\d+)\.\w+["\']?',
            # Kindle embedded references: kindle:embed:12?mime=image/jpeg
            rb'src=["\']?kindle:embed:0*(\d+)(?:\?[^"\']*)?["\']?',
            # Some variants use explicit recindex attribute in img tags
            rb'recindex=["\']?0*(\d+)["\']?',
        ]

        for tag_match in re.finditer(tag_pattern, html_content, re.IGNORECASE):
            tag = tag_match.group(0)
            for pattern in value_patterns:
                match = re.search(pattern, tag, re.IGNORECASE)
                if not match:
                    continue
                try:
                    record_idx = int(match.group(1))
                    if record_idx not in seen:
                        seen.add(record_idx)
                        image_order.append(record_idx)
                except (ValueError, IndexError):
                    pass
                break

        return image_order

    def _get_image_records_in_order(
        self,
        data: bytes,
        records: List[Tuple[int, int]],
        html_order: Optional[List[int]] = None,
        first_image_index: int = 0,
    ) -> List[Tuple[int, bytes]]:
        """
        Get image records in the correct reading order.

        If html_order is provided, images are returned in that order.
        Supports absolute record indices and indices relative to first_image_index.
        If html_order is missing or partial, falls back to sequential record order.
        """
        image_map: Dict[int, bytes] = {}
        for i, (start, end) in enumerate(records):
            if start >= len(data) or end > len(data):
                continue

            record_data = data[start:end]

            if self._is_image_data(record_data):
                image_map[i] = record_data

        image_records = []
        seen = set()
        sorted_image_indices = sorted(image_map)

        inferred_first_image_index = first_image_index
        if inferred_first_image_index <= 0 and sorted_image_indices:
            inferred_first_image_index = sorted_image_indices[0]

        if html_order:
            strategies = [("absolute", 0)]
            if inferred_first_image_index > 0:
                # If references include 0, prefer 0-based relative mapping.
                prefer_zero_based = any(idx == 0 for idx in html_order)
                if prefer_zero_based:
                    strategies.extend([("relative0", inferred_first_image_index), ("relative1", inferred_first_image_index)])
                else:
                    strategies.extend([("relative1", inferred_first_image_index), ("relative0", inferred_first_image_index)])

            best_strategy = ("absolute", 0)
            best_match_count = -1
            for strategy, base in strategies:
                local_seen = set()
                for ref_idx in html_order:
                    if strategy == "absolute":
                        candidate = ref_idx
                    elif strategy == "relative0":
                        candidate = base + ref_idx
                    else:
                        candidate = base + ref_idx - 1

                    if candidate in image_map:
                        local_seen.add(candidate)

                match_count = len(local_seen)
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_strategy = (strategy, base)

            strategy, base = best_strategy
            for ref_idx in html_order:
                if strategy == "absolute":
                    candidate = ref_idx
                elif strategy == "relative0":
                    candidate = base + ref_idx
                else:
                    candidate = base + ref_idx - 1

                if candidate in image_map and candidate not in seen:
                    seen.add(candidate)
                    image_records.append((candidate, image_map[candidate]))

        # Keep deterministic output and avoid missing images not referenced in HTML.
        for record_idx in sorted_image_indices:
            if record_idx in seen:
                continue
            if inferred_first_image_index > 0 and record_idx < inferred_first_image_index:
                continue
            seen.add(record_idx)
            image_records.append((record_idx, image_map[record_idx]))

        return image_records

    def extract_metadata(self, file_path: str) -> BookMetadata:
        metadata = BookMetadata()

        try:
            with open(file_path, "rb") as f:
                data = f.read()

            if self.MOBI_MAGIC not in data[:100] and self.PALMDOC_MAGIC not in data[:100]:
                return metadata

            records = self._read_pdb_records(data)
            if not records:
                return metadata

            record0_start = records[0][0]
            mobi_header = self._read_mobi_header(data, record0_start)

            if not mobi_header:
                return metadata

            if mobi_header.get("full_name_offset") and mobi_header.get("full_name_length"):
                name_start = record0_start + mobi_header["full_name_offset"]
                name_end = name_start + mobi_header["full_name_length"]
                if name_end <= len(data):
                    metadata.title = data[name_start:name_end].decode("utf-8", errors="ignore")

            if mobi_header.get("exth_flags", 0) & 0x40:
                exth_data = self._read_exth_header(data, record0_start, mobi_header["header_length"])

                if exth_data.get("title"):
                    metadata.title = exth_data["title"]
                if exth_data.get("author"):
                    metadata.author = exth_data["author"]
                if exth_data.get("publisher"):
                    metadata.publisher = exth_data["publisher"]

                if exth_data.get("cover_offset") is not None:
                    first_image = mobi_header.get("first_image_index", 0)
                    cover_record_idx = first_image + exth_data["cover_offset"]
                    if cover_record_idx < len(records):
                        start, end = records[cover_record_idx]
                        if start < len(data) and end <= len(data):
                            cover_data = data[start:end]
                            if self._is_image_data(cover_data):
                                metadata.cover_image = cover_data

        except Exception as e:
            self.logger.warning(f"Could not extract metadata from {file_path}: {e}")

        return metadata

    def extract_images(
        self, file_path: str, output_dir: str, dry_run: bool = False
    ) -> ExtractionStats:
        stats = ExtractionStats()

        try:
            with open(file_path, "rb") as f:
                data = f.read()

            if self.MOBI_MAGIC not in data[:100] and self.PALMDOC_MAGIC not in data[:100]:
                raise InvalidFileError(file_path, "MOBI")

            records = self._read_pdb_records(data)
            if not records:
                raise CorruptedFileError(file_path, "No PDB records found")

            self.logger.debug(f"Found {len(records)} PDB records")

            record0_start = records[0][0]
            palmdoc_header = self._read_palmdoc_header(data, record0_start)
            mobi_header = self._read_mobi_header(data, record0_start)

            if mobi_header:
                if mobi_header.get("exth_flags", 0) & 0x40:
                    self._exth_data = self._read_exth_header(
                        data, record0_start, mobi_header["header_length"]
                    )

            html_order = None
            first_image_index = mobi_header.get("first_image_index", 0) if mobi_header else 0
            if palmdoc_header and mobi_header:
                try:
                    html_content = self._extract_text_content(
                        data, records, palmdoc_header, mobi_header
                    )
                    if html_content:
                        html_order = self._extract_image_order_from_html(html_content)
                        self.logger.debug(f"Found {len(html_order)} images in HTML reading order")
                except Exception as e:
                    self.logger.warning(f"Could not extract HTML order: {e}")

            image_records = self._get_image_records_in_order(
                data, records, html_order, first_image_index
            )
            self.logger.info(f"Found {len(image_records)} images in MOBI file")

            if dry_run:
                for idx, record_data in image_records:
                    img_hash = self.hash_bytes_sha256(record_data)
                    should_skip, reason = self.should_skip_image(record_data, img_hash)
                    if not should_skip:
                        stats.saved += 1
                    elif reason == "ignored_hash":
                        stats.ignored += 1
                    elif reason == "duplicate":
                        stats.duplicates += 1
                    elif reason == "too_small":
                        stats.filtered_by_size += 1
                return stats

            self.prepare_output_directory(output_dir)

            for idx, record_data in image_records:
                img_hash = self.hash_bytes_sha256(record_data)
                should_skip, reason = self.should_skip_image(record_data, img_hash)

                if should_skip:
                    if reason == "ignored_hash":
                        stats.ignored += 1
                    elif reason == "duplicate":
                        stats.duplicates += 1
                    elif reason == "too_small":
                        stats.filtered_by_size += 1
                    continue

                ext = self._get_image_extension(record_data)
                self.save_image(record_data, output_dir, stats.saved, ext)
                stats.saved += 1

        except (InvalidFileError, CorruptedFileError):
            raise
        except Exception as e:
            raise ExtractionError(file_path, str(e))

        return stats

    def extract_images_from_mobi(
        self, mobi_path: str, output_dir: str
    ) -> Dict[str, int]:
        stats = self.extract_images(mobi_path, output_dir)
        return stats.to_dict()

    def extract_from_directory(
        self,
        directory: str,
        recursive: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, ExtractionStats]:
        return super().extract_from_directory(directory, recursive, dry_run)
