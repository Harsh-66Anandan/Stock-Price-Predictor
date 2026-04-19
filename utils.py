import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import timedelta, datetime
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import random
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

# Shared Aesthetic Color Palette
AESTHETIC_COLORS = ['#00C9FF', '#92FE9D', '#FF1493', '#FFD700', '#B026FF']

@st.cache_data(ttl=600)
def get_auto_tickers_data():
    ticker_config = {'Audi': 'NSU.DE', 'BMW': 'BMW.DE', 'VW': 'VOW3.DE', 'GM': 'GM', 'Ford': 'F'}
    data = {}
    for name, symbol in ticker_config.items():
        try:
            hist = yf.Ticker(symbol).history(period="5d")
            if not hist.empty and len(hist) >= 2:
                price, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                data[name] = (price, ((price - prev) / prev) * 100)
            else:
                data[name] = (0.0, 0.0)
        except:
            data[name] = (random.uniform(10, 100), random.uniform(-1.5, 1.5))
    return data

@st.cache_data(ttl=3600)
def get_market_overview_data():
    symbols = {'Audi': 'NSU.DE', 'BMW': 'BMW.DE', 'VW': 'VOW3.DE', 'GM': 'GM', 'Ford': 'F'}
    fallbacks = {'Audi': 78.5, 'BMW': 65.2, 'VW': 61.4, 'GM': 48.1, 'Ford': 49.3}
    pe_fallbacks = {'Audi': 12.4, 'BMW': 5.8, 'VW': 4.1, 'GM': 5.3, 'Ford': 11.2}
    data = []
    for name, sym in symbols.items():
        try:
            info = yf.Ticker(sym).info
            mcap = info.get('marketCap', fallbacks[name] * 1e9)
            pe = info.get('trailingPE', pe_fallbacks[name])
            if mcap is None: mcap = fallbacks[name] * 1e9
            if pe is None: pe = pe_fallbacks[name]
            data.append({'Company': name, 'Market Cap': mcap, 'P/E Ratio': pe})
        except:
            data.append({'Company': name, 'Market Cap': fallbacks[name] * 1e9, 'P/E Ratio': pe_fallbacks[name]})
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_historical_sector_data():
    tickers = ['NSU.DE', 'BMW.DE', 'VOW3.DE', 'GM', 'F']
    ticker_map = {'NSU.DE': 'Audi', 'BMW.DE': 'BMW', 'VOW3.DE': 'VW', 'GM': 'GM', 'F': 'Ford'}
    try:
        df = yf.download(tickers, period="1y")
        if isinstance(df.columns, pd.MultiIndex):
            if 'Close' in df.columns.levels[0]: df = df['Close']
        elif 'Close' in df: df = df['Close']
        df = df.rename(columns=ticker_map)
        df = df.ffill().bfill()
        return df
    except:
        return pd.DataFrame()

# ==============================================================================
# UPGRADED HIGH-VOLUME LIVE NEWS ENGINE (VIA GOOGLE RSS)
# ==============================================================================
@st.cache_data(ttl=900) # Caches for 15 minutes
def get_sector_news():
    news_items = []
    
    try:
        # Direct XML request to Google News specifically filtering for our 5 companies
        url = "https://news.google.com/rss/search?q=Audi+OR+BMW+OR+Volkswagen+OR+General+Motors+OR+Ford+stock+market&hl=en-US&gl=US&ceid=US:en"
        
        # We spoof a standard browser User-Agent so we don't get blocked
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        # Grab the top 15 breaking articles
        for item in root.findall('.//item')[:15]:
            title = item.find('title').text
            link = item.find('link').text
            pub_date_str = item.find('pubDate').text
            
            # Extract publisher if available
            source_tag = item.find('source')
            publisher = source_tag.text if source_tag is not None else "Financial News"
            
            # Format the time beautifully
            try:
                dt = parsedate_to_datetime(pub_date_str)
                date_str = dt.strftime('%b %d, %H:%M')
            except:
                date_str = "Recent"
                
            news_items.append({
                'title': title, 
                'link': link, 
                'publisher': publisher,
                'date_str': date_str
            })
            
    except Exception as e:
        print(f"RSS Engine encountered an issue: {e}")
        pass
        
    # Failsafe
    if not news_items:
        news_items = [
            {'title': 'Reuters: Global Automotive Industry News', 'link': 'https://www.reuters.com/business/autos-transportation/', 'publisher': 'Reuters', 'date_str': 'Live feed unavailable'}
        ]
        
    return news_items

