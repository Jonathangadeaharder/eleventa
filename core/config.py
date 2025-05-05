class Settings:
    DATABASE_URL = "sqlite:///./test.db"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

settings = Settings()
config = settings
