# Stock Price Predictor - Complete Project Documentation

## 📋 Project Overview
A **full-stack AI-powered stock trading platform** with web UI, backend API, ML prediction models, and portfolio management. Built with Streamlit (frontend) and FastAPI (backend).

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit)                     │
│  ┌────────────┬─────────┬──────────┬──────────┬────────────┐│
│  │ Dashboard  │Terminal │Backtest  │Portfolio │User Profile││
│  │ (Market    │(Trading)│(Strategy │(Holdings)│(Settings)  ││
│  │  Analysis) │ & AI)   │ Testing) │ & Balance│            ││
│  └────────────┴─────────┴──────────┴──────────┴────────────┘│
│           │         │          │         │          │        │
├───────────┴─────────┴──────────┴─────────┴──────────┴────────┤
│                    HTTP REST API (FastAPI)                   │
│  ┌────────────┬────────────┬──────────────┬──────────────┐   │
│  │Auth Endpoints
│  │Trade Logs  │Profile Mgmt│Health Check  │               │   │
│  └────────────┴────────────┴──────────────┴──────────────┘   │
├──────────────────────────────────────────────────────────────┤
│           Database Layer (SQLAlchemy + SQLite)               │
│  ┌────────────────┐  ┌────────────────────┐                 │
│  │stockdb.db      │  │trades.db           │                 │
│  │├─ users        │  │├─ trade_records    │                 │
│  │├─ otp_codes    │  │├─ position_records │                 │
│  │└─ profiles     │  │└─ balances         │                 │
│  └────────────────┘  └────────────────────┘                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 🗂️ File Structure & Components

### **1. Frontend (Streamlit)**

#### `app.py` - Main Entry Point
- **Starts FastAPI server** in background thread
- **Handles authentication flow** (login/register gates)
- **Routing system** for different pages
- **Global CSS styling** (dark theme with gradients)
- **Floating profile button** and sidebar navigation

**Key Code Flow:**
```python
@st.cache_resource
def start_fastapi():
    """Start FastAPI once in background thread"""
    def run():
        import uvicorn
        uvicorn.run("main:app", host="127.0.0.1", port=8000)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# ── Auth Gate (blocks until logged in) ──
if not st.session_state.is_authenticated:
    # Show login/register modal
    auth.auth_modal()
    st.stop()  # Nothing below runs until logged in

# ── Render pages based on selection ──
if st.session_state.nav_selection == "🏠 Market Overview":
    dashboard.render()
elif st.session_state.nav_selection == "📈 AI Live Terminal":
    terminal.render()
# ... more pages
```

#### `auth.py` - Authentication Module
- User registration & login
- OTP verification (email-based 2FA)
- Password validation
- Session management

**Key Functions:**
```python
def is_valid_email(email):     # Regex validation
def is_valid_password(pwd):    # Min 6 chars
def auth_modal():              # Modal UI for auth flows
```

#### `dashboard.py` - Market Overview
- Displays 5 major auto companies: Audi, BMW, VW, GM, Ford
- Shows live stock prices & % changes
- Market cap analysis
- Sector market share pie chart (with ECharts.js)
- News feed aggregation

**Key Features:**
- Real-time ticker data via `yfinance`
- Market cap calculations
- Interactive pie chart visualization

#### `terminal.py` - AI Live Trading Terminal
- **Hybrid ML Model**: ARIMA + Random Forest
- Technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands
- Price predictions with confidence intervals
- Asset selector cards
- Technical analysis visualization

**Key Model:**
```python
run_prediction_model(asset_name):
    ├─ ARIMA: Time-series forecasting
    └─ Random Forest: Pattern classification
           Returns: [forecast, confidence, signal]
```

#### `backtesting.py` - Strategy Testing
- **SMA Crossover Strategy** (fast SMA > slow SMA = BUY)
- **RSI Mean Reversion** (oversold = BUY, overbought = SELL)
- Equity curve simulation
- Drawdown analysis
- Performance metrics

**Backtest Logic:**
```python
# Example: SMA Crossover
SMA_Fast > SMA_Slow → Generate BUY signal
Strategy_Returns = Market_Returns * Signal
Equity = Initial_Capital * (1 + Strategy_Returns).cumprod()
```

#### `portfolio.py` - Position Management
- Virtual trading (buy/sell positions)
- Order confirmation modal with risk checks
- Balance tracking
- Trade history log
- Equity curve visualization
- Position holdings display

**Risk Checks:**
```python
if action == "BUY":
    if balance < cost:
        raise Error("Insufficient buying power")

elif action == "SELL":
    if owned_shares < quantity:
        raise Error("Insufficient inventory - Shorting blocked")
```

#### `user_profile.py` - User Settings
- Display name & profile image
- Email & phone management
- Currency selection
- 2FA toggle
- Account type display

#### `utils.py` - Utility Functions
- **Data fetching**: `yfinance` for live prices
- **Web scraping**: Beautiful Soup for news
- **Technical indicators**: SMA, EMA, RSI, MACD, Bollinger Bands
- **Prediction model**: ARIMA + Random Forest

---

### **2. Backend (FastAPI API)**

