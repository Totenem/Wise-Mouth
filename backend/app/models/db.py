"""SQLAlchemy models + small persistence helpers.

In-memory room state is the source of truth while live; these writes are
fire-and-forget so a DB hiccup never stalls the UI.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from ..config import settings

log = logging.getLogger("wisemouth.db")


class Base(DeclarativeBase):
    pass


def _now():
    return dt.datetime.now(dt.timezone.utc)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="live")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(32), index=True)
    speaker: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    timestamp_ms: Mapped[int] = mapped_column(Integer)


class SignalRow(Base):
    __tablename__ = "signals"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(32), index=True)
    type: Mapped[str] = mapped_column(String(40))
    speaker: Mapped[str] = mapped_column(String(100))
    evidence: Mapped[str] = mapped_column(Text)
    timestamp_ms: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float)
    signal_metadata: Mapped[dict] = mapped_column(JSON, default=dict)  # full Signal payload


class CommitmentRow(Base):
    __tablename__ = "commitments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(32), index=True)
    speaker: Mapped[str] = mapped_column(String(100))
    commitment: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    original_timestamp: Mapped[int] = mapped_column(Integer)
    changed_timestamp: Mapped[int | None] = mapped_column(Integer, nullable=True)


class QuestionRow(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(32), index=True)
    question: Mapped[str] = mapped_column(Text)
    speaker: Mapped[str] = mapped_column(String(100))
    answered: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp_ms: Mapped[int] = mapped_column(Integer)


_engine = None


def init_db() -> None:
    global _engine
    url = settings.database_url or "sqlite:///./data/wisemouth.db"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
    _engine = create_engine(url, **kwargs)
    Base.metadata.create_all(_engine)


def _run(fn) -> None:
    if _engine is None:
        return
    try:
        with Session(_engine) as s:
            fn(s)
            s.commit()
    except Exception as e:
        log.warning("db write failed: %s", e)


def fire(fn) -> None:
    """Schedule a DB write off the event loop; never raises."""
    try:
        asyncio.get_running_loop().create_task(asyncio.to_thread(_run, fn))
    except RuntimeError:
        _run(fn)


def read(fn):
    if _engine is None:
        return None
    with Session(_engine) as s:
        return fn(s)


def list_conversations() -> list[dict]:
    def q(s: Session):
        rows = s.execute(select(Conversation).order_by(Conversation.started_at.desc()).limit(50)).scalars().all()
        return [{"id": r.id, "title": r.title, "started_at": r.started_at.isoformat(), "status": r.status} for r in rows]
    return read(q) or []


def load_conversation(cid: str) -> dict | None:
    def q(s: Session):
        c = s.get(Conversation, cid)
        if c is None:
            return None
        segs = s.execute(select(TranscriptSegment).where(TranscriptSegment.conversation_id == cid)
                         .order_by(TranscriptSegment.timestamp_ms)).scalars().all()
        sigs = s.execute(select(SignalRow).where(SignalRow.conversation_id == cid)
                         .order_by(SignalRow.timestamp_ms)).scalars().all()
        return {
            "id": c.id, "title": c.title, "status": c.status,
            "started_at": c.started_at.isoformat(),
            "ended_at": c.ended_at.isoformat() if c.ended_at else None,
            "transcript": [{"id": t.id, "speaker": t.speaker, "text": t.text, "start_ms": t.timestamp_ms} for t in segs],
            "signals": [r.signal_metadata for r in sigs],
        }
    return read(q)
