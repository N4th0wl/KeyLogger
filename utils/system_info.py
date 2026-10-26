"""
utils/system_info.py
Kumpulkan informasi sistem dan jaringan perangkat.
"""

import platform
import socket
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_system_info() -> str:
    """
    Kembalikan string yang berisi informasi sistem lengkap:
    hostname, IP, OS, prosesor, user, waktu startup.
    """
    lines = ["```", "=== SYSTEM INFO ==="]

    def safe(label: str, value_fn):
        try:
            lines.append(f"{label:<18}: {value_fn()}")
        except Exception as exc:
            lines.append(f"{label:<18}: [error: {exc}]")

    safe("Timestamp",    lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    safe("Hostname",     socket.gethostname)
    safe("IP Address",   lambda: socket.gethostbyname(socket.gethostname()))
    safe("OS",           lambda: f"{platform.system()} {platform.release()} ({platform.version()})")
    safe("Machine",      platform.machine)
    safe("Processor",    platform.processor)
    safe("Python",       platform.python_version)
    safe("Username",     lambda: os.environ.get("USERNAME") or os.environ.get("USER") or "unknown")

    lines.append("===================")
    lines.append("```")
    return "\n".join(lines)