#### `main.py` - FastAPI Server
- REST API endpoints for auth, trades, profiles
- OTP generation & verification
- Database session management

**Key Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check + DB connection |
| `/auth/register` | POST | User registration |
| `/auth/login` | POST | User login |
| `/auth/send-otp` | POST | Send OTP to email |
| `/auth/verify-otp` | POST | Verify OTP code |
| `/auth/validate-session/{username}` | GET | Session validation on refresh |
| `/profile/{username}` | GET/PUT | User profile operations |
| `/trades/record` | POST | Log trade transaction |
| `/trades/history/{email}` | GET | Fetch user's trade history |

**Sample Register Endpoint:**
```python
@app.post("/auth/register")
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check if username/email exists
    existing = db.query(User).filter(
        (User.username == req.username) |
        (User.email == req.email)
    ).first()
    
    if existing:
        return {"success": False, "message": "Username/Email taken"}
    
    # Create new user
    new_user = User(
        full_name=req.full_name,
        username=req.username,
        email=req.email,
        password=hash_password(req.password),
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"success": True, "message": "✅ Registration successful"}
```

---

### **3. Database Models**

#### `models.py` - User Database (stockdb.db)

```python
class User(Base):
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True)
    
    # Registration Fields
    full_name = Column(String)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    phone = Column(String)
    account_no = Column(String)
    password = Column(String)  # Hashed
    
    # Profile Fields
    display_name = Column(String)
    currency = Column(String, default="USD ($)")
    two_fa_enabled = Column(Integer, default=1)  # Boolean
    biometric_login = Column(Integer, default=0)
    profile_image = Column(Text)  # Base64 encoded
    
    # OTP Fields
    otp_code = Column(String)
    otp_expires_at = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

#### `trades_models.py` - Trading Database (trades.db)

```python
class TradeRecord(Base):
    __tablename__ = "trade_records"
    
    id = Column(Integer, primary_key=True)
    user_email = Column(String, index=True)
    action = Column(String)  # "BUY" or "SELL"
    asset = Column(String)  # "Audi", "BMW", etc
    quantity = Column(Integer)
    price = Column(Float)
    total_value = Column(Float)
    balance_after = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class PositionRecord(Base):
    __tablename__ = "position_records"
    
    id = Column(Integer, primary_key=True)
    user_email = Column(String, unique=True)
    positions_json = Column(String)  # Stores portfolio as JSON
    total_balance = Column(Float)
    updated_at = Column(DateTime)
```

---

### **4. Machine Learning Models**

#### `training_*.py` Files (Audi, BMW, Ford, GM, VW)
- **Algorithm**: Random Forest Classifier
- **Data**: Historical CSV files (Close price)
- **Features**: 
  - Previous prices (lookback window)
  - Technical indicators
- **Target**: Binary classification (Up/Down prediction)

**Training Pipeline:**
```python
# Example: training_audi.py
data = pd.read_csv('AUD.csv')

# Feature Engineering
data['lag_1'] = data['Close'].shift(1)
data['lag_5'] = data['Close'].shift(5)
data['SMA_5'] = data['Close'].rolling(5).mean()

# Labels (1 = price went up next day, 0 = went down)
data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Random Forest Model
model = RandomForestClassifier(n_estimators=100, max_depth=10)
model.fit(X_train, y_train)

# Evaluation
accuracy = accuracy_score(y_test, model.predict(X_test))
print(f"Model Accuracy: {accuracy:.2%}")
```

---

## 🔄 Complete User Flow

### **1. Registration & Login Flow**

```
User Access Website (app.py)
    ↓
[Check if Authenticated?]
    ├─ NO → Show Login/Register Modal (auth.py)
    │   └─ User fills registration form
    │       └─ Sends data to FastAPI /auth/register
    │           └─ FastAPI validates & creates DB entry
    │               └─ User logs back in
    └─ YES → Skip to Dashboard
```

### **2. Trading Flow**

```
User navigates to Portfolio (portfolio.py)
    ↓
[Clicks BUY/SELL Button]
    ↓
Portfolio calls API to get live price (yfinance)
    ↓
Order Confirmation Modal appears
    [Risk Check: Sufficient balance? Own enough shares?]
    ├─ PASS → Execute Trade
    │   └─ Update session_state.positions
    │   └─ Record in trades.db
    │   └─ Call API /trades/record
    └─ FAIL → Show Error Message
```

### **3. Prediction Flow**

```
User selects asset in Terminal (terminal.py)
    ↓
Loads historical data from CSV (AUD.csv, BMW.DE.csv, etc)
    ↓
Adds Technical Indicators (utils.py)
    ├─ SMA, EMA, RSI, MACD, Bollinger Bands
    └─ Normalizes features
    ↓
Runs Hybrid Model (utils.py)
    ├─ ARIMA: Time-series forecast
    ├─ Random Forest: Pattern classification
    └─ Combines both → Prediction
    ↓
Displays forecast with confidence on chart
```

### **4. Backtesting Flow**

```
User selects strategy & parameters (backtesting.py)
    ├─ SMA Crossover (fast/slow windows)
    └─ RSI Mean Reversion (thresholds)
    ↓
