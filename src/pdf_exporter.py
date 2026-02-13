"""PDF export support for extracted image directories."""

import os
from typing import List


def export_directory_as_pdf(output_dir: str) -> str:
    """Export directory images into one PDF.

    :param output_dir: Source directory with extracted images.
    :return: Generated PDF path.
    :raises RuntimeError: When Pillow is unavailable.
    :raises ValueError: When no image files are available.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("PDF export requires Pillow (pip install Pillow).") from exc

    valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
    image_paths: List[str] = []
    for name in sorted(os.listdir(output_dir)):
        path = os.path.join(output_dir, name)
        if os.path.isfile(path) and os.path.splitext(name)[1].lower() in valid_exts:
            image_paths.append(path)

    if not image_paths:
        raise ValueError("No supported images available for PDF export.")

    pages = []
    for path in image_paths:
        img = Image.open(path)
        pages.append(img.convert("RGB"))

    pdf_path = f"{output_dir}.pdf"
    first, rest = pages[0], pages[1:]
    first.save(pdf_path, save_all=True, append_images=rest)
    for page in pages:
        page.close()
    return pdf_path
