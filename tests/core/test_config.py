import os
import pytest
from config import config


def test_config_defaults():
    """Test that config has default values."""
    assert config.store_name == "Mi Tienda"
    assert config.store_address == "Calle Falsa 123"
    assert config.store_cuit == "30-12345678-9"
    assert config.store_iva_condition == "Responsable Inscripto"
    assert config.store_phone == ""


def test_config_backward_compatibility():
    """Test that uppercase properties work for backward compatibility."""
    assert config.STORE_NAME == config.store_name
    assert config.STORE_ADDRESS == config.store_address
    assert config.STORE_CUIT == config.store_cuit
    assert config.STORE_IVA_CONDITION == config.store_iva_condition
    assert config.STORE_PHONE == config.store_phone
    assert config.PDF_OUTPUT_DIR == config.pdf_output_dir


def test_config_env_override(monkeypatch):
    """Test that environment variables override defaults."""
    # Set environment variable
    monkeypatch.setenv("STORE_NAME", "Test Store from Env")
    
    # Create new config instance to pick up env var
    from config import Config
    test_config = Config()
    
    assert test_config.store_name == "Test Store from Env"
    assert test_config.STORE_NAME == "Test Store from Env"
