# Enterprise Stock Predictor & Portfolio Manager

A professional-grade, full-stack financial analytics platform featuring a **Streamlit** frontend, a **FastAPI** backend, and a **Hybrid Machine Learning** core. This application provides a comprehensive suite of tools for stock market analysis, including AI-driven forecasting, strategy backtesting, and secure portfolio management.

## 🏗️ Architecture
The project follows a modular, three-tier architecture to ensure scalability and separation of concerns:
- **Frontend (Streamlit):** An interactive, responsive user interface styled with custom CSS.
- **Backend (FastAPI):** A high-performance REST API managing business logic and user authentication.
- **Database (SQLite/SQLAlchemy):** A persistent relational database storing unified user credentials and profiles.
- **ML Core (Hybrid Model):** Customized ARIMA + Random Forest training scripts for Audi, BMW, Ford, GM, and VW.

## 🚀 Key Features

### 1. Unified Authentication Gateway
- **Secure Login & Registration:** Multi-view modal with strict Regex validation.
- **Persistent Sessions:** All data is securely stored in `stockdb.db`.
- **Auto-Bouncer:** Unauthorized access is blocked at the system level.

### 2. User Identity Management
- **Enterprise Profiles:** Customizable display names, currency preferences, and security settings.
- **Dynamic Avatars:** Real-time image upload and cropping tool to personalize identity.

### 3. Intelligence & Analytics
- **📈 AI Live Terminal:** Specialized forecasting interface powered by stock-specific ML models.
- **🧠 Hybrid Training:** Custom scripts (`training_*.py`) that combine ARIMA and Random Forest for high-accuracy predictions.
- **⚙️ Backtest Engine:** Validate trading strategies against historical data.
- **💼 Portfolio Tracker:** Manage asset holdings and monitor performance.

## ⚙️ Installation & Setup

### 1. Install Dependencies
```bash
pip install streamlit fastapi uvicorn sqlalchemy requests Pillow streamlit-cropper scikit-learn statsmodels pandas yfinance numpy matplotlib"decentralized-app"
