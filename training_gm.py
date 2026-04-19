# ==============================================================================
# AI Stock Predictor - Group C1 (Contrarian Edition + Full EDA)
# Team: Harsh Anandan Nair, Aryan Choudhury, Jenil Patel
# Logic: Buy on Predicted Drop / Sell on Predicted Rise
# ==============================================================================

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import plotly.graph_objects as go
import plotly.express as px

# 1. DATA INGESTION (Matching your GM.csv structure)
# ------------------------------------------------------------------------------
csv_path = Path(__file__).with_name('GM.csv')
data = pd.read_csv(csv_path)

# Formatting dates for the data
try:
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')
except:
    data['Date'] = pd.to_datetime(data['Date'], format='%d-%m-%Y')
data.sort_values('Date', inplace=True)
data.set_index('Date', inplace=True)

# 2. FEATURE ENGINEERING
# ------------------------------------------------------------------------------
data['Pct_Change'] = data['Close'].pct_change()
data['MA5'] = data['Close'].rolling(window=5).mean()
data['MA10'] = data['Close'].rolling(window=10).mean()

# REVERSED LOGIC: 1 = BUY (Price Drop), 0 = SELL (Price Rise)
data['Target'] = (data['Close'].shift(-1) < data['Close']).astype(int)
data = data.dropna()

# ------------------------------------------------------------------------------
# 3. EXPLORATORY DATA ANALYSIS (EDA)
# ------------------------------------------------------------------------------
print("\n--- Starting Calculative EDA ---")

# A. Statistical Summary
print("\n[Dataset Snapshot]")
print(data[['Close', 'Volume', 'Pct_Change']].describe())

# B. Plot 1: Historical Candlestick Chart
# Gives us the "vibe" of the 1972 market volatility
fig_candle = go.Figure(data=[go.Candlestick(
    x=data.index,
    open=data['Open'], high=data['High'],
    low=data['Low'], close=data['Close'],
    name='Price'
)])
fig_candle.update_layout(title='Ford Historical Price Action (1972 Era)', template='plotly_dark')
fig_candle.show()

# C. Plot 2: Correlation Heatmap
# Checking which features actually influence our Contrarian Target
corr_matrix = data.corr()
fig_corr = px.imshow(
    corr_matrix, text_auto=True, aspect="auto",
    color_continuous_scale='RdBu_r',
    title="Feature Correlation Heatmap (Focus on Target)"
)
fig_corr.show()

# D. Plot 3: Contrarian Target Distribution
# Are there more 'Buy the Dip' opportunities or 'Sell the Peak' ones?
target_counts = data['Target'].value_counts().reset_index()
target_counts.columns = ['Target', 'Count']
target_counts['Label'] = target_counts['Target'].map({1: 'Predicted DROP (BUY)', 0: 'Predicted RISE (SELL)'})

fig_dist = px.pie(
    target_counts, values='Count', names='Label',
    title='Market Opportunity Distribution',
    color_discrete_sequence=['#ef553b', '#00cc96'] # Red for Rise, Green for Drop
)
fig_dist.show()

print("--- EDA Complete ---\n")

# ------------------------------------------------------------------------------
# 4. RANDOM FOREST ML LOGIC
# ------------------------------------------------------------------------------
features = ['Open', 'High', 'Low', 'Close', 'Volume', 'Pct_Change', 'MA5', 'MA10']
X = data[features]
y = data['Target']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

print("Training Random Forest on Contrarian Logic...")
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# 5. EVALUATION & FINAL VISUALIZATION
# ------------------------------------------------------------------------------
y_pred = rf_model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")

# Visualizing the last 50 days of predictions
results = data.tail(50).copy()
results['Signal'] = rf_model.predict(results[features])

fig_final = go.Figure()
fig_final.add_trace(go.Scatter(x=results.index, y=results['Close'], mode='lines', name='Price'))

# Buy signals (Green Triangles) where model predicts a drop
buys = results[results['Signal'] == 1]
fig_final.add_trace(go.Scatter(
    x=buys.index, y=buys['Close'], mode='markers',
    marker=dict(symbol='triangle-up', size=12, color='lime'),
    name='BUY (Predicted Drop)'
))

# Sell signals (Red Triangles) where model predicts a rise
sells = results[results['Signal'] == 0]
fig_final.add_trace(go.Scatter(
    x=sells.index, y=sells['Close'], mode='markers',
    marker=dict(symbol='triangle-down', size=12, color='red'),
    name='SELL (Predicted Rise)'
))

fig_final.update_layout(title='Final Contrarian Trade Signals', template='plotly_white')
fig_final.show()