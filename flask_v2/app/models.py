from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db


class Language(db.Model):
    __tablename__ = "languages"
    id: so.Mapped[str] = so.mapped_column(primary_key=True)
    lang_code: so.Mapped[str] = so.mapped_column(sa.String(2), index=True,
                                                 unique=True)


class User(db.Model):
    __tablename__ = "users"
    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    client: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    language_id: so.Mapped[str] = so.mapped_column(sa.String(64), sa.ForeignKey(Language.id))
    message_history: so.Mapped[Optional[str]] = so.mapped_column(sa.String())
