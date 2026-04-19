# portfolio.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import datetime
import requests
from utils import get_auto_tickers_data, AESTHETIC_COLORS

# ── API Configuration ─────────────────────────────
API_BASE = "http://localhost:8000"

# ── Portfolio Database Initialization ────────────
def init_portfolio():
    if 'balance' not in st.session_state:
        st.session_state.balance = 100000.0
    if 'positions' not in st.session_state:
        st.session_state.positions = {}
    if 'trade_log' not in st.session_state:
        st.session_state.trade_log = []
    if 'equity_history' not in st.session_state:
        st.session_state.equity_history = [{
            'time'  : datetime.datetime.now().strftime("%H:%M:%S"),
            'equity': 100000.0
        }]

# ── Order Confirmation Modal ──────────────────────
@st.dialog("🔒 Order Confirmation & Risk Check")
def order_confirmation_modal(action, asset, qty, price):

    # Validate price
    if price <= 0:
        st.error("Market API Error: Asset price is registering as $0.00. Trading halted.")
        return

    cost_or_revenue = qty * price

    # Pre-trade validation
    if action == "BUY":
        if st.session_state.balance < cost_or_revenue:
            st.error(
                f"**Rejected:** Insufficient Buying Power.\n\n"
                f"Required: ${cost_or_revenue:,.2f} | "
                f"Available: ${st.session_state.balance:,.2f}"
            )
            return
        theme_color = "#00C9FF"
        action_text = "TOTAL COST"

    elif action == "SELL":
        owned_shares = st.session_state.positions.get(asset, {}).get('shares', 0)
        if owned_shares < qty:
            st.error(
                f"**Rejected:** Insufficient Inventory (Naked Shorting Blocked).\n\n"
                f"Attempted to sell: {qty} shares | "
                f"Currently own: {owned_shares} shares."
            )
            return
        theme_color = "#ef473a"
        action_text = "ESTIMATED PROCEEDS"

    # Order summary display
    st.markdown(f"### Review your {action} order for {asset}")
    st.markdown(f"""
    <div style="background:rgba(0,0,0,0.3);padding:15px;border-radius:10px;
                border-left:4px solid {theme_color};margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;">
            <span>Action:</span><strong>{action}</strong>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span>Quantity:</span><strong>{qty} Shares</strong>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span>Quoted Price:</span><strong>${price:,.2f}</strong>
        </div>
        <hr style="border-color:rgba(255,255,255,0.1);margin:10px 0;">
        <div style="display:flex;justify-content:space-between;
                    color:{theme_color};font-size:18px;">
            <span>{action_text}:</span>
            <strong>${cost_or_revenue:,.2f}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Execute button
    if st.button("✅ AUTHORIZE & EXECUTE TRADE", type="primary", use_container_width=True):

        # ── STEP 1: Update session state ──────────────
        if action == "BUY":
            st.session_state.balance -= cost_or_revenue
            if asset in st.session_state.positions:
                old_qty = st.session_state.positions[asset]['shares']
                old_avg = st.session_state.positions[asset]['avg_price']
                new_qty = old_qty + qty
                new_avg = ((old_qty * old_avg) + cost_or_revenue) / new_qty
                st.session_state.positions[asset] = {
                    'shares'   : new_qty,
                    'avg_price': new_avg
                }
            else:
                st.session_state.positions[asset] = {
                    'shares'   : qty,
                    'avg_price': price
                }

        elif action == "SELL":
            st.session_state.balance += cost_or_revenue
            st.session_state.positions[asset]['shares'] -= qty
            if st.session_state.positions[asset]['shares'] == 0:
                del st.session_state.positions[asset]

        # ── STEP 2: Write to session state audit log ──
        st.session_state.trade_log.insert(0, {
            'Time'  : datetime.datetime.now().strftime("%H:%M:%S"),
            'Action': action,
            'Asset' : asset,
            'Qty'   : qty,
            'Price' : f"${price:.2f}",
            'Value' : f"${cost_or_revenue:.2f}"
        })

        # ── STEP 3: Save to trades.db via FastAPI ─────
        user_email = st.session_state.get("user_email", "guest@stockapp.com")

        payload = {
            "user_email"   : user_email,
            "action"       : action,
            "asset"        : asset,
            "quantity"     : qty,
            "price"        : price,
            "total_value"  : cost_or_revenue,
            "balance_after": st.session_state.balance
        }

        try:
            response = requests.post(
                f"{API_BASE}/trades/save",
                json=payload,
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                if "error" not in result:
                    st.toast(
                        f"✅ {action} executed & saved! "
                        f"Trade ID: #{result.get('trade_id', '?')}"
                    )
                else:
                    st.toast(f"⚠️ Trade done but DB error: {result['error']}")
            else:
                st.toast(f"⚠️ Trade done but server error: {response.status_code}")

        except requests.exceptions.ConnectionError:
            st.toast("⚠️ Trade executed but FastAPI is not running — not saved to DB")
        except requests.exceptions.Timeout:
            st.toast("⚠️ Trade executed but request timed out")
        except Exception as e:
            st.toast(f"⚠️ Trade executed but unexpected error: {e}")

        st.rerun()


# ── Main Render Function ──────────────────────────
def render():
    init_portfolio()

    st.markdown('<h1 class="gradient-text">Portfolio Performance</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#8fc1d4;'>Manage active positions, execution, and historical analytics.</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Live prices
    live_data   = get_auto_tickers_data()
    live_prices = {k: v[0] for k, v in live_data.items()}

    # Account calculations
    positions_value = sum([
        data['shares'] * live_prices.get(asset, data['avg_price'])
        for asset, data in st.session_state.positions.items()
    ])
    total_equity = st.session_state.balance + positions_value
    total_pl     = total_equity - 100000.0
    pl_color     = "#92FE9D" if total_pl >= 0 else "#ef473a"
    pl_arrow     = "▲" if total_pl >= 0 else "▼"

    # Update equity history
    if total_equity != st.session_state.equity_history[-1]['equity']:
        st.session_state.equity_history.append({
            'time'  : datetime.datetime.now().strftime("%H:%M:%S"),
            'equity': total_equity
        })

    # ── Account Summary ───────────────────────────
    st.markdown("<p class='section-title'>ACCOUNT SUMMARY</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'''
        <div class="kpi-card">
            <p class="metric-label">Buying Power</p>
            <h2 style="margin:0;font-size:2.2rem;font-weight:800;color:#00C9FF;">
                ${st.session_state.balance:,.2f}
            </h2>
        </div>''', unsafe_allow_html=True)
    c2.markdown(f'''
        <div class="kpi-card">
            <p class="metric-label">Open Positions Value</p>
            <h2 style="margin:0;font-size:2.2rem;font-weight:800;color:white;">
                ${positions_value:,.2f}
            </h2>
        </div>''', unsafe_allow_html=True)
    c3.markdown(f'''
        <div class="kpi-card" style="border-color:{pl_color};">
            <p class="metric-label">Total P/L (All Time)</p>
            <h2 style="margin:0;font-size:2.2rem;font-weight:800;color:{pl_color};">
                {pl_arrow} ${abs(total_pl):,.2f}
            </h2>
        </div>''', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────
    chart_c1, chart_c2 = st.columns([1, 2.5], gap="large")

    with chart_c1:
        st.markdown("<p class='section-title'>ASSET ALLOCATION</p>", unsafe_allow_html=True)
        labels = ['Cash'] + list(st.session_state.positions.keys())
        values = [st.session_state.balance] + [
            data['shares'] * live_prices.get(a, data['avg_price'])
            for a, data in st.session_state.positions.items()
        ]
        colors = ['#00C9FF'] + AESTHETIC_COLORS[:len(st.session_state.positions)]

        fig_pie = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=.7,
            marker_colors=colors, textinfo="none",
            hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>"
        )])
        fig_pie.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=250,
            margin=dict(l=0, r=0, t=10, b=10),
            showlegend=False
        )

        invested_pct = (positions_value / total_equity) * 100 if total_equity > 0 else 0
        fig_pie.add_annotation(
            text=f"{invested_pct:.0f}%", x=0.5, y=0.55,
            font_size=28, font_weight="bold", font_color="white", showarrow=False
        )
        fig_pie.add_annotation(
            text="INVESTED", x=0.5, y=0.40,
            font_size=10, font_color="#8fc1d4", showarrow=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_c2:
        st.markdown("<p class='section-title'>PORTFOLIO EQUITY CURVE</p>", unsafe_allow_html=True)
        df_eq   = pd.DataFrame(st.session_state.equity_history)
        fig_eq  = px.area(df_eq, x='time', y='equity', color_discrete_sequence=['#92FE9D'])
        fig_eq.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=250,
            margin=dict(l=0, r=0, t=10, b=10),
            xaxis_title="", yaxis_title=""
        )
        fig_eq.update_traces(line=dict(width=3), fillcolor="rgba(146,254,157,0.1)")

        min_eq = df_eq['equity'].min()
        max_eq = df_eq['equity'].max()
        buffer = (max_eq - min_eq) * 0.1 if max_eq != min_eq else 1000
        fig_eq.update_yaxes(range=[min_eq - buffer, max_eq + buffer])
        st.plotly_chart(fig_eq, use_container_width=True)

    # ── Trade Execution Terminal ───────────────────
    st.markdown("<p class='section-title' style='margin-top:20px;'>MARKET EXECUTION TERMINAL</p>", unsafe_allow_html=True)
    t_c1, t_c2, t_c3 = st.columns([1.5, 1, 1], gap="medium")

    with t_c1:
        target_asset  = st.selectbox(
            "Target Asset",
            ["Audi", "BMW", "Ford", "GM", "VW"],
            label_visibility="collapsed"
        )
        trade_qty     = st.number_input(
            "Quantity (Shares)",
            min_value=1, value=10, step=1,
            label_visibility="collapsed"
        )
        current_price = live_prices.get(target_asset, 0.0)
        st.markdown(
            f"<p style='color:#8fc1d4;font-size:13px;'>"
            f"Market Price: <b style='color:white;'>${current_price:.2f}</b> | "
            f"Est. Total: <b style='color:white;'>${(current_price * trade_qty):,.2f}</b>"
            f"</p>",
            unsafe_allow_html=True
        )

    with t_c2:
        if st.button("🟢 EXECUTE BUY", key="buy_btn", use_container_width=True):
            order_confirmation_modal("BUY", target_asset, trade_qty, current_price)

    with t_c3:
        if st.button("🔴 EXECUTE SELL", key="sell_btn", use_container_width=True):
            order_confirmation_modal("SELL", target_asset, trade_qty, current_price)

    # ── Open Positions Ledger ──────────────────────
    st.markdown("<p class='section-title' style='margin-top:30px;'>OPEN POSITIONS LEDGER</p>", unsafe_allow_html=True)
    if st.session_state.positions:
        ledger_data = []
        for asset, data in st.session_state.positions.items():
            cur_p        = live_prices.get(asset, data['avg_price'])
            unrealized_pl = (cur_p - data['avg_price']) * data['shares']
            pl_pct        = ((cur_p - data['avg_price']) / data['avg_price']) * 100 if data['avg_price'] > 0 else 0.0
            ledger_data.append({
                "Asset"             : asset,
                "Shares"            : data['shares'],
                "Avg Entry"         : f"${data['avg_price']:.2f}",
                "Current Price"     : f"${cur_p:.2f}",
                "Unrealized P/L ($)": unrealized_pl,
                "Return (%)"        : pl_pct
            })

        df_ledger = pd.DataFrame(ledger_data)
        st.dataframe(
            df_ledger.style
            .map(
                lambda x: 'color:#92FE9D;font-weight:bold;' if x > 0
                else ('color:#ef473a;font-weight:bold;' if x < 0 else ''),
                subset=['Unrealized P/L ($)', 'Return (%)']
            )
            .format({
                'Unrealized P/L ($)': "${:.2f}",
                'Return (%)': "{:.2f}%"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No open positions. Execute a trade in the terminal above to begin.")

    # ── Trade Audit Log ───────────────────────────
    st.markdown("<p class='section-title' style='margin-top:30px;'>TRADE AUDIT LOG</p>", unsafe_allow_html=True)
    if st.session_state.trade_log:
        df_log = pd.DataFrame(st.session_state.trade_log)
        st.dataframe(df_log, use_container_width=True, hide_index=True)

        # ── View all trades from database ─────────
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📋 Load All Trades from Database", use_container_width=True):
            try:
                user_email = st.session_state.get("user_email", "guest@stockapp.com")
                r = requests.get(f"{API_BASE}/trades/user/{user_email}", timeout=5)
                if r.status_code == 200:
                    db_trades = r.json()
                    if db_trades:
                        st.success(f"✅ {len(db_trades)} trade(s) found in database:")
                        st.dataframe(pd.DataFrame(db_trades), use_container_width=True, hide_index=True)
                    else:
                        st.info("No trades found in database for this user.")
                else:
                    st.error(f"❌ Error {r.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("❌ FastAPI is not running.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.caption("No historical trades recorded.")