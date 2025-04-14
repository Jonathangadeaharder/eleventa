import os
import json

# Base directory for the application
# Should be the directory containing config.py if config.py is in the root
# Or the parent directory if config.py is in a subdirectory.
# Assuming config.py is in the project root, it should be:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database configuration (now uses corrected BASE_DIR)
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'eleventa_clone.db')}"

# Path to configuration file
CONFIG_FILE = os.path.join(BASE_DIR, 'app_config.json')

# Application Settings
class Config:
    STORE_NAME = "Mi Tienda"
    STORE_ADDRESS = "Calle Falsa 123"
    STORE_CUIT = "30-12345678-9"
    STORE_IVA_CONDITION = "Responsable Inscripto"
    STORE_PHONE = ""

    # Add other config variables here
    # Example: DEFAULT_PRINTER = ""

    @classmethod
    def load(cls):
        """Load configuration from JSON file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Update class attributes from loaded data
                for key, value in config_data.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)
                print(f"Configuration loaded from {CONFIG_FILE}")
                return True
            except Exception as e:
                print(f"Error loading configuration: {e}")
        else:
            print(f"Configuration file not found. Using defaults.")
        return False

    @classmethod
    def save(cls):
        """Save configuration to JSON file"""
        try:
            # Create dictionary from class attributes (only uppercase ones)
            config_data = {
                key: value for key, value in cls.__dict__.items() 
                if key.isupper() and not key.startswith('__')
            }
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            print(f"Configuration saved to {CONFIG_FILE}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

# Try to load configuration on import
Config.load()

# Make database URL accessible directly 