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

ADMIN_SHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"
sheet = client.open_by_key(ADMIN_SHEET_ID).worksheet("admin")

st.set_page_config(page_title="لوحة الأدمن", page_icon="🛠️")
st.title("🛠️ لوحة إدارة المستخدمين")

# ===== تحقق من صلاحيات الأدمن =====
if st.session_state.get("permissions") != "admin":
    st.error("🚫 هذه الصفحة مخصصة للأدمن فقط")
    st.stop()

# ===== عرض المستخدمين =====
st.subheader("📋 قائمة المستخدمين")
data = sheet.get_all_records()
df = pd.DataFrame(data)
st.dataframe(df)

# ===== إنشاء مستخدم جديد =====
st.subheader("➕ إنشاء حساب جديد")
with st.form("create_user_form"):
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور")
    create = st.form_submit_button("إنشاء")

    if create:
        if username and password:
            new_sheet = client.create(f"بيانات - {username}")
            url = new_sheet.url  # بدون مشاركة الشيت
            sheet.append_row([username, password, url, "user"])
            st.success("✅ تم إنشاء الحساب بنجاح")
            st.rerun()
        else:
            st.warning("يرجى إدخال اسم المستخدم وكلمة المرور")
