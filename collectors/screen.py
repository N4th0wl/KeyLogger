"""
collectors/screen.py
Mengambil screenshot layar dan mengembalikannya sebagai bytes PNG.
"""

import io
import logging

from PIL import ImageGrab

logger = logging.getLogger(__name__)


def capture_screenshot() -> bytes:
    """
    Ambil screenshot seluruh layar.
    Kembalikan bytes gambar dalam format PNG.
    Raise RuntimeError jika gagal.
    """
    try:
        img = ImageGrab.grab(all_screens=True)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as exc:
        logger.error("Screenshot gagal: %s", exc)
        raise RuntimeError(f"Screenshot gagal: {exc}") from exc
