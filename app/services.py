from sqlalchemy.orm import Session
from sqlalchemy import desc, text

from app.models import User, Conversation, Message


def get_or_create_user(db: Session, external_id: str, name: str | None = None) -> User:
    user = db.query(User).filter(User.external_id == external_id).first()

    if user:
        return user

    user = User(
        external_id=external_id,
        name=name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_conversation(db: Session, user_id, channel: str = "web") -> Conversation:
    conversation = Conversation(
        user_id=user_id,
        channel=channel
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def save_message(db: Session, conversation_id, role: str, content: str) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_recent_messages(db: Session, conversation_id, limit: int = 10) -> list[Message]:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(desc(Message.created_at))
        .limit(limit)
        .all()
    )

    return list(reversed(messages))