import os
from typing import Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseSettings
    SettingsConfigDict = None

# Base directory for the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Check if we're in test mode
TEST_MODE = os.environ.get('TEST_MODE', 'false').lower() == 'true'

# Database configuration
if TEST_MODE:
    DATABASE_URL = "sqlite:///:memory:"
else:
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'eleventa_clone.db')}"

# Application Settings using Pydantic BaseSettings
class Config(BaseSettings):
    """Application configuration with support for .env files and environment variables."""
    
    # Store information
    store_name: str = Field(default="Mi Tienda")
    store_address: str = Field(default="Calle Falsa 123")
    store_cuit: str = Field(default="30-12345678-9")
    store_iva_condition: str = Field(default="Responsable Inscripto")
    store_phone: str = Field(default="")
    
    # Directories
    pdf_output_dir: str = Field(default_factory=lambda: os.path.join(BASE_DIR, 'pdfs'))
    
    # Optional printer settings
    default_printer: Optional[str] = Field(default=None)
    
    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            env_prefix=""
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
        
    # Backward compatibility properties for uppercase access
    @property
    def STORE_NAME(self) -> str:
        return self.store_name
        
    @property
    def STORE_ADDRESS(self) -> str:
        return self.store_address
        
    @property
    def STORE_CUIT(self) -> str:
        return self.store_cuit
        
    @property
    def STORE_IVA_CONDITION(self) -> str:
        return self.store_iva_condition
        
    @property
    def STORE_PHONE(self) -> str:
        return self.store_phone
        
    @property
    def PDF_OUTPUT_DIR(self) -> str:
        return self.pdf_output_dir

# Create global config instance
config = Config()

# Make database URL accessible directly