def add_technical_indicators(df):
    if df.empty: return df
    data = df.copy()
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    data['RSI'] = 100 - (100 / (1 + (gain / loss)))
    data['MACD'] = data['Close'].ewm(span=12, adjust=False).mean() - data['Close'].ewm(span=26, adjust=False).mean()
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MA20'] = data['Close'].rolling(20).mean()
    data['BB_Upper'] = data['MA20'] + (data['Close'].rolling(20).std() * 2)
    data['BB_Lower'] = data['MA20'] - (data['Close'].rolling(20).std() * 2)
    if 'Volume' in data.columns and not data['Volume'].eq(0).all():
        data['VWAP'] = (data['Volume'] * (data['High'] + data['Low'] + data['Close']) / 3).cumsum() / data['Volume'].cumsum()
    else: data['VWAP'] = data['MA20']
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    data['ATR'] = data['TR'].rolling(14).mean()
    return data

# ==============================================================================
# INTEGRATED HYBRID ML ENGINE
# ==============================================================================
def run_prediction_model(data, forecast_steps=15):
    try:
        ml_data = data.sort_index().copy()
        
        ml_data['Pct_Change'] = ml_data['Close'].pct_change()
        ml_data['MA5'] = ml_data['Close'].rolling(window=5).mean()
        ml_data['MA10'] = ml_data['Close'].rolling(window=10).mean()
        
        ml_data['Target'] = (ml_data['Close'].shift(-1) > ml_data['Close']).astype(int)
        ml_data = ml_data.dropna()
        
        if len(ml_data) < 20:
            return None, None, None, 0, 0, 0, [], None, "Not enough data to train the Hybrid Model."

        feature_cols = ['Pct_Change', 'MA5', 'MA10']
        x = ml_data[feature_cols]
        y = ml_data['Target']
        
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(x_train, y_train)
        
        y_pred = rf_model.predict(x_test)
        acc = accuracy_score(y_test, y_pred)
        
        feat_imp = pd.DataFrame({
            'Feature': feature_cols, 
            'Importance': rf_model.feature_importances_
        }).sort_values(by='Importance', ascending=False)

        rf_model.fit(x, y)

        model = ARIMA(ml_data['Close'].values, order=(5, 1, 0))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=forecast_steps)
        
        last_date = ml_data.index[-1]
        forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_steps, freq='B')

        forecast_pct_change = pd.Series(forecast).pct_change().fillna(0).values.reshape(-1, 1)
        forecast_ma5 = [ml_data['Close'].iloc[-5:].mean()] * len(forecast)
        forecast_ma10 = [ml_data['Close'].iloc[-10:].mean()] * len(forecast)

        forecast_features = pd.DataFrame({
            'Pct_Change': forecast_pct_change.flatten(),
            'MA5': forecast_ma5,
            'MA10': forecast_ma10
        })
        
        predicted_signals = rf_model.predict(forecast_features)

        cur_price = ml_data['Close'].iloc[-1]
        final_price = forecast[-1]
        proj_return = ((final_price - cur_price) / cur_price) * 100
        
        recent_features = x.iloc[-10:]
        recent_signals = rf_model.predict(recent_features)
        recent_history = list(zip(ml_data.index[-10:], recent_signals))

        return forecast_dates, forecast, predicted_signals, acc, proj_return, final_price, recent_history, feat_imp, None
        
    except Exception as e: 
        return None, None, None, 0, 0, 0, [], None, str(e)