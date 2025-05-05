from sqlalchemy import Column, Integer, String, Boolean
from core.database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    email = Column(String(100))
    is_admin = Column(Boolean, default=False)
    
    # Password attribute (not stored in database, used for setting password_hash)
    _password = None
    
    @property
    def password(self):
        return self._password
        
    @password.setter
    def password(self, value):
        self._password = value
    
    def __init__(self, username=None, password=None, password_hash=None, 
                 is_active=True, email=None, is_admin=False, id=None, role=None):
        """
        Initialize a new user.
        
        Args:
            username (str): The username for this user
            password (str, optional): Plain text password - will be hashed for storage
            password_hash (str, optional): Pre-hashed password value (from DB)
            is_active (bool, optional): Whether the user is active
            email (str, optional): User's email address
            is_admin (bool, optional): Whether the user has admin privileges
            id (int, optional): The user ID
            role (str, optional): User role ('admin' or other) - legacy parameter
        """
        self.username = username
        
        # Store password but don't set password_hash directly
        if password:
            self.password = password
        elif password_hash:
            self.password_hash = password_hash
            
        self.is_active = is_active
        self.email = email
        
        # Handle either is_admin or role parameter
        if role == 'admin':
            self.is_admin = True
        else:
            self.is_admin = is_admin
            
        if id is not None:
            self.id = id
