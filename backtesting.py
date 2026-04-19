import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- CORE BACKTESTING LOGIC ---
def run_sma_crossover_backtest(df, fast_window, slow_window, initial_capital):
    """Vectorized backtest for a Simple Moving Average Crossover strategy."""
    data = df.copy()
    
    # Calculate Moving Averages
    data['SMA_Fast'] = data['Close'].rolling(window=fast_window).mean()
    data['SMA_Slow'] = data['Close'].rolling(window=slow_window).mean()
    
    # Generate Signals (1 = Buy, 0 = Sell/Flat)
    data['Signal'] = 0
    data.loc[data['SMA_Fast'] > data['SMA_Slow'], 'Signal'] = 1
    
    # Calculate Position Changes (1 = Entry, -1 = Exit)
    data['Position'] = data['Signal'].diff()
    
    # Calculate Returns
    data['Market_Returns'] = data['Close'].pct_change()
    data['Strategy_Returns'] = data['Market_Returns'] * data['Signal'].shift(1)
    
    # Calculate Equity Curve
    data['Strategy_Returns'] = data['Strategy_Returns'].fillna(0)
    data['Equity'] = initial_capital * (1 + data['Strategy_Returns']).cumprod()
    
    # Calculate Drawdown
    data['Peak'] = data['Equity'].cummax()
    data['Drawdown'] = (data['Equity'] - data['Peak']) / data['Peak']
    
    return data

def run_rsi_mean_reversion_backtest(df, rsi_window, rsi_oversold, rsi_overbought, initial_capital):
    """Vectorized backtest for an RSI Mean Reversion strategy."""
    data = df.copy()
    
    # Calculate RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_window).mean()
    
    # Avoid division by zero
    loss = loss.replace(0, np.nan)
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data['RSI'] = data['RSI'].fillna(100) # Fallback
    
    # Generate Signals (1 = Buy, 0 = Flat)
    data['Signal'] = np.nan
    data.loc[data['RSI'] < rsi_oversold, 'Signal'] = 1  # Buy when oversold
    data.loc[data['RSI'] > rsi_overbought, 'Signal'] = 0 # Sell when overbought
    
    # Forward fill signals: hold position until sell signal
    data['Signal'] = data['Signal'].ffill().fillna(0)
    
    # Calculate Position Changes (1 = Entry, -1 = Exit)
    data['Position'] = data['Signal'].diff()
    
    # Calculate Returns
    data['Market_Returns'] = data['Close'].pct_change()
    data['Strategy_Returns'] = data['Market_Returns'] * data['Signal'].shift(1)
    
    # Calculate Equity Curve
    data['Strategy_Returns'] = data['Strategy_Returns'].fillna(0)
    data['Equity'] = initial_capital * (1 + data['Strategy_Returns']).cumprod()
    
    # Calculate Drawdown
    data['Peak'] = data['Equity'].cummax()
    data['Drawdown'] = (data['Equity'] - data['Peak']) / data['Peak']
    
    return data

