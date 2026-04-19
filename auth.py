# auth.py
import streamlit as st
import re
import time
import requests

API_URL = "http://localhost:8000"

# ── Validation helpers ─────────────────────────────────────────────────────────
def is_valid_name(name):    return bool(re.match(r"^[a-zA-Z\s]+$", name.strip()))
def is_valid_username(u):   return bool(re.match(r"^[a-zA-Z0-9_]{3,}$", u.strip()))
def is_valid_email(email):  return bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email.strip()))
def is_valid_phone(phone):  return phone.strip().isdigit() and len(phone.strip()) >= 10
def is_valid_account(acc):  return acc.strip().isdigit() and len(acc.strip()) >= 8
def is_valid_password(pwd): return len(pwd) >= 6


def auth_modal():
    # ── Session State Init ─────────────────────────────────────────────────────
    # ALL inits INSIDE this function — runs on every Streamlit rerun.
    # Module-level inits only fire once on first import and then disappear.
    if "auth_view"       not in st.session_state: st.session_state.auth_view       = "login"
    if "login_tab"       not in st.session_state: st.session_state.login_tab       = "password"
    if "otp_sent"        not in st.session_state: st.session_state.otp_sent        = False
    if "otp_email_saved" not in st.session_state: st.session_state.otp_email_saved = ""

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="
            background: rgba(10,20,25,0.9);
            border: 1px solid rgba(0,201,255,0.3);
            border-radius: 20px;
            padding: 40px 30px;
            backdrop-filter: blur(20px);
        ">
        """, unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # VIEW: LOGIN
        # Only renders when auth_view == "login" — no overlap with register form
        # ══════════════════════════════════════════════════════════════════════
        if st.session_state.auth_view == "login":

            st.markdown(
                "<p style='text-align:center;color:#8fc1d4;font-size:14px;"
                "letter-spacing:1px;'>🔒 Security Verification</p>",
                unsafe_allow_html=True
            )

            # ── Tab Switcher ──────────────────────────────────────────────────
            col_tab1, col_tab2 = st.columns(2)
            with col_tab1:
                if st.button(
                    "🔑 Password Login",
                    use_container_width=True,
                    type="primary" if st.session_state.login_tab == "password" else "secondary",
                    key="tab_password_btn"
                ):
                    st.session_state.login_tab = "password"
                    st.rerun()

            with col_tab2:
                if st.button(
                    "📧 Email OTP",
                    use_container_width=True,
                    type="primary" if st.session_state.login_tab == "otp" else "secondary",
                    key="tab_otp_btn"
                ):
                    st.session_state.login_tab = "otp"
                    st.rerun()

            st.markdown(
                "<hr style='margin:12px 0; border-color:rgba(255,255,255,0.1);'>",
                unsafe_allow_html=True
            )

            # ── PASSWORD PANEL ────────────────────────────────────────────────
            if st.session_state.login_tab == "password":
                username = st.text_input(
                    "Username", key="login_username",
                    placeholder="Enter your username"
                )
                password = st.text_input(
                    "Password", type="password", key="login_password",
                    placeholder="Enter your password"
                )

                if st.button("🔓 Login", use_container_width=True,
                             type="primary", key="pwd_login_btn"):
                    if username and password:
                        try:
                            res = requests.post(
                                f"{API_URL}/auth/login",
                                json={"username": username.strip(),
                                      "password": password.strip()},
                                timeout=5
                            )
                            data = res.json()
                            if data.get("success"):
                                st.session_state.is_authenticated = True
                                st.session_state.current_username = data.get("username")
                                st.session_state.display_name     = data.get("display_name")
                                st.session_state.user_email       = data.get("email")
                                st.session_state.profile_image    = data.get("profile_image")
                                st.session_state.nav_selection    = "🏠 Market Overview"
                                st.session_state.show_auth_modal  = False
                                st.rerun()
                            else:
                                st.error(data.get("message", "❌ Invalid credentials."))
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
                    else:
                        st.error("❌ Please fill in both fields.")

            # ── EMAIL OTP PANEL ───────────────────────────────────────────────
            elif st.session_state.login_tab == "otp":

                # STEP 1: Enter email and request OTP
                if not st.session_state.otp_sent:
                    otp_email = st.text_input(
                        "Registered Email Address",
                        placeholder="example@gmail.com",
                        key="otp_email_input"
                    )
                    if st.button("📨 Send OTP", use_container_width=True,
                                 key="send_otp_btn", type="primary"):
                        if is_valid_email(otp_email):
                            with st.spinner("Sending OTP to your inbox..."):
                                try:
                                    r = requests.post(
                                        f"{API_URL}/auth/send-otp",
                                        json={"email": otp_email.strip()},
                                        timeout=10
                                    )
                                    result = r.json()
                                    if result.get("success"):
                                        st.session_state.otp_email_saved = otp_email.strip()
                                        st.session_state.otp_sent = True
                                        st.rerun()
                                    else:
                                        st.error(result.get("message", "❌ Failed to send OTP."))
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
                        else:
                            st.error("❌ Invalid email format.")

                # STEP 2: Enter OTP and verify
                else:
                    st.success(
                        f"✅ OTP sent to **{st.session_state.otp_email_saved}**. "
                        f"Check your inbox."
                    )
                    otp_code = st.text_input(
                        "Enter 6-Digit OTP",
                        max_chars=6,
                        key="otp_code_input",
                        placeholder="123456"
                    )

                    if st.button("✅ Verify & Login", use_container_width=True,
                                 type="primary", key="verify_otp_btn"):
                        if otp_code and len(otp_code.strip()) == 6:
                            try:
                                r = requests.post(
                                    f"{API_URL}/auth/verify-otp",
                                    json={"email": st.session_state.otp_email_saved,
                                          "otp":   otp_code.strip()},
                                    timeout=5
                                )
                                result = r.json()
                                if result.get("success"):
                                    st.session_state.is_authenticated = True
                                    st.session_state.user_email       = result.get("email")
                                    st.session_state.display_name     = result.get("display_name")
                                    st.session_state.current_username = result.get("username")
                                    st.session_state.nav_selection    = "🏠 Market Overview"
                                    st.session_state.show_auth_modal  = False
                                    st.session_state.otp_sent         = False
                                    st.session_state.otp_email_saved  = ""
                                    st.rerun()
                                else:
                                    st.error(result.get("message", "❌ Wrong OTP."))
                            except Exception as e:
                                st.error(f"❌ Verification failed: {e}")
                        else:
                            st.error("❌ Please enter the full 6-digit OTP.")

                    if st.button("🔄 Use a different email",
                                 use_container_width=True, key="change_email_btn"):
                        st.session_state.otp_sent        = False
                        st.session_state.otp_email_saved = ""
                        st.rerun()

            st.markdown("---")
            if st.button("📝 New here? Create an Account",
                         use_container_width=True, key="go_register_btn"):
                st.session_state.auth_view = "register"
                st.rerun()

        # ══════════════════════════════════════════════════════════════════════
        # VIEW: REGISTER
        # Completely separate from login — no widget key conflicts possible
        # ══════════════════════════════════════════════════════════════════════
        elif st.session_state.auth_view == "register":

            st.markdown(
                "<h3 style='color:white; margin-bottom:20px;'>📝 Create New Account</h3>",
                unsafe_allow_html=True
            )

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                reg_name     = st.text_input("Full Name",       key="reg_name",     placeholder="John Doe")
                reg_email    = st.text_input("Email Address",   key="reg_email",    placeholder="john@gmail.com")
                reg_phone    = st.text_input("Phone Number",    key="reg_phone",    placeholder="10-digit number")
            with col_r2:
                reg_username = st.text_input("Username",        key="reg_username", placeholder="john_doe")
                reg_acc      = st.text_input("Account Number",  key="reg_acc",      placeholder="8+ digit number")
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                reg_pass    = st.text_input("Create Password",  key="reg_pass",    type="password", placeholder="Min 6 characters")
            with col_p2:
                reg_confirm = st.text_input("Confirm Password", key="reg_confirm", type="password", placeholder="Repeat password")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("✅ Complete Registration", use_container_width=True,
                         type="primary", key="register_btn"):

                # ── Field-by-field validation with specific error messages ──
                error = None
                if not reg_name.strip():
                    error = "❌ Full Name is required."
                elif not is_valid_name(reg_name):
                    error = "❌ Full Name must contain letters only."
                elif not reg_username.strip():
                    error = "❌ Username is required."
                elif not is_valid_username(reg_username):
                    error = "❌ Username must be 3+ characters (letters, numbers, underscore only)."
                elif not reg_email.strip():
                    error = "❌ Email is required."
                elif not is_valid_email(reg_email):
                    error = "❌ Invalid email format."
                elif not reg_phone.strip():
                    error = "❌ Phone number is required."
                elif not is_valid_phone(reg_phone):
                    error = "❌ Phone must be at least 10 digits (numbers only)."
                elif not reg_acc.strip():
                    error = "❌ Account number is required."
                elif not is_valid_account(reg_acc):
                    error = "❌ Account number must be at least 8 digits (numbers only)."
                elif not reg_pass:
                    error = "❌ Password is required."
                elif not is_valid_password(reg_pass):
                    error = "❌ Password must be at least 6 characters."
                elif reg_pass != reg_confirm:
                    error = "❌ Passwords do not match."

                if error:
                    st.error(error)
                else:
                    with st.spinner("Creating your account..."):
                        try:
                            res = requests.post(
                                f"{API_URL}/auth/register",
                                json={
                                    "full_name":  reg_name.strip(),
                                    "username":   reg_username.strip(),
                                    "email":      reg_email.strip(),
                                    "phone":      reg_phone.strip(),
                                    "account_no": reg_acc.strip(),
                                    "password":   reg_pass
                                },
                                timeout=10
                            )
                            result = res.json()
                            if result.get("success"):
                                st.success("✅ Account created successfully! Redirecting to login...")
                                time.sleep(1.5)
                                st.session_state.auth_view = "login"
                                st.rerun()
                            else:
                                st.error(result.get("message", "❌ Registration failed. Try a different username or email."))
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Backend server is offline. Please restart the app.")
                        except Exception as e:
                            st.error(f"❌ Unexpected error: {e}")

            if st.button("← Back to Login", use_container_width=True,
                         key="back_to_login_btn"):
                st.session_state.auth_view = "login"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)