Loads historical data → Calculates signals → Simulates trades
    ↓
Generates equity curve & metrics
    ├─ Total Return %
    ├─ Sharpe Ratio
    ├─ Max Drawdown
    ├─ Win Rate
    └─ Equity Curve Chart
```

---

## 🔐 Authentication System

### **Two-Factor Authentication (OTP)**
1. User enters email
2. Backend generates 6-digit OTP → sends via SMTP
3. OTP stored in `otp_store` dict with 10-min expiration
4. User enters OTP
5. Backend verifies → Sets session authenticated

**Email Service** (`email_service.py`):
```python
SENDER_EMAIL = "aryanchoudhury95979@gmail.com"
SENDER_PASSWORD = "ljpyptnkvsftcjli"  # App-specific password

def send_otp_email(receiver_email, otp):
    """Send OTP via SMTP"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Stock Predictor OTP Code"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    
    plain = f"Your OTP is: {otp}\nExpires in 10 minutes."
    
    msg.attach(MIMEText(plain, "plain"))
    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
```

---

## 💾 Data Flow

### **Where Data Comes From**
1. **Live Prices**: `yfinance` library (Yahoo Finance API)
2. **Historical Data**: CSV files in project (AUD.csv, BMW.DE.csv, etc)
3. **News Data**: Web scraping with BeautifulSoup + RSS feeds

### **How Data Flows**
```
yfinance API
    ↓
utils.get_auto_tickers_data() → Returns {Company: (price, change%)}
    ↓
Used by:
├─ dashboard.py (KPI cards)
├─ terminal.py (asset selector)
├─ portfolio.py (trade execution)
└─ backtesting.py (historical data)
```

---

## 🎯 Key Technical Concepts

### **Session State Management**
Streamlit uses `st.session_state` to persist data across reruns:
```python
st.session_state.is_authenticated = True
st.session_state.current_username = "john_doe"
st.session_state.selected_asset = "BMW"
st.session_state.positions = {"Audi": {"shares": 10, "avg_price": 50}}
```

### **Caching**
```python
@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_auto_tickers_data():
    # Expensive API calls cached here
    return data

@st.cache_resource  # Cache across sessions
def start_fastapi():
    # Start server only once
    return thread
```

### **Technical Indicators**
```python
# SMA (Simple Moving Average)
SMA_20 = Close.rolling(window=20).mean()

# RSI (Relative Strength Index)
delta = Close.diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
RS = gain / loss
RSI = 100 - (100 / (1 + RS))

# MACD (Moving Average Convergence Divergence)
EMA_12 = Close.ewm(span=12).mean()
EMA_26 = Close.ewm(span=26).mean()
MACD = EMA_12 - EMA_26
Signal = MACD.ewm(span=9).mean()
```

---

## 📊 Prediction Model (AI Terminal)

### **ARIMA Model**
Autoregressive Integrated Moving Average: Forecasts based on past values
```
ARIMA(p, d, q)
- p: Number of autoregressive lags
- d: Number of differencing steps
- q: Number of moving average terms
```

### **Random Forest Classifier**
Ensemble ML model for price direction prediction
```
Binary Classification:
- 1 = Price will go UP tomorrow
- 0 = Price will go DOWN tomorrow

Trained on: Historical prices + Technical indicators
```

### **Hybrid Approach**
```python
def run_prediction_model(asset_name):
    # Get historical data
    data = pd.read_csv(f"{asset_name}.csv")
    
    # Add technical indicators
    data = add_technical_indicators(data)
    
    # ARIMA forecast
    arima_forecast = fit_arima_model(data['Close'])
    
    # Random Forest prediction
    rf_signal = fit_random_forest(data[features], data['Target'])
    
    # Combine both
    final_prediction = (arima_forecast + rf_signal) / 2
    
    return final_prediction, confidence_interval
```

---

## 🚀 Running the Application

### **Prerequisites**
- Python 3.9+
- Virtual environment with packages installed:
```
pip install streamlit fastapi uvicorn requests pandas numpy scikit-learn 
            plotly sqlalchemy pydantic statsmodels yfinance beautifulsoup4 lxml
```

### **Start the App**
```bash
# From project directory
.venv\Scripts\streamlit run app.py
```

### **What Happens**
1. ✅ Streamlit launches on `http://localhost:8501`
2. ✅ FastAPI auto-starts on `http://localhost:8000` (background)
3. ✅ Databases created: `stockdb.db`, `trades.db`
4. ✅ User registration/login system ready
5. ✅ AI predictions & trading ready to use

---

## 📈 Summary

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Frontend** | User interface & interactions | Streamlit |
| **Backend** | REST API & auth | FastAPI + SQLAlchemy |
| **Database** | User data & trades | SQLite |
| **ML Models** | Price predictions | ARIMA + Random Forest |
| **Data** | Live prices & historical | yfinance + CSV |
| **Charts** | Visualizations | Plotly + ECharts.js |

This is a complete **production-ready** stock trading platform with authentication, real-time data, ML predictions, and backtesting capabilities! 🎯

