import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials

# ===== إعداد الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعدادات الشيت الرئيسي =====
ADMIN_SHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"
admin_sheet = client.open_by_key(ADMIN_SHEET_ID).worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())

# ===== صفحة تسجيل الدخول =====
st.set_page_config(page_title="تسجيل الدخول", page_icon="🔐")

# ✅ أيقونة + عنوان
st.markdown("""
<div style='text-align: center;'>
    <h1 style='font-size: 70px;'>🗂️</h1>
    <h2>تسجيل الدخول</h2>
    <p style='color: gray;'>جلب المعلومات من قاعدة البيانات</p>
</div>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    with st.form("login_form"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة السر", type="password")
        submitted = st.form_submit_button("دخول")

        if submitted:
            matched = users_df[
                (users_df["اسم المستخدم"] == username) &
                (users_df["كلمة السر"] == password)
            ]
            if not matched.empty:
                user_row = matched.iloc[0]
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["sheet_url"] = user_row["رابط الشيت"]
                st.session_state["permissions"] = user_row["الصلاحيات"]
                st.success("✅ تم تسجيل الدخول")
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة السر غير صحيحة")

# ===== إعادة التوجيه =====
if st.session_state.get("authenticated"):
    if st.session_state.get("permissions") == "admin":
        st.switch_page("pages/AdminDashboard.py")
    else:
        st.switch_page("pages/UserDashboard.py")
