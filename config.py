import os
from typing import Optional
from pathlib import Path
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

def get_app_data_dir() -> Path:
    """
    Determines the appropriate user-specific data directory for the application.
    """
    # For Windows, use %LOCALAPPDATA%
    if os.name == 'nt':
        app_data_path = Path(os.environ.get('LOCALAPPDATA', ''))
    # For other OS (macOS, Linux), use a standard dot-folder in the home directory
    else:
        app_data_path = Path.home()

    # Create the application-specific directory
    app_dir = app_data_path / 'Eleventa'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

# Define the path for the SQLite database
APP_DATA_DIR = get_app_data_dir()
DATABASE_PATH = APP_DATA_DIR / 'eleventa.db'

# Database configuration
if TEST_MODE:
    DATABASE_URL = "sqlite:///:memory:"
else:
    DATABASE_URL = f"sqlite:///{DATABASE_PATH.resolve()}"

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

    def save_to_env_file(self):
        """Save current configuration to .env file."""
        env_path = os.path.join(BASE_DIR, '.env')
        env_content = f"""# Eleventa Configuration
# Store Information
STORE_NAME={self.store_name}
STORE_ADDRESS={self.store_address}
STORE_CUIT={self.store_cuit}
STORE_IVA_CONDITION={self.store_iva_condition}
STORE_PHONE={self.store_phone}

# Directories
PDF_OUTPUT_DIR={self.pdf_output_dir}

# Optional Settings
{f'DEFAULT_PRINTER={self.default_printer}' if self.default_printer else '# DEFAULT_PRINTER='}

# Test Mode (for development)
TEST_MODE=false
"""
        
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            return True
        except Exception as e:
            print(f"Error saving configuration to .env file: {e}")
            return False

# Create global config instance
config = Config()

# Make database URL accessible directly