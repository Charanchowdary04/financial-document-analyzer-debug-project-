"""SQLAlchemy database setup and models for analysis jobs."""
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from config import DATABASE_URL

Base = declarative_base()

# SQLite needs check_same_thread=False for FastAPI; use StaticPool for file DB
_connect_args = {}
_engine_kw = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
    _engine_kw = {"connect_args": _connect_args, "poolclass": StaticPool}

engine = create_engine(DATABASE_URL, **_engine_kw)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String(20), default=JobStatus.PENDING, nullable=False)
    file_path = Column(String(512), nullable=False)
    original_filename = Column(String(256), nullable=True)
    query = Column(Text, nullable=True)
    result_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Create tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
