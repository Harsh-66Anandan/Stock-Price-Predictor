import streamlit as st
import base64
import io
import requests
from PIL import Image
from streamlit_cropper import st_cropper

API_URL = "http://localhost:8000"

@st.dialog("Upload & Crop Avatar")
def avatar_upload_dialog():
    st.write("Select a photo to use as your profile picture.")
    uploaded_image = st.file_uploader("Choose a photo", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if uploaded_image is not None:
        img = Image.open(uploaded_image)
        cropped_img = st_cropper(img, aspect_ratio=(1, 1), box_color='#00C9FF', return_type='image')
        
        if st.button("💾 Save Profile Picture", type="primary", use_container_width=True):
            buffered = io.BytesIO()
            cropped_img.save(buffered, format="PNG")
            img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Save to Database
            st.session_state.profile_image = img_data
            requests.put(f"{API_URL}/users/{st.session_state.current_username}", json={
                "display_name": st.session_state.display_name,
                "currency": st.session_state.get('currency', "USD ($)"),
                "two_fa_enabled": True,
                "biometric_login": False,
                "profile_image": img_data
            })
            
            st.toast("✅ Avatar updated successfully in database!")
            st.rerun()

def render():
    username = st.session_state.current_username
    
    # 1. Fetch Latest Data from Backend
    try:
        res = requests.get(f"{API_URL}/users/{username}")
        if res.status_code == 200:
            db_user = res.json()
            st.session_state.display_name = db_user["display_name"]
            st.session_state.profile_image = db_user["profile_image"]
            email_val = db_user["email"]
            currency_val = db_user["currency"]
            two_fa_val = db_user["two_fa_enabled"]
            bio_val = db_user["biometric_login"]
        else:
            st.error("Failed to load user profile from database.")
            return
    except requests.exceptions.ConnectionError:
        st.error("Backend Server is offline.")
        return

    display_text = st.session_state.display_name if st.session_state.display_name else username
    
    # Header Section
    col_avatar, col_info = st.columns([1, 5])
    with col_avatar:
        if st.session_state.profile_image:
            st.markdown(f'<div style="width: 100px; height: 100px; border-radius: 50%; background-image: url(\'data:image/png;base64,{st.session_state.profile_image}\'); background-size: cover; background-position: center; box-shadow: 0 0 20px rgba(0,201,255,0.4); margin-bottom: 20px;"></div>', unsafe_allow_html=True)
        else:
            initial = display_text[0].upper()
            st.markdown(f'<div style="width: 100px; height: 100px; border-radius: 50%; background: linear-gradient(135deg, #00C9FF, #92FE9D); display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 40px; color: #0a151c; box-shadow: 0 0 20px rgba(0,201,255,0.4); margin-bottom: 20px;">{initial}</div>', unsafe_allow_html=True)
        
    with col_info:
        st.markdown(f'<h1 class="gradient-text" style="margin-bottom:0;">{display_text}</h1>', unsafe_allow_html=True)
        st.markdown(f"<p style='color:#8fc1d4; font-size:14px; letter-spacing:1px;'>@{username} | ENTERPRISE EDITION</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Profile Form
    st.markdown("<p class='section-title'>PROFILE INFORMATION</p>", unsafe_allow_html=True)
    prof_c1, prof_c2 = st.columns(2)
    with prof_c1:
        new_name = st.text_input("Display Name", value=st.session_state.display_name)
        st.text_input("Account Type", value="Institutional / Enterprise", disabled=True)
    with prof_c2:
        st.text_input("Email Address", value=email_val, disabled=True) # Email shouldn't be edited here
        new_currency = st.selectbox("Default Currency", ["USD ($)", "EUR (€)", "GBP (£)"], index=["USD ($)", "EUR (€)", "GBP (£)"].index(currency_val))
    
    st.markdown("<br><p class='section-title'>AVATAR SETTINGS</p>", unsafe_allow_html=True)
    if st.button("📸 Change Avatar Profile Picture"):
        avatar_upload_dialog()

    st.markdown("<br><p class='section-title'>SECURITY</p>", unsafe_allow_html=True)
    new_2fa = st.checkbox("Enable Two-Factor Authentication (2FA)", value=two_fa_val)
    new_bio = st.checkbox("Biometric Login on Mobile", value=bio_val)
    
    # Update Database Call
    if st.button("💾 Update Identity Data", type="primary"):
        payload = {
            "display_name": new_name,
            "currency": new_currency,
            "two_fa_enabled": new_2fa,
            "biometric_login": new_bio,
            "profile_image": st.session_state.profile_image
        }
        res = requests.put(f"{API_URL}/users/{username}", json=payload)
        
        if res.status_code == 200:
            st.session_state.display_name = new_name
            st.session_state.currency = new_currency
            st.toast("✅ Profile synchronized with database successfully!")
            st.rerun()
        else:
            st.error("❌ Failed to update database.")