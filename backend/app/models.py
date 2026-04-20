import uuid
from typing import List, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from pgvector.sqlalchemy import Vector
import numpy as np
import datetime
from app import db


class Language(db.Model):
    __tablename__ = "languages"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    lang_code: so.Mapped[str] = so.mapped_column(sa.String(2), index=True, unique=True)
    contexts: so.Mapped[List["Context"]] = so.relationship()
    strategies: so.Mapped[List["StrategyTranslation"]] = so.relationship()
    strategy_vectors: so.Mapped[List["StrategyVector"]] = so.relationship()


class User(db.Model):
    __tablename__ = "users"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    client: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    language_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Language.id))
    study_subject: so.Mapped[Optional[str]] = so.mapped_column(sa.String())
    context_id: so.Mapped[str] = so.mapped_column(sa.String(256), server_default="0", default="0")
    context_title: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    evaluation: so.Mapped[List["StrategyEvaluation"]] = so.relationship(
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
    __tablename__ = "strategy"
    id: so.Mapped[str] = so.mapped_column(sa.String(), primary_key=True)


class StrategyTranslation(db.Model):
    __tablename__ = "strategy_translation"
    id: so.Mapped[str] = so.mapped_column(sa.String(), primary_key=True)
    strategy: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Strategy.id))
    name: so.Mapped[str] = so.mapped_column(sa.String())
    description: so.Mapped[str] = so.mapped_column(sa.String())
    language_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Language.id))


class StrategyVector(db.Model):
    __tablename__ = "strategy_vector"
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    strategy: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Strategy.id))
    description: so.Mapped[str] = so.mapped_column(sa.String())
    embedding: so.Mapped[np.array] = so.mapped_column(Vector(384))
    language_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Language.id))

class TabEvent(db.Model):
    __tablename__ = "tab_events"
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    event_type: so.Mapped[str] = so.mapped_column(sa.String(32))
    timestamp: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime)
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["user_id", "user_client"],
            ["users.id", "users.client"],
            ondelete="CASCADE"
        ),
    )




class StrategyEmbedding(db.Model):
    """RAG-based strategy embeddings using Ollama nomic-embed-text (768-dim)."""
    __tablename__ = "strategy_embedding"
    strategy_id: so.Mapped[str] = so.mapped_column(sa.String(), primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String())
    phase: so.Mapped[Optional[str]] = so.mapped_column(sa.String())
    category: so.Mapped[Optional[str]] = so.mapped_column(sa.String())
    content: so.Mapped[Optional[str]] = so.mapped_column(sa.String())
    embedding: so.Mapped[np.array] = so.mapped_column(Vector(768))


class ConversationState(db.Model):
    __tablename__ = "state"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(back_populates="conversation_state", cascade="all, delete")
    interview_completed: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    current_turn: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    current_context: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id), nullable=True)
    strategy_for_frequency: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Strategy.id), nullable=True)
    completed_contexts: so.Mapped[List["ConversationCompletedContexts"]] = so.relationship(
        back_populates="conversation",
        cascade="all, delete")
    current_conversation_step: so.Mapped[str] = so.mapped_column(sa.String(32),
                                                                 sa.CheckConstraint(
                                                                     "current_conversation_step IN ('intro', 'strategy', 'probe', 'frequency', 'complete')",
                                                                     name="response_check"),
                                                                 nullable=True)
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client],
                                              ondelete="CASCADE"), {})


class ConversationCompletedContexts(db.Model):
    __tablename__ = "conversation_completed_contexts"
    conversation_id: so.Mapped["ConversationState"] = so.mapped_column(
        sa.ForeignKey(ConversationState.id, ondelete="CASCADE"), primary_key=True)
    completed_context_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id,
                                                                          ondelete="CASCADE"),
                                                            primary_key=True)
    conversation: so.Mapped["ConversationState"] = so.relationship(
        back_populates="completed_contexts", cascade="all, delete")


class InterviewAnswer(db.Model):
    __tablename__ = "interview_answer"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(back_populates="interview_answers", cascade="all, delete")
    context: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id), nullable=True)
    strategy: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Strategy.id), nullable=True)
    turn: so.Mapped[int] = so.mapped_column(sa.Integer)
    message: so.Mapped[str] = so.mapped_column(sa.String())
    conversation_step: so.Mapped[str] = so.mapped_column(sa.String(32),
                                                         sa.CheckConstraint(
                                                             "conversation_step IN ('intro', 'strategy', 'probe', 'frequency', 'complete')",
                                                             name="step_check"),
                                                         nullable=False)
    strategies: so.Mapped[List["UserStrategy"]] = so.relationship(
        back_populates="interview_answer",
        cascade="all, delete")
    message_time: so.Mapped[datetime.datetime] = so.mapped_column(
        server_default=sa.text("CURRENT_TIMESTAMP")
    )
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client],
                                              ondelete="CASCADE"),)


