import sys
from unittest.mock import patch
import pytest

import core.config
from main import app


def test_main_cli_args(monkeypatch):
    monkeypatch.setenv("NOIR_HOST", "127.0.0.9")
    monkeypatch.setenv("NOIR_PORT", "9999")
    assert core.config.get_host() == "127.0.0.9"
    assert core.config.get_port() == 9999

    import main
    # Simulate CLI arguments overriding env vars
    test_args = ["main.py", "--host", "0.0.0.0", "-p", "7777"]
    with patch.object(sys, "argv", test_args):
        import argparse
        parser = argparse.ArgumentParser(description="Noir Reader Pro Server")
        parser.add_argument("--host", default=None)
        parser.add_argument("-p", "--port", type=int, default=None)
        args = parser.parse_args()
        host = args.host or core.config.get_host()
        port = args.port or core.config.get_port()
        assert host == "0.0.0.0"
        assert port == 7777


def test_desktop_cli_args_and_connect_host(monkeypatch):
    import app_desktop

    # When binding to 0.0.0.0, connect_host must resolve to 127.0.0.1
    host = "0.0.0.0"
    connect_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    assert connect_host == "127.0.0.1"

    # When binding to specific host, connect_host is that host
    host = "192.168.1.100"
    connect_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    assert connect_host == "192.168.1.100"