def render():
    st.markdown('<h1 class="gradient-text">Quantitative Backtesting</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#8fc1d4; margin-bottom:20px;'>Simulate algorithmic trading strategies against historical market data.</p>", unsafe_allow_html=True)

    # --- STRATEGY CONFIGURATION (SIDEBAR) ---
    st.sidebar.markdown("## ⚙️ Strategy Sandbox")
    
    asset_map = {
        "Audi": "AUD.csv",
        "BMW": "BMW.DE.csv",  
        "VW": "VWAGY.csv",   
        "GM": "GM.csv",
        "Ford": "FORD.csv"         
    }
    
    selected_asset = st.sidebar.selectbox("Test Asset", list(asset_map.keys()))
    initial_capital = st.sidebar.number_input("Initial Capital ($)", min_value=1000, value=100000, step=10000)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Algorithm Parameters")
    
    # --- NEW DYNAMIC UI MENU ---
    strategy_type = st.sidebar.selectbox("Strategy Type", ["SMA Crossover", "RSI Mean Reversion"])
    
    if strategy_type == "SMA Crossover":
        fast_ma = st.sidebar.slider("Fast Moving Average", min_value=5, max_value=50, value=20)
        slow_ma = st.sidebar.slider("Slow Moving Average", min_value=20, max_value=200, value=50)
        lookback_requirement = slow_ma
    else: # RSI Mean Reversion
        rsi_window = st.sidebar.slider("RSI Window", min_value=5, max_value=30, value=14)
        rsi_oversold = st.sidebar.slider("Oversold Threshold (Buy)", min_value=10, max_value=40, value=30)
        rsi_overbought = st.sidebar.slider("Overbought Threshold (Sell)", min_value=60, max_value=90, value=70)
        lookback_requirement = rsi_window

    # --- DATA LOADING & CLEANING ---
    current_file = asset_map[selected_asset]
    if not os.path.exists(current_file):
        st.error(f"⚠️ Missing historical data for {selected_asset}. Please ensure `{current_file}` is in the directory.")
        return

    try:
        df = pd.read_csv(current_file)
        if 'Date' in df.columns: 
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        elif 'date' in df.columns: 
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns: 
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
        df = df.dropna(subset=['Close']).sort_index()
    except Exception as e:
        st.error(f"⚠️ Data formatting error: {e}")
        return

    # THE BUG FIX: It now checks against whatever parameter the active strategy is using!
    if len(df) < lookback_requirement + 1:
        st.warning(f"Not enough data points to calculate strategy indicators. Need more historical data.")
        return

    # --- EXECUTE BACKTEST ---
    with st.spinner(f"Simulating {strategy_type} on {selected_asset}..."):
        if strategy_type == "SMA Crossover":
            results = run_sma_crossover_backtest(df, fast_ma, slow_ma, initial_capital)
        elif strategy_type == "RSI Mean Reversion":
            results = run_rsi_mean_reversion_backtest(df, rsi_window, rsi_oversold, rsi_overbought, initial_capital)

    # --- KPI METRICS CALCULATION ---
    final_equity = results['Equity'].iloc[-1]
    total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100
    max_drawdown_pct = results['Drawdown'].min() * 100
    total_trades = results['Position'].abs().sum() / 2  # Entry + Exit = 1 Trade
    
    buy_hold_equity = initial_capital * (1 + results['Market_Returns'].fillna(0)).cumprod()
    buy_hold_return = ((buy_hold_equity.iloc[-1] - initial_capital) / initial_capital) * 100

    # Color logic
    ret_color = "#92FE9D" if total_return_pct >= 0 else "#FF3B30"
    bh_color = "#00C9FF" if total_return_pct > buy_hold_return else "#aaa"

    # --- RENDER KPI DASHBOARD ---
    st.markdown("<p class='section-title'>SIMULATION RESULTS</p>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    
    k1.markdown(f'''
    <div class="kpi-card" style="border-color: {ret_color};">
        <p class="metric-label">Net Profit / Loss</p>
        <h2 style="margin:0; font-size:1.8rem; font-weight:800; color:{ret_color};">${final_equity - initial_capital:,.2f}</h2>
        <p style="margin:0; font-size:12px; color:{ret_color};">({total_return_pct:+.2f}%)</p>
    </div>
    ''', unsafe_allow_html=True)
    
    k2.markdown(f'''
    <div class="kpi-card">
        <p class="metric-label">Max Drawdown</p>
        <h2 style="margin:0; font-size:1.8rem; font-weight:800; color:#FF3B30;">{max_drawdown_pct:.2f}%</h2>
        <p style="margin:0; font-size:12px; color:#aaa;">Peak-to-Trough Risk</p>
    </div>
    ''', unsafe_allow_html=True)
    
    k3.markdown(f'''
    <div class="kpi-card">
        <p class="metric-label">Total Trades Executed</p>
        <h2 style="margin:0; font-size:1.8rem; font-weight:800; color:white;">{int(total_trades)}</h2>
        <p style="margin:0; font-size:12px; color:#aaa;">Round trips (Buy & Sell)</p>
    </div>
    ''', unsafe_allow_html=True)

    k4.markdown(f'''
    <div class="kpi-card" style="border-color: rgba(255,255,255,0.1);">
        <p class="metric-label">Buy & Hold Benchmark</p>
        <h2 style="margin:0; font-size:1.8rem; font-weight:800; color:{bh_color};">{buy_hold_return:+.2f}%</h2>
        <p style="margin:0; font-size:12px; color:#aaa;">Vs. Strategy Return</p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- INTERACTIVE DUAL-CHART VISUALIZATION ---
    st.markdown("<p class='section-title'>TECHNICAL EXECUTION & EQUITY CURVE</p>", unsafe_allow_html=True)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, 
                        row_heights=[0.6, 0.4], 
                        subplot_titles=(f"{selected_asset} Price & Signals", "Portfolio Equity Curve"))

    # 1. Price Chart
    fig.add_trace(go.Candlestick(x=results.index, open=results['Open'], high=results['High'], low=results['Low'], close=results['Close'], name="Price", increasing_line_color='#92FE9D', decreasing_line_color='#FF3B30'), row=1, col=1)
    
    buy_signals = results[results['Position'] == 1]
    sell_signals = results[results['Position'] == -1]

    # Dynamic Chart Logic depending on Strategy
    if strategy_type == "SMA Crossover":
        fig.add_trace(go.Scatter(x=results.index, y=results['SMA_Fast'], line=dict(color='#00C9FF', width=1.5), name=f"Fast SMA ({fast_ma})"), row=1, col=1)
        fig.add_trace(go.Scatter(x=results.index, y=results['SMA_Slow'], line=dict(color='#FFD700', width=1.5), name=f"Slow SMA ({slow_ma})"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['SMA_Fast'], mode='markers', marker=dict(color='#92FE9D', symbol='triangle-up', size=12, line=dict(color='black', width=1)), name='BUY Signal'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['SMA_Fast'], mode='markers', marker=dict(color='#FF3B30', symbol='triangle-down', size=12, line=dict(color='black', width=1)), name='SELL Signal'), row=1, col=1)
    else:
        # For RSI, we plot the execution signals slightly above/below the candlestick wicks
        fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'] * 0.98, mode='markers', marker=dict(color='#92FE9D', symbol='triangle-up', size=14, line=dict(color='black', width=1)), name='BUY Signal'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Close'] * 1.02, mode='markers', marker=dict(color='#FF3B30', symbol='triangle-down', size=14, line=dict(color='black', width=1)), name='SELL Signal'), row=1, col=1)


    # 2. Equity Curve
    fig.add_trace(go.Scatter(x=results.index, y=results['Equity'], line=dict(color='#B026FF', width=2), name="Strategy Equity", fill='tozeroy', fillcolor='rgba(176, 38, 255, 0.1)'), row=2, col=1)
    fig.add_trace(go.Scatter(x=results.index, y=buy_hold_equity, line=dict(color='rgba(255,255,255,0.3)', width=1, dash='dot'), name="Buy & Hold"), row=2, col=1)

    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.02)', height=750, margin=dict(l=10,r=10,t=40,b=10), xaxis_rangeslider_visible=False, hovermode='x unified')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Download Trade Log
    st.markdown("<p class='section-title'>STRATEGY EXPORT</p>", unsafe_allow_html=True)
    trade_data = results[results['Position'] != 0].copy()
    if not trade_data.empty:
        trade_data['Action'] = trade_data['Position'].map({1: 'BUY', -1: 'SELL'})
        
        if strategy_type == "SMA Crossover":
            export_df = trade_data[['Action', 'Close', 'SMA_Fast', 'SMA_Slow', 'Equity']]
        else:
            export_df = trade_data[['Action', 'Close', 'RSI', 'Equity']]

        export_csv = export_df.to_csv().encode('utf-8')
        st.download_button(label=f"📥 Download {strategy_type} Trade Log", data=export_csv, file_name=f'backtest_log_{selected_asset}.csv', mime='text/csv', use_container_width=True)
    else:
        st.info("No trades executed with current parameters. Try adjusting the indicator thresholds.")