class UserStrategy(db.Model):
    __tablename__ = "user_strategy"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(
        back_populates="strategies", cascade="all, delete")
    interview_answer_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(InterviewAnswer.id))
    interview_answer: so.Mapped["InterviewAnswer"] = so.relationship(
        back_populates="strategies", cascade="all, delete")
    context: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id))
    strategy: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Strategy.id))
    frequency: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client],
                                              ondelete="CASCADE"), {})


class LlmResponse(db.Model):
    __tablename__ = "llm_response"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(back_populates="llm_responses", cascade="all, delete")
    message: so.Mapped[str] = so.mapped_column(sa.String())
    context: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Context.id), nullable=True)
    strategy: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Strategy.id), nullable=True)
    turn: so.Mapped[int] = so.mapped_column(sa.Integer)
    conversation_step: so.Mapped[str] = so.mapped_column(sa.String(32),
                                                         sa.CheckConstraint(
                                                             "conversation_step IN ('intro', 'strategy', 'probe', 'frequency', 'complete')",
                                                             name="step_check"),
                                                         nullable=False)
    message_time: so.Mapped[datetime.datetime] = so.mapped_column(
        server_default=sa.text("CURRENT_TIMESTAMP")
    )
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client],
                                              ondelete="CASCADE"), {})


class StrategyEvaluation(db.Model):
    __tablename__ = "strategy_evaluation"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64))
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64))
    user: so.Mapped["User"] = so.relationship(back_populates="evaluation", cascade="all, delete")
    strategy: so.Mapped[str] = so.mapped_column(sa.ForeignKey(Strategy.id))
    SU: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    SF: so.Mapped[float] = so.mapped_column(sa.Float())
    SC: so.Mapped[float] = so.mapped_column(sa.Float())
    __table_args__ = (sa.ForeignKeyConstraint([user_id, user_client],
                                              [User.id, User.client],
                                              ondelete="CASCADE"), {})


class Archive(db.Model):
    __tablename__ = "archive"
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    archived_conversation: so.Mapped[str] = so.mapped_column(sa.String())


class SurveyResponse(db.Model):
    """Stores one submitted survey (all item responses as JSON)."""
    __tablename__ = "survey_responses"

    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    survey_id: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=False, index=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=False, index=True)
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=False)
    language: so.Mapped[str] = so.mapped_column(sa.String(8), nullable=False)
    responses: so.Mapped[dict] = so.mapped_column(sa.JSON, nullable=False)
    submitted_at: so.Mapped[datetime.datetime] = so.mapped_column(
        server_default=sa.text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        sa.Index("idx_survey_user", "survey_id", "user_id", "user_client"),
    )

class ActivityLog(db.Model):
    __tablename__ = "activity_log"
    id: so.Mapped[str] = so.mapped_column(sa.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: so.Mapped[int] = so.mapped_column(sa.Integer, index=True)
    user_id: so.Mapped[Optional[str]] = so.mapped_column(sa.String, index=True)
    user_client: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    action: so.Mapped[str] = so.mapped_column(sa.String, index=True)
    value: so.Mapped[Optional[dict]] = so.mapped_column(sa.JSON)
    user_agent: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    ip_address: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    context: so.Mapped[Optional[str]] = so.mapped_column(sa.String, index=True)
    strategy: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    turn: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer)
    step: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    http_status: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer)
    __table_args__ = (
        sa.Index("idx_user_action", "user_id", "action"),
        sa.Index("idx_timestamp_action", "timestamp", "action"),
        sa.Index("idx_user_timestamp", "user_id", "timestamp"),
    )

    def __repr__(self):
        return f'<ActivityLog {self.action} user={self.user_id} timestamp={self.timestamp}>'

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'user_client': self.user_client,
            'action': self.action,
            'value': self.value,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'context': self.context,
            'strategy': self.strategy,
            'turn': self.turn,
            'step': self.step,
            'http_status': self.http_status
        }


class MouseTrace(db.Model):
    __tablename__ = "mouse_traces"
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=False, index=True)
    user_client: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=False)
    x: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    y: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    page_width: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, nullable=True)
    page_height: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, nullable=True)
    timestamp: so.Mapped[int] = so.mapped_column(sa.BigInteger, nullable=False, index=True)
    session_id: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64), nullable=True)
