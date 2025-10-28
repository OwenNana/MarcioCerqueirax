import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد صفحة تسجيل الدخول =====
st.set_page_config(page_title="تسجيل الدخول", page_icon="🔐")
st.title("🔐 تسجيل الدخول")

# تحقق من صلاحية المستخدم
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# التحقق من تسجيل الدخول
if not st.session_state["authenticated"]:
    with st.form("login_form"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول")

        if submitted:
            matched = users_df[
                (users_df["username"] == username) &
                (users_df["password"] == password)
            ]
            if not matched.empty:
                user_row = matched.iloc[0]
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["sheet_url"] = user_row["sheet_name"]
                st.session_state["permissions"] = user_row["role"]
                st.success("✅ تم تسجيل الدخول")
                # إعادة التوجيه بناءً على الصلاحية
                try:
                    if st.session_state["permissions"] == "supervisor":
                        st.switch_page("pages/SupervisorDashboard.py")
                    elif st.session_state["permissions"] == "admin":
                        st.switch_page("pages/AdminDashboard.py")
                    else:
                        st.switch_page("pages/UserDashboard.py")
                except Exception as e:
                    st.error(f"⚠️ حدث خطأ في التوجيه: {str(e)}")
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
