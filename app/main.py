from fastapi import FastAPI
from sqlalchemy import text

from app.database import SessionLocal
from app.services import (
    get_or_create_user,
    create_conversation,
    save_message,
    get_recent_messages,
)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "API rodando"}


@app.get("/db-test")
def db_test():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {"database": "connected", "result": result}
    finally:
        db.close()


@app.get("/test-flow")
def test_flow():
    db = SessionLocal()
    try:
        user = get_or_create_user(db, external_id="matheus_001", name="Matheus")
        conversation = create_conversation(db, user.id, channel="web")

        save_message(db, conversation.id, "user", "Oi, quero revisar cardiologia.")
        save_message(db, conversation.id, "assistant", "Claro. Qual tema de cardiologia você quer revisar?")

        messages = get_recent_messages(db, conversation.id)

        return {
            "user_id": str(user.id),
            "conversation_id": str(conversation.id),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content
                }
                for m in messages
            ]
        }
    finally:
        db.close()