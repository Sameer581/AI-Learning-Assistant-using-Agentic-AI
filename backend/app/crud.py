from sqlalchemy.orm import Session
from . import models,schemas

def create_message(db: Session, message: schemas.MessageCreate, user_id: int):
    db_message = models.Message(
        content = message.content,
        sender_type = message.sender_type,
        owner_id = user_id
    )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

"""
crud.py (The Database Worker) 🛠️: This file separates your database logic from your API logic. The create_message function takes a database session and a Pydantic schema, converts it into a SQLAlchemy model, and saves it. This keeps your main.py file cleaner.
"""


