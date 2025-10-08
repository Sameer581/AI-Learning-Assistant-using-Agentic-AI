from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage
import json
import sys

from . import models, schemas, crud
from .database import SessionLocal, engine
from .agents import agent_graph

# Initialize database
models.Base.metadata.create_all(bind=engine)

# Initialize app
app = FastAPI()

# CORS setup for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React local dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Stream AI responses as JSON
async def stream_ai_response(message_content: str, db: Session, user_id: int):
    full_ai_response = ""

    async for step in agent_graph.astream({"messages": [HumanMessage(content=message_content)]}):
        print("DEBUG: Step from LangGraph:", step)

        # Loop through each agent’s step output
        for agent_key, agent_output in step.items():
            if isinstance(agent_output, dict) and "messages" in agent_output:
                for msg in agent_output["messages"]:
                    if isinstance(msg, AIMessage) and msg.content:
                        chunk = msg.content
                        print("DEBUG: Yielding chunk:", chunk)
                        sys.stdout.flush()

                        # ✅ Send as JSON for React compatibility
                        json_data = json.dumps({
                            "choices": [
                                {"delta": {"content": chunk}}
                            ]
                        })
                        yield f"data: {json_data}\n\n"
                        full_ai_response += chunk

    # Indicate stream completion
    yield "data: [DONE]\n\n"

    print("Finished streaming, full response:", full_ai_response)

    # Save complete AI message in DB
    if full_ai_response:
        ai_message_schema = schemas.MessageCreate(
            content=full_ai_response,
            sender_type='ai'
        )
        crud.create_message(db=db, message=ai_message_schema, user_id=user_id)


# POST endpoint for chat messages
@app.post("/api/chat/")
async def handle_chat_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    user_id = 1  # Static for now; extendable later
    crud.create_message(db=db, message=message, user_id=user_id)
    return StreamingResponse(
        stream_ai_response(message.content, db, user_id),
        media_type="text/event-stream"
    )
