"""
Department model for organizing products.

This module defines the Department class used for categorizing products.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class Department(BaseModel):
    """
    Department domain model for product categorization.
    
    Attributes:
        id (Optional[int]): Unique identifier for the department.
        name (str): Name of the department.
        description (Optional[str]): Description of the department.
    """
    id: Optional[int] = None
    name: Optional[str] = Field(default="", max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(from_attributes=True)
