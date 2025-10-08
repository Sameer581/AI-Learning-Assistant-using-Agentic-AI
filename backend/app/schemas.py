from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    content: str
    sender_type: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    owner_id: int
    timestamp: datetime

class Config:
    orm_mode = True


"""schemas.py (The Data Rules) 📜: Pydantic schemas enforce data validation. This ensures that any data sent to your API has the correct fields (content, sender_type) and data types (str). It acts like a bouncer, making sure only valid data gets in.

"""