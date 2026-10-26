"""
utils/cache.py
Offline queue — menyimpan log yang gagal dikirim ke disk (terenkripsi)
dan mencoba mengirim ulang saat koneksi pulih.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from utils.crypto import encrypt, decrypt

logger = logging.getLogger(__name__)

# Direktori tempat menyimpan file cache
CACHE_DIR = Path(__file__).parent.parent / ".cache"


class OfflineCache:
    """
    Menyimpan payload gagal sebagai file .bin di direktori .cache/.
    Setiap entry = satu file dengan timestamp sebagai nama.

    Parameter:
        cipher: instance Fernet atau None (tidak dienkripsi)
    """

    def __init__(self, cipher=None) -> None:
        self._cipher = cipher
        CACHE_DIR.mkdir(exist_ok=True)
        logger.info("OfflineCache init. Cache dir: %s", CACHE_DIR)

    # ── Public API ─────────────────────────────────────────────────────────────

    def push(self, payload: str) -> None:
        """Simpan payload teks ke disk."""
        try:
            raw = payload.encode("utf-8")
            data = encrypt(raw, self._cipher)
            fname = CACHE_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.bin"
            fname.write_bytes(data)
            logger.info("Cache: disimpan → %s", fname.name)
        except Exception as exc:
            logger.error("Cache push error: %s", exc)

    def flush(self, send_fn: Callable[[str], bool]) -> None:
        """
        Coba kirim semua entri cache yang tersimpan menggunakan send_fn.
        send_fn(payload: str) → True jika berhasil, False jika gagal.
        Hapus file hanya jika berhasil dikirim.
        """
        files = sorted(CACHE_DIR.glob("*.bin"))
        if not files:
            return

        logger.info("Cache: mencoba flush %d entri...", len(files))
        for fpath in files:
            try:
                raw = fpath.read_bytes()
                payload = decrypt(raw, self._cipher).decode("utf-8")
                if send_fn(payload):
                    fpath.unlink()
                    logger.info("Cache: berhasil dikirim & dihapus → %s", fpath.name)
                else:
                    logger.warning("Cache: masih gagal dikirim → %s", fpath.name)
            except Exception as exc:
                logger.error("Cache flush error pada %s: %s", fpath.name, exc)

    def count(self) -> int:
        """Jumlah entri cache yang belum terkirim."""
        return len(list(CACHE_DIR.glob("*.bin")))
