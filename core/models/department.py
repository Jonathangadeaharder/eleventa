"""
Department model for organizing products.

This module defines the Department class used for categorizing products.
"""


class Department:
    """
    Department model for product categorization.
    
    Attributes:
        id (int): Unique identifier for the department.
        name (str): Name of the department.
        description (str, optional): Description of the department.
    """
    
    def __init__(self, id=None, name=None, description=None):
        """
        Initialize a new Department.
        
        Args:
            id (int, optional): Unique identifier for the department.
            name (str, optional): Name of the department.
            description (str, optional): Description of the department.
        """
        self.id = id
        self.name = name
        self.description = description 