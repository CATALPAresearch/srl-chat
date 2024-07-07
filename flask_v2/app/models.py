from typing import List, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db


class Language(db.Model):
    __tablename__ = "languages"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    lang_code: so.Mapped[str] = so.mapped_column(sa.String(2), index=True, unique=True)
    contexts: so.Mapped[List["Context"]] = so.relationship()
    strategies: so.Mapped[List["Strategy"]] = so.relationship()


class User(db.Model):
    __tablename__ = "users"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    client: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    language_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Language.id))
    message_history: so.Mapped[Optional[str]] = so.mapped_column(sa.String())
    interview_answers: so.Mapped[List["InterviewAnswer"]] = so.relationship(back_populates="user")
    conversation_state: so.Mapped["ConversationState"] = so.relationship(back_populates="user")


class Context(db.Model):
    __tablename__ = "contexts"
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    context: so.Mapped[str] = so.mapped_column(sa.String())
    language_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Language.id))


class ConversationState(db.Model):
    __tablename__ = "state"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(User.id))
    user: so.Mapped["User"] = so.relationship(back_populates="conversation_state")
    interview_completed: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=0)
    completed_contexts: so.Mapped[List[int]] = so.mapped_column(sa.ForeignKey(Context.id), nullable=True)


class Strategy(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    strategy: so.Mapped[str] = so.mapped_column(sa.String())
    description: so.Mapped[str] = so.mapped_column(sa.String())
    language_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Language.id))


class InterviewAnswer(db.Model):
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(User.id))
    user: so.Mapped["User"] = so.relationship(back_populates="interview_answers")
    context: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id))
    strategies: so.Mapped[List[int]] = so.mapped_column(sa.ForeignKey(Strategy.id))
