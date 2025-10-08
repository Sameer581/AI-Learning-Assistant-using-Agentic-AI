import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit= False, autoflush=False, bind=engine)
Base = declarative_base()

"""
database.py:

create_engine(DATABASE_URL): This is the main entry point to your database. It takes the connection string from your .env file (e.g., "postgresql://user:password@host:port/dbname") and establishes a connection pool.

sessionmaker: This creates a class SessionLocal that will be used to create individual database sessions. Think of a session as a single conversation with your database.

declarative_base(): This creates a Base class that your table models (User, Message) will inherit from. It's how SQLAlchemy knows that these classes correspond to tables in the database.

"""

