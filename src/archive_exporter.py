"""Archive exporters for extracted image directories."""

import os
import zipfile


def export_directory_as_comic_archive(output_dir: str, archive_format: str) -> str:
    """Export output directory into CBZ or CBR file.

    :param output_dir: Source directory with extracted images.
    :param archive_format: ``cbz`` or ``cbr``.
    :return: Archive file path.
    :raises ValueError: When archive format is unsupported.
    """
    normalized = archive_format.lower()
    if normalized not in {"cbz", "cbr"}:
        raise ValueError(f"Unsupported archive format: {archive_format}")

    archive_path = f"{output_dir}.{normalized}"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        files = sorted(os.listdir(output_dir))
        for name in files:
            file_path = os.path.join(output_dir, name)
            if os.path.isfile(file_path):
                zipf.write(file_path, arcname=name)
    return archive_path
