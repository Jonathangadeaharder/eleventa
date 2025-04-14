from dataclasses import dataclass, field

@dataclass
class User:
    """Represents an application user."""
    id: int | None = field(default=None, kw_only=True)
    username: str
    password_hash: str # Store hashed passwords only!
    is_active: bool = True
