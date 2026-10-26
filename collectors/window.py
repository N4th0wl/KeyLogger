"""
collectors/window.py
Deteksi judul window / aplikasi yang sedang aktif.
Mendukung Windows (win32gui) dan Linux (xdotool / Xlib).
"""

import platform
import logging

logger = logging.getLogger(__name__)

_OS = platform.system()


def get_active_window() -> str:
    """
    Kembalikan judul window yang sedang aktif sebagai string.
    Kembalikan string kosong jika tidak bisa dideteksi.
    """
    try:
        if _OS == "Windows":
            return _get_active_window_windows()
        elif _OS == "Linux":
            return _get_active_window_linux()
        else:
            return ""
    except Exception as exc:
        logger.debug("get_active_window error: %s", exc)
        return ""


# ── Windows ───────────────────────────────────────────────────────────────────
def _get_active_window_windows() -> str:
    import win32gui  # type: ignore
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)


# ── Linux ─────────────────────────────────────────────────────────────────────
def _get_active_window_linux() -> str:
    import subprocess
    result = subprocess.run(
        ["xdotool", "getactivewindow", "getwindowname"],
        capture_output=True,
        text=True,
        timeout=2,
    )
    return result.stdout.strip()
