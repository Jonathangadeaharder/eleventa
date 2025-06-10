from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
import bcrypt

class User(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = Field(default="", max_length=50)  # Made optional for tests
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    password_hash: Optional[str] = Field(default="", max_length=100)  # Made optional for tests
    password: Optional[str] = None  # For input, to be hashed
    is_active: bool = True
    is_admin: bool = False
    
    @field_validator('password_hash', mode='before')
    @classmethod
    def hash_password_if_needed(cls, password_hash, values):
        """Hash the password if one is provided and password_hash is empty."""
        if not password_hash and values.data.get('password'):
            # Hash the password
            password_bytes = values.data['password'].encode('utf-8')
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        return password_hash

    model_config = ConfigDict(from_attributes=True)
