from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, event
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime

DATABASE_URL = "sqlite:///./trades.db"

# SQLite configuration for concurrent access
trades_engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # 30 second timeout for locked database
    },
    poolclass=StaticPool,  # Use single connection
    echo=True
)

# Enable WAL mode for better concurrency
@event.listens_for(trades_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

Base = declarative_base()

class TradeRecord(Base):
    __tablename__ = "trades"

    id           = Column(Integer, primary_key=True, index=True)
    user_email   = Column(String, index=True)
    action       = Column(String)
    asset        = Column(String)
    quantity     = Column(Integer)
    price        = Column(Float)
    total_value  = Column(Float)
    balance_after= Column(Float)
    executed_at  = Column(DateTime, default=datetime.utcnow)

class PositionRecord(Base):
    __tablename__ = "positions"

    id          = Column(Integer, primary_key=True, index=True)
    user_email  = Column(String, index=True)
    asset       = Column(String, index=True)
    shares      = Column(Integer, default=0)
    avg_price   = Column(Float, default=0.0)
    updated_at  = Column(DateTime, default=datetime.utcnow)


def create_trade_tables():
    Base.metadata.create_all(bind=trades_engine)
    print("✅ Trade tables created!")


def get_trades_db():
    db = Session(trades_engine)
    try:
        yield db
    finally:
        db.close()
