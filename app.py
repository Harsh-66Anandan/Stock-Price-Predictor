# app.py
import streamlit as st

# ── MUST BE FIRST ─────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Stock Price Predictor",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════
# AUTO START FASTAPI IN BACKGROUND THREAD
# ══════════════════════════════════════════════════
import threading
import time
import requests

@st.cache_resource
def start_fastapi():
    """Start FastAPI once in background thread. Never runs twice."""
    def run():
        import uvicorn
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            log_level="error",
            reload=False
        )
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

def wait_for_fastapi(retries=20, delay=0.5):
    """Wait until FastAPI is ready to accept requests."""
    for _ in range(retries):
        try:
            requests.get("http://localhost:8000/health", timeout=1)
            return True
        except:
            time.sleep(delay)
    return False

def is_fastapi_running():
    """Quick check if FastAPI is up."""
    try:
        requests.get("http://localhost:8000/health", timeout=1)
        return True
    except:
        return False

# ── Start FastAPI (only once due to cache_resource) ──
start_fastapi()

# ── Wait for it to be ready ───────────────────────
if not is_fastapi_running():
    with st.spinner("⏳ Starting backend server..."):
        ready = wait_for_fastapi()
    if not ready:
        st.error("❌ Backend failed to start. Please restart the app.")
        st.stop()

# ══════════════════════════════════════════════════
# IMPORTS
# ══════════════════════════════════════════════════
import auth
import dashboard
import terminal
import backtesting
import portfolio
import user_profile

# ══════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════
API_URL = "http://localhost:8000"

# ══════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ══════════════════════════════════════════════════
if "is_authenticated"  not in st.session_state: st.session_state.is_authenticated  = False
if "auth_view"         not in st.session_state: st.session_state.auth_view         = "login"
if "show_auth_modal"   not in st.session_state: st.session_state.show_auth_modal   = False
if "current_username"  not in st.session_state: st.session_state.current_username  = None
if "display_name"      not in st.session_state: st.session_state.display_name      = "User"
if "profile_image"     not in st.session_state: st.session_state.profile_image     = None
if "user_email"        not in st.session_state: st.session_state.user_email        = ""
if "nav_selection"     not in st.session_state: st.session_state.nav_selection     = "🏠 Market Overview"

# ══════════════════════════════════════════════════
# AUTO-RESTORE SESSION ON PAGE REFRESH
# ══════════════════════════════════════════════════
if not st.session_state.is_authenticated and st.session_state.current_username:
    """User was logged in before refresh — validate with backend"""
    try:
        res = requests.get(
            f"{API_URL}/auth/validate-session/{st.session_state.current_username}",
            timeout=5
        )
        data = res.json()
        if data.get("success"):
            # Session still valid — restore login state
            st.session_state.is_authenticated = True
            st.session_state.display_name     = data.get("display_name", "User")
            st.session_state.user_email       = data.get("email", "")
            st.session_state.profile_image    = data.get("profile_image")
    except:
        pass  # If validation fails, user stays logged out

# ══════════════════════════════════════════════════
# FORCE RERUN IF JUST AUTHENTICATED
# ══════════════════════════════════════════════════
# None needed - Streamlit autom reruns when session state changes!

# When login succeeds, close the modal
if st.session_state.is_authenticated and st.session_state.show_auth_modal:
    st.session_state.show_auth_modal = False

# ══════════════════════════════════════════════════
# AUTH GATE — block app until logged in
# ══════════════════════════════════════════════════
if not st.session_state.is_authenticated:

    st.markdown("""
        <div style="text-align:center; padding:80px 0 20px 0;">
            <h1 style="background:linear-gradient(to right,#00C9FF,#92FE9D);
                       -webkit-background-clip:text;
                       -webkit-text-fill-color:transparent;
                       font-size:3rem; font-weight:900;">
                Stock Price Predictor
            </h1>
            <p style="color:#8fc1d4; font-size:16px; letter-spacing:2px;">
                ENTERPRISE EDITION
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ── API status indicator ──────────────────────
    if is_fastapi_running():
        st.markdown("""
            <div style="text-align:center; margin-bottom:20px;">
                <span style="background:rgba(146,254,157,0.1);
                             border:1px solid #92FE9D;
                             border-radius:20px; padding:6px 20px;
                             font-size:12px; color:#92FE9D;">
                    ● BACKEND ONLINE
                </span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align:center; margin-bottom:20px;">
                <span style="background:rgba(255,59,48,0.1);
                             border:1px solid #FF3B30;
                             border-radius:20px; padding:6px 20px;
                             font-size:12px; color:#FF3B30;">
                    ● BACKEND OFFLINE
                </span>
            </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔐 Login / Register",
                     use_container_width=True,
                     type="primary"):
            st.session_state.show_auth_modal = True
            st.session_state.auth_view = "login"

    # ── Only render modal if NOT authenticated ──
    if st.session_state.show_auth_modal and not st.session_state.is_authenticated:
        auth.auth_modal()
    elif st.session_state.is_authenticated:
        # Just authenticated - close modal and stop showing login
        st.session_state.show_auth_modal = False
    
    st.stop()  # ← nothing below runs until logged in

# ══════════════════════════════════════════════════
# LOGGED IN — RENDER FULL APP
# ══════════════════════════════════════════════════

def launch_profile():
    st.session_state.nav_selection = "👤 User Profile"

def logout_user():
    """Clear all session state and return to login screen."""
    st.session_state.is_authenticated  = False
    st.session_state.auth_view         = "login"
    st.session_state.show_auth_modal   = False
    st.session_state.current_username  = None
    st.session_state.display_name      = "User"
    st.session_state.profile_image     = None
    st.session_state.user_email        = ""
    st.session_state.nav_selection     = "🏠 Market Overview"
    # Don't call st.rerun() here — button callback already triggers rerun

