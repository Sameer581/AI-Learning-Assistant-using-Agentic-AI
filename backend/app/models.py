from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="owner")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    sender_type = Column(String, nullable=False) 
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="messages")

"""
models.py:

class User(Base) & class Message(Base): These Python classes are blueprints for your database tables.

__tablename__ = "...": This explicitly names the table in your PostgreSQL database.

Column(...): Each Column represents a column in the database table, defining its data type (Integer, String, Text, etc.) and constraints (primary_key=True, unique=True).

relationship(...): This creates a link between the User and Message tables, telling SQLAlchemy that one user can have many messages.2"""


