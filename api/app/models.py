from typing import List, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
import datetime
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
    evaluation: so.Mapped["StrategyEvaluation"] = so.relationship(
        back_populates="user",
        cascade="all, delete")
    strategies: so.Mapped[List["UserStrategy"]] = so.relationship(
        back_populates="user",
        cascade="all, delete")
    interview_answers: so.Mapped[List["InterviewAnswer"]] = so.relationship(
        back_populates="user",
        cascade="all, delete")
    conversation_state: so.Mapped["ConversationState"] = so.relationship(
        back_populates="user",
        cascade="all, delete")
    llm_responses: so.Mapped[List["LlmResponse"]] = so.relationship(
        back_populates="user",
        cascade="all, delete")
    __table_args__ = (sa.UniqueConstraint('id', 'client', name='_user_client_uc'),)


class Context(db.Model):
    __tablename__ = "contexts"
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    context: so.Mapped[str] = so.mapped_column(sa.String())
    language_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Language.id))


class Strategy(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    strategy: so.Mapped[str] = so.mapped_column(sa.String())
    description: so.Mapped[str] = so.mapped_column(sa.String())
    language_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Language.id))


class ConversationState(db.Model):
    __tablename__ = "state"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(back_populates="conversation_state", cascade="all, delete")
    interview_completed: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=0)
    current_turn: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    current_context: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id), nullable=True)
    strategy_for_frequency: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Strategy.id), nullable=True)
    completed_contexts: so.Mapped[List["ConversationCompletedContexts"]] = so.relationship(
        back_populates="conversation",
        cascade="all, delete")
    most_recent_response: so.Mapped[str] = so.mapped_column(sa.String(32),
                                                            sa.CheckConstraint(
        "most_recent_response IN ('getstrategies', 'probe', 'frequency', 'complete')", name="response_check"),
                                                            nullable=True)
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client]), {})


class ConversationCompletedContexts(db.Model):
    __tablename__ = "conversation_completed_contexts"
    conversation_id: so.Mapped["ConversationState"] = so.mapped_column(
        sa.ForeignKey(ConversationState.id, ondelete="CASCADE"), primary_key=True)
    completed_context_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id), primary_key=True)
    conversation: so.Mapped["ConversationState"] = so.relationship(
        back_populates="completed_contexts", cascade="all, delete")


class InterviewAnswer(db.Model):
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(back_populates="interview_answers", cascade="all, delete")
    context: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id))
    turn: so.Mapped[int] = so.mapped_column(sa.Integer)
    message: so.Mapped[str] = so.mapped_column(sa.String())
    strategies: so.Mapped[List["UserStrategy"]] = so.relationship(
        back_populates="interview_answer",
        cascade="all, delete")
    message_time: so.Mapped[datetime.datetime] = so.mapped_column(
        nullable=False, server_default=sa.func.CURRENT_TIMESTAMP()
    )
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client]),)


class UserStrategy(db.Model):
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(
        back_populates="strategies", cascade="all, delete")
    interview_answer_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(InterviewAnswer.id))
    interview_answer: so.Mapped["InterviewAnswer"] = so.relationship(
        back_populates="strategies", cascade="all, delete")
    context: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id))
    strategy: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Strategy.id))
    frequency: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client]), {})


class LlmResponse(db.Model):
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(back_populates="llm_responses", cascade="all, delete")
    message: so.Mapped[str] = so.mapped_column(sa.String())
    turn: so.Mapped[int] = so.mapped_column(sa.Integer)
    message_time: so.Mapped[datetime.datetime] = so.mapped_column(
        nullable=False, server_default=sa.func.CURRENT_TIMESTAMP()
    )
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client]), {})


class StrategyEvaluation(db.Model):
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(back_populates="evaluation", cascade="all, delete")
    strategy: so.Mapped["strategy"] = so.mapped_column(sa.ForeignKey(Strategy.id))
    SU: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=0)
    SF: so.Mapped[float] = so.mapped_column(sa.Float())
    SC: so.Mapped[float] = so.mapped_column(sa.Float())
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client]), {})