import pytest
from pathlib import Path
import core.config
import core.paths
import api.router_settings


@pytest.fixture(autouse=True)
def isolate_test_configs(tmp_path: Path, monkeypatch):
    """
    Otomatis isolasi semua file konfigurasi (device_config, config, settings)
    ke temporary directory agar eksekusi test TIDAK PERNAH mencemari file di project root.
    """
    test_device_cfg = tmp_path / "test_device_config.json"
    test_config_json = tmp_path / "test_config.json"
    test_settings_json = tmp_path / "test_reader_settings.json"

    # Default kosong
    test_device_cfg.write_text("{}", encoding="utf-8")
    test_config_json.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", test_device_cfg)
    monkeypatch.setattr(core.config, "CONFIG_JSON", test_config_json)
    monkeypatch.setattr(api.router_settings, "SETTINGS_JSON", test_settings_json)