# ── Dynamic avatar ────────────────────────────────
display_text = (st.session_state.display_name
                or st.session_state.current_username
                or "User")

if st.session_state.profile_image:
    avatar_style   = (f"background-image:url('data:image/png;base64,"
                      f"{st.session_state.profile_image}');"
                      f"background-size:cover;"
                      f"background-position:center;"
                      f"color:transparent !important;")
    avatar_content = "\u00A0"
else:
    initial        = display_text[0].upper() if display_text else "U"
    avatar_style   = "background:linear-gradient(135deg,#00C9FF,#92FE9D);color:#0a151c !important;"
    avatar_content = initial

# ── Global CSS ────────────────────────────────────
st.markdown(f"""
<style>
    header[data-testid="stHeader"] {{
        visibility: visible !important;
        background-color: rgba(15,32,39,0.8) !important;
        backdrop-filter: blur(10px);
    }}
    footer {{ display: none !important; }}

    .stApp {{
        background: linear-gradient(135deg,#0f2027 0%,#203a43 50%,#2c5364 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }}

    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] span#top-profile-locator) {{
        height:0px !important; margin:0 !important; padding:0 !important;
        gap:0 !important; overflow:visible !important;
    }}
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] span#top-profile-locator) button {{
        position: fixed !important;
        top: 80px !important;
        right: 20px !important;
        width: 45px !important;
        height: 45px !important;
        border-radius: 50% !important;
        z-index: 999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 2px solid rgba(255,255,255,0.1) !important;
        box-shadow: 0 4px 15px rgba(0,201,255,0.3) !important;
        transition: all 0.3s cubic-bezier(0.175,0.885,0.32,1.275) !important;
        padding: 0 !important;
        {avatar_style}
    }}
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] span#top-profile-locator) button p {{
        font-weight: 900 !important;
        font-size: 20px !important;
        margin: 0 !important;
        line-height: 1 !important;
    }}
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] span#top-profile-locator) button:hover {{
        transform: scale(1.15) translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(0,201,255,0.6) !important;
        border-color: #ffffff !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(10,20,25,0.6) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.05);
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        background: linear-gradient(145deg,rgba(255,255,255,0.03) 0%,rgba(255,255,255,0.01) 100%);
        padding: 12px 18px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
        cursor: pointer;
        width: 100%;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label:nth-child(5) {{
        display: none !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{
        display: none;
    }}
    .kpi-card {{
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 10px;
    }}
    .metric-label {{
        color: #8fc1d4;
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }}
    .section-title {{
        color: #8fc1d4;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }}
    .gradient-text {{
        background: linear-gradient(to right,#00C9FF,#92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .news-box {{
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# ── Floating profile icon ─────────────────────────
with st.container():
    st.markdown('<span id="top-profile-locator"></span>', unsafe_allow_html=True)
    st.button(avatar_content, key="global_profile_redirect", on_click=launch_profile)

# ── Sidebar ───────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align:center; padding:10px 0 20px 0;">
    <h2 style="background:linear-gradient(to right,#00C9FF,#92FE9D);
               -webkit-background-clip:text;
               -webkit-text-fill-color:transparent;
               font-size:1.8rem; font-weight:900; margin:0;">
        Stock Price Predictor
    </h2>
    <p style="color:#8fc1d4; font-size:11px;
              letter-spacing:2px; text-transform:uppercase; margin:0;">
        Enterprise Edition
    </p>
</div>
""", unsafe_allow_html=True)

# ── API status in sidebar ─────────────────────────
if is_fastapi_running():
    st.sidebar.markdown("""
        <div style="background:rgba(146,254,157,0.1);
                    border:1px solid #92FE9D;border-radius:8px;
                    padding:6px 12px;margin-bottom:10px;
                    font-size:11px;color:#92FE9D;text-align:center;">
            ● API CONNECTED
        </div>""", unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
        <div style="background:rgba(255,59,48,0.1);
                    border:1px solid #FF3B30;border-radius:8px;
                    padding:6px 12px;margin-bottom:10px;
                    font-size:11px;color:#FF3B30;text-align:center;">
            ● API DISCONNECTED
        </div>""", unsafe_allow_html=True)

page_selection = st.sidebar.radio(
    "NAVIGATION",
    [
        "🏠 Market Overview",
        "📈 AI Live Terminal",
        "⚙️ Backtest",
        "💼 Portfolio",
        "👤 User Profile"
    ],
    key="nav_selection",
    label_visibility="collapsed"
)

st.sidebar.markdown("<br>" * 5, unsafe_allow_html=True)

# ── Profile and Logout buttons ────────────────────
col_profile, col_logout = st.sidebar.columns(2, gap="small")
with col_profile:
    st.button(
        display_text,
        key="profile_btn",
        on_click=launch_profile,
        use_container_width=True
    )
with col_logout:
    st.button(
        "🚪 Logout",
        key="logout_btn",
        on_click=logout_user,
        use_container_width=True,
        type="secondary"
    )

# ── Page router ───────────────────────────────────
if st.session_state.nav_selection == "🏠 Market Overview":
    dashboard.render()
elif st.session_state.nav_selection == "📈 AI Live Terminal":
    terminal.render()
elif st.session_state.nav_selection == "⚙️ Backtest":
    backtesting.render()
elif st.session_state.nav_selection == "💼 Portfolio":
    portfolio.render()
elif st.session_state.nav_selection == "👤 User Profile":
    user_profile.render()