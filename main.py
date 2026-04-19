# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from models import engine, get_db, create_tables, User
from trades_models import get_trades_db, create_trade_tables, TradeRecord, PositionRecord
from email_service import generate_otp, send_otp_email
import re

app = FastAPI(title="Stock Predictor API")

create_tables()
create_trade_tables()

# OTP stored in memory — resets on server restart (fine for 10 min tokens)
otp_store: dict = {}

# ══════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    full_name  : str
    username   : str
    email      : str
    phone      : str
    account_no : str
    password   : str

class LoginRequest(BaseModel):
    username: str
    password: str

class SendOTPRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp  : str

class ProfileUpdateRequest(BaseModel):
    display_name   : str
    email          : Optional[str] = None
    currency       : str
    two_fa_enabled : bool
    biometric_login: bool
    profile_image  : Optional[str] = None

class TradeSchema(BaseModel):
    user_email    : str
    action        : str
    asset         : str
    quantity      : int
    price         : float
    total_value   : float
    balance_after : float

# ══════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════

@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "✅ running", "db": "✅ connected"}
    except Exception as e:
        return {"status": "❌ error", "detail": str(e)}

# ══════════════════════════════════════════════════
# AUTH — REGISTER
# ══════════════════════════════════════════════════

@app.post("/auth/register")
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        print(f"[REGISTER] New registration attempt for username: {req.username.strip()}")
        existing = db.query(User).filter(
            (User.username == req.username.strip()) |
            (User.email    == req.email.strip())
        ).first()

        if existing:
            if existing.username == req.username.strip():
                print(f"[REGISTER] Username already taken: {req.username.strip()}")
                return {"success": False, "message": "❌ Username already taken."}
            if existing.email == req.email.strip():
                print(f"[REGISTER] Email already registered: {req.email.strip()}")
                return {"success": False, "message": "❌ Email already registered."}

        new_user = User(
            full_name    = req.full_name.strip(),
            username     = req.username.strip(),
            email        = req.email.strip(),
            phone        = req.phone.strip(),
            account_no   = req.account_no.strip(),
            password     = req.password,
            display_name = req.full_name.strip()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"[REGISTER] ✅ User registered successfully: {new_user.username} with password: {new_user.password}")
        return {
            "success": True,
            "message": "✅ Account created successfully!",
            "user_id": new_user.id
        }
    except Exception as e:
        db.rollback()
        print(f"[REGISTER] Error: {str(e)}")
        return {"success": False, "message": str(e)}

# ══════════════════════════════════════════════════
# AUTH — LOGIN (password)
# ══════════════════════════════════════════════════

@app.post("/auth/login")
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        print(f"[LOGIN] Attempting login for username: {req.username.strip()}")
        user = db.query(User).filter(
            User.username == req.username.strip()
        ).first()

        if not user:
            print(f"[LOGIN] User not found: {req.username.strip()}")
            return {"success": False, "message": "❌ Invalid username or password."}
        
        print(f"[LOGIN] User found: {user.username}, password in DB: {user.password}")
        
        # Compare passwords (strip both to handle whitespace issues)
        if user.password.strip() != req.password.strip():
            print(f"[LOGIN] Password mismatch. DB password: '{user.password.strip()}' vs provided: '{req.password.strip()}'")
            return {"success": False, "message": "❌ Invalid username or password."}

        print(f"[LOGIN] ✅ Login successful for {user.username}")
        return {
            "success"      : True,
            "message"      : "✅ Login successful!",
            "user_id"      : user.id,
            "username"     : user.username,
            "display_name" : user.display_name or user.username,
            "email"        : user.email,
            "profile_image": user.profile_image
        }
    except Exception as e:
        print(f"[LOGIN] Error: {str(e)}")
        return {"success": False, "message": str(e)}

# ══════════════════════════════════════════════════
# AUTH — VALIDATE SESSION
# ══════════════════════════════════════════════════

