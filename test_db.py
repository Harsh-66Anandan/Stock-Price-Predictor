# test_db.py
from models import engine, create_tables, User, Trade, Portfolio
from sqlalchemy.orm import Session
from sqlalchemy import text

print("=" * 50)
print("STOCK PREDICTOR — DATABASE TEST")
print("=" * 50)

# ── TEST 1: Connection ───────────────────────────
print("\n[1] Testing connection...")
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Database connected!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit()

# ── TEST 2: Create Tables ────────────────────────
print("\n[2] Creating tables...")
create_tables()

# ── TEST 3: Insert a User ────────────────────────
print("\n[3] Inserting test user...")
with Session(engine) as db:
    # Check if already exists (avoid duplicate error)
    existing = db.query(User).filter_by(email="test@gmail.com").first()
    if existing:
        print("⚠️  User already exists, skipping insert.")
        user = existing
    else:
        user = User(email="test@gmail.com", display_name="Test User")
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ User inserted! ID = {user.id}")

# ── TEST 4: Read User Back ───────────────────────
print("\n[4] Reading user from database...")
with Session(engine) as db:
    user = db.query(User).filter_by(email="test@gmail.com").first()
    print(f"✅ Found user → ID: {user.id} | Name: {user.display_name} | Email: {user.email}")

# ── TEST 5: Insert a Trade ───────────────────────
print("\n[5] Inserting test trade...")
with Session(engine) as db:
    trade = Trade(
        user_id=1,
        asset="BMW",
        action="BUY",
        quantity=10,
        price=85.50,
        total_value=855.00
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    print(f"✅ Trade inserted! ID = {trade.id} | {trade.action} {trade.quantity} {trade.asset} @ ${trade.price}")

# ── TEST 6: Insert Portfolio Position ───────────
print("\n[6] Inserting portfolio position...")
with Session(engine) as db:
    position = Portfolio(
        user_id=1,
        asset="BMW",
        shares=10,
        avg_price=85.50
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    print(f"✅ Position saved! {position.shares} shares of {position.asset} @ avg ${position.avg_price}")

# ── TEST 7: Read All Trades ──────────────────────
print("\n[7] Reading all trades from database...")
with Session(engine) as db:
    trades = db.query(Trade).all()
    for t in trades:
        print(f"   → [{t.id}] {t.action} {t.quantity} {t.asset} @ ${t.price} | Total: ${t.total_value}")

print("\n" + "=" * 50)
print("ALL TESTS PASSED ✅ — Database is working!")
print("=" * 50)
print("\n📁 Your database file is at: F:\\PythonProject\\stockdb.db")
print("👉 Open it with DB Browser for SQLite to see your data visually")