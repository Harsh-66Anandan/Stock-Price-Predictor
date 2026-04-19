# models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime

DATABASE_URL = "sqlite:///./stockdb.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    # ── Registration fields ──────────────────────
    full_name        = Column(String,  nullable=True)
    username         = Column(String,  unique=True, index=True, nullable=True)
    email            = Column(String,  unique=True, index=True)
    phone            = Column(String,  nullable=True)
    account_no       = Column(String,  nullable=True)
    password         = Column(String,  nullable=True)
    # ── Profile fields ───────────────────────────
    display_name     = Column(String,  nullable=True)
    account_type     = Column(String,  default="Institutional / Enterprise")
    currency         = Column(String,  default="USD ($)")
    two_fa_enabled   = Column(Integer, default=1)
    biometric_login  = Column(Integer, default=0)
    profile_image    = Column(Text,    nullable=True)
    # ── OTP fields ───────────────────────────────
    otp_code         = Column(String,  nullable=True)
    otp_expires_at   = Column(String,  nullable=True)
    # ── Timestamps ───────────────────────────────
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ User table created in stockdb.db!")

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()