@app.get("/auth/validate-session/{username}")
def validate_session(username: str, db: Session = Depends(get_db)):
    """Check if a user is still valid (for session persistence across refresh)"""
    try:
        user = db.query(User).filter(User.username == username.strip()).first()
        
        if not user:
            return {"success": False, "message": "User not found"}
        
        return {
            "success"      : True,
            "user_id"      : user.id,
            "username"     : user.username,
            "display_name" : user.display_name or user.username,
            "email"        : user.email,
            "profile_image": user.profile_image
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# ══════════════════════════════════════════════════
# AUTH — SEND OTP
# ANY email can receive OTP — not just registered users
# ══════════════════════════════════════════════════

@app.post("/auth/send-otp")
def send_otp(req: SendOTPRequest, db: Session = Depends(get_db)):
    try:
        email = req.email.strip().lower()

        # Validate email format
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            return {"success": False, "message": "❌ Invalid email format."}

        # Generate OTP
        otp    = generate_otp()
        expiry = datetime.utcnow() + timedelta(minutes=10)

        # Store OTP in memory
        otp_store[email] = {"otp": otp, "expires_at": expiry}

        print(f"[OTP] Generated {otp} for {email}")

        # Send email
        result = send_otp_email(email, otp)

        if result.get("success"):
            return {"success": True, "message": f"✅ OTP sent to {email}"}
        else:
            otp_store.pop(email, None)
            return {"success": False, "message": result.get("message", "❌ Failed to send email.")}

    except Exception as e:
        return {"success": False, "message": str(e)}

# ══════════════════════════════════════════════════
# AUTH — VERIFY OTP
# ══════════════════════════════════════════════════

@app.post("/auth/verify-otp")
def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    try:
        email  = req.email.strip().lower()
        record = otp_store.get(email)

        # Check OTP exists
        if not record:
            return {
                "success": False,
                "message": "❌ No OTP found. Please generate a new one."
            }

        # Check expiry
        if datetime.utcnow() > record["expires_at"]:
            otp_store.pop(email, None)
            return {
                "success": False,
                "message": "❌ OTP expired. Please generate a new one."
            }

        # Check OTP matches
        if req.otp.strip() != record["otp"]:
            return {
                "success": False,
                "message": "❌ Wrong OTP. Check your email and try again."
            }

        # ✅ Correct — delete OTP (one time use)
        otp_store.pop(email, None)

        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        if user:
            return {
                "success"     : True,
                "message"     : "✅ Login successful!",
                "user_id"     : user.id,
                "username"    : user.username or email.split("@")[0],
                "display_name": user.display_name or email.split("@")[0].capitalize(),
                "email"       : user.email,
                "profile_image": user.profile_image
            }
        else:
            # User not registered — still let them in with email as identity
            return {
                "success"     : True,
                "message"     : "✅ Login successful!",
                "user_id"     : None,
                "username"    : email.split("@")[0],
                "display_name": email.split("@")[0].capitalize(),
                "email"       : email,
                "profile_image": None
            }

    except Exception as e:
        return {"success": False, "message": str(e)}

# ══════════════════════════════════════════════════
# PROFILE ROUTES
# ══════════════════════════════════════════════════

@app.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username,
             "email": u.email, "display_name": u.display_name,
             "created_at": str(u.created_at)} for u in users]

@app.get("/users/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username"       : user.username,
        "email"          : user.email,
        "full_name"      : user.full_name,
        "display_name"   : user.display_name,
        "currency"       : user.currency,
        "account_type"   : user.account_type,
        "two_fa_enabled" : bool(user.two_fa_enabled),
        "biometric_login": bool(user.biometric_login),
        "profile_image"  : user.profile_image
    }

