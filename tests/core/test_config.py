import os
import json
import pytest
import tempfile
import config
from config import Config


def test_load_defaults_when_no_file(tmp_path, monkeypatch):
    temp_file = tmp_path / "nonexistent.json"
    # Point to a non-existent file
    monkeypatch.setattr(config, "CONFIG_FILE", str(temp_file))
    # Ensure no file exists
    if temp_file.exists():
        temp_file.unlink()
    # Use a sentinel to check unchanged default
    prev = Config.STORE_NAME
    result = Config.load()
    assert result is False
    assert Config.STORE_NAME == prev


def test_save_and_load_cycle(tmp_path, monkeypatch):
    temp_file = tmp_path / "app_config.json"
    monkeypatch.setattr(config, "CONFIG_FILE", str(temp_file))
    # Set custom values
    Config.STORE_NAME = "Test Store"
    Config.STORE_ADDRESS = "123 Test Ave"
    # Save should succeed
    assert Config.save() is True
    # File created
    assert temp_file.exists()
    data = json.loads(temp_file.read_text(encoding='utf-8'))
    assert data.get("STORE_NAME") == "Test Store"
    assert data.get("STORE_ADDRESS") == "123 Test Ave"
    # Modify file externally
    data["STORE_NAME"] = "Loaded Store"
    temp_file.write_text(json.dumps(data), encoding='utf-8')
    # Load should pick up change
    assert Config.load() is True
    assert Config.STORE_NAME == "Loaded Store"
