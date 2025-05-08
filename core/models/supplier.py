from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class Supplier(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., max_length=100)
    contact_person: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20) # Consider specific validation if needed
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    cuit: Optional[str] = Field(default=None, max_length=20)  # Clave Única de Identificación Tributaria (Argentina)
    notes: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = True
    
    class Config:
        from_attributes = True # Updated from orm_mode for Pydantic v2
