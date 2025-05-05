"""
Department model for organizing products.

This module defines the Department class used for categorizing products.
"""


from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from core.database import Base

class Department(Base):
    """
    Department model for product categorization.
    
    Attributes:
        id (int): Unique identifier for the department.
        name (str): Name of the department.
        description (str, optional): Description of the department.
    """
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    
    # Add the relationship to fix the bidirectional reference
    products = relationship("Product", back_populates="department")

    def __init__(self, name="", description=None, id=None):
        """
        Initialize a new Department.
        
        Args:
            name (str, optional): Name of the department. Defaults to an empty string.
            description (str, optional): Description of the department.
            id (int, optional): The department ID (typically set by the database).
        """
        self.name = name
        self.description = description
        if id is not None:
            self.id = id
