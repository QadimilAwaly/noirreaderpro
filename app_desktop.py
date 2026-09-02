"""
Noir Reader Pro — Desktop Application Launcher.
Menjalankan server FastAPI di latar belakang dan membuka antarmuka desktop native (pywebview)
atau peramban web default sebagai fallback.
"""
from __future__ import annotations

import os
import sys
import time
import socket
import threading
import webbrowser
from pathlib import Path

import uvicorn
from core.config import DEFAULT_HOST, DEFAULT_PORT
from main import app


def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def start_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Jalankan uvicorn server."""
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )


def wait_for_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 6.0) -> bool:
    """Tunggu hingga server siap menerima koneksi."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(host, port):
            return True
        time.sleep(0.15)
    return False


def main():
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    url = f"http://{host}:{port}"

    # Jalankan server FastAPI di daemon thread jika belum aktif
    if not is_port_in_use(host, port):
        server_thread = threading.Thread(target=start_server, args=(host, port), daemon=True)
        server_thread.start()
        wait_for_server(host, port)

    # Coba buka menggunakan pywebview (jendela desktop native tanpa address bar)
    try:
        import webview
        webview.create_window(
            title="Noir Reader Pro",
            url=url,
            width=1120,
            height=780,
            min_size=(680, 500),
            text_select=True,
            confirm_close=False,
        )
        webview.start()
    except Exception:
        # Fallback jika pywebview tidak tersedia: buka di browser default
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
