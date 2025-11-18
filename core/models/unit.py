from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import datetime


class Unit(BaseModel):
    """Model for custom unit categories."""

    id: Optional[int] = None
    name: str = Field(
        ..., max_length=50, description="Name of the unit (e.g., 'Saco', 'Bidón')"
    )
    abbreviation: Optional[str] = Field(
        default=None, max_length=10, description="Short abbreviation for the unit"
    )
    description: Optional[str] = Field(
        default=None, max_length=255, description="Description of the unit"
    )
    is_active: bool = Field(default=True, description="Whether the unit is active")
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)

    def __str__(self):
        return self.name