@app.put("/users/{username}")
def update_user(username: str, req: ProfileUpdateRequest,
                db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.email and req.email.strip() != user.email:
        existing = db.query(User).filter(
            User.email == req.email.strip()
        ).first()
        if existing:
            return {"success": False,
                    "message": "❌ Email already used by another account."}
        user.email = req.email.strip()

    user.display_name    = req.display_name
    user.currency        = req.currency
    user.two_fa_enabled  = 1 if req.two_fa_enabled else 0
    user.biometric_login = 1 if req.biometric_login else 0
    user.updated_at      = datetime.utcnow()

    if req.profile_image is not None:
        user.profile_image = req.profile_image

    try:
        db.commit()
        db.refresh(user)
        return {
            "success"     : True,
            "message"     : "✅ Profile updated!",
            "display_name": user.display_name,
            "email"       : user.email,
            "currency"    : user.currency
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@app.delete("/users/{username}")
def delete_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"success": True, "message": f"✅ User {username} deleted."}

# ══════════════════════════════════════════════════
# TRADE ROUTES
# ══════════════════════════════════════════════════

@app.post("/trades/save")
def save_trade(trade: TradeSchema, db: Session = Depends(get_trades_db)):
    try:
        new_trade = TradeRecord(
            user_email    = trade.user_email,
            action        = trade.action,
            asset         = trade.asset,
            quantity      = trade.quantity,
            price         = trade.price,
            total_value   = trade.total_value,
            balance_after = trade.balance_after,
            executed_at   = datetime.utcnow()
        )
        db.add(new_trade)

        position = db.query(PositionRecord).filter(
            PositionRecord.user_email == trade.user_email,
            PositionRecord.asset      == trade.asset
        ).first()

        if trade.action == "BUY":
            if position:
                new_qty             = position.shares + trade.quantity
                new_avg             = ((position.shares * position.avg_price) +
                                       (trade.quantity  * trade.price)) / new_qty
                position.shares     = new_qty
                position.avg_price  = round(new_avg, 2)
                position.updated_at = datetime.utcnow()
            else:
                db.add(PositionRecord(
                    user_email = trade.user_email,
                    asset      = trade.asset,
                    shares     = trade.quantity,
                    avg_price  = trade.price
                ))
        elif trade.action == "SELL":
            if position:
                position.shares    -= trade.quantity
                position.updated_at = datetime.utcnow()
                if position.shares <= 0:
                    db.delete(position)

        db.commit()
        db.refresh(new_trade)
        return {
            "success" : True,
            "message" : f"✅ {trade.action} saved!",
            "trade_id": new_trade.id,
            "action"  : trade.action,
            "asset"   : trade.asset,
            "quantity": trade.quantity,
            "price"   : trade.price
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@app.get("/trades/all")
def get_all_trades(db: Session = Depends(get_trades_db)):
    trades = db.query(TradeRecord).order_by(
        TradeRecord.executed_at.desc()).all()
    return [{"id": t.id, "user_email": t.user_email,
             "action": t.action, "asset": t.asset,
             "quantity": t.quantity, "price": t.price,
             "total_value": t.total_value,
             "balance_after": t.balance_after,
             "executed_at": str(t.executed_at)} for t in trades]

@app.get("/trades/user/{email}")
def get_user_trades(email: str, db: Session = Depends(get_trades_db)):
    trades = db.query(TradeRecord).filter(
        TradeRecord.user_email == email
    ).order_by(TradeRecord.executed_at.desc()).all()
    return [{"id": t.id, "action": t.action, "asset": t.asset,
             "quantity": t.quantity, "price": t.price,
             "total_value": t.total_value,
             "executed_at": str(t.executed_at)} for t in trades]

@app.get("/positions/{email}")
def get_positions(email: str, db: Session = Depends(get_trades_db)):
    positions = db.query(PositionRecord).filter(
        PositionRecord.user_email == email).all()
    return [{"asset": p.asset, "shares": p.shares,
             "avg_price": p.avg_price,
             "updated_at": str(p.updated_at)} for p in positions]