"""
sender/discord.py
Mengirim pesan teks dan/atau file attachment ke Discord via Webhook.
"""

import logging
from io import BytesIO
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Discord membatasi isi pesan maksimal 2000 karakter
_MAX_MSG_LEN = 1900
# Timeout request HTTP (detik)
_TIMEOUT = 15


class DiscordSender:
    """
    Wrapper ringan di atas Discord Webhook API.

    Parameter:
        webhook_url: URL webhook Discord lengkap
    """

    def __init__(self, webhook_url: str) -> None:
        if not webhook_url or "YOUR_WEBHOOK" in webhook_url:
            raise ValueError(
                "DISCORD_WEBHOOK_URL belum dikonfigurasi di file .env Anda."
            )
        self._url = webhook_url

    # ── Public API ─────────────────────────────────────────────────────────────

    def send_text(self, content: str) -> bool:
        """
        Kirim pesan teks ke channel Discord.
        Jika teks > 1900 karakter, otomatis dipecah menjadi beberapa pesan.
        Kembalikan True jika semua bagian berhasil dikirim.
        """
        chunks = self._split(content)
        success = True
        for chunk in chunks:
            ok = self._post_json({"content": chunk})
            if not ok:
                success = False
        return success

    def send_file(
        self,
        data: bytes,
        filename: str,
        caption: Optional[str] = None,
    ) -> bool:
        """
        Kirim file (bytes) sebagai attachment ke channel Discord.
        Kembalikan True jika berhasil.
        """
        payload = {}
        if caption:
            payload["content"] = caption[:_MAX_MSG_LEN]

        files = {"file": (filename, BytesIO(data), "application/octet-stream")}
        return self._post_multipart(payload, files)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _post_json(self, payload: dict) -> bool:
        try:
            resp = requests.post(self._url, json=payload, timeout=_TIMEOUT)
            resp.raise_for_status()
            return True
        except requests.RequestException as exc:
            logger.error("Discord send_text gagal: %s", exc)
            return False

    def _post_multipart(self, payload: dict, files: dict) -> bool:
        try:
            resp = requests.post(
                self._url, data=payload, files=files, timeout=_TIMEOUT
            )
            resp.raise_for_status()
            return True
        except requests.RequestException as exc:
            logger.error("Discord send_file gagal: %s", exc)
            return False

    @staticmethod
    def _split(text: str) -> list[str]:
        """Pecah teks panjang menjadi chunk ≤ _MAX_MSG_LEN karakter."""
        if not text:
            return []
        chunks = []
        while text:
            chunks.append(text[:_MAX_MSG_LEN])
            text = text[_MAX_MSG_LEN:]
        return chunks
