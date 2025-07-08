import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد الصفحة =====
st.set_page_config(page_title="تقييم اليوم", page_icon="📋")
st.markdown("""
    <style>
        html, body, [data-testid="stApp"] {
            background-color: white !important;
            color: black !important;
        }
        .block-container {
            background-color: white !important;
        }
        .activity-label {
            color: #800000;
            font-weight: bold;
            font-size: 18px;
            text-align: center;
            margin-bottom: 4px;
        }
        .select-wrapper {
            display: flex;
            justify-content: center;
            margin-bottom: 16px;
        }
        .stSelectbox > div[data-baseweb="select"] {
            background-color: white !important;
            color: black !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📋 تقييم الأنشطة اليومية")

# ===== تحقق من صلاحية المستخدم =====
if "username" not in st.session_state or "sheet_url" not in st.session_state:
    st.error("❌ يجب تسجيل الدخول أولاً.")
    st.stop()

if st.session_state["permissions"] != "user":
    if st.session_state["permissions"] == "admin":
        st.warning("👤 تم تسجيل الدخول كأدمن، سيتم تحويلك للوحة التحكم...")
        st.switch_page("pages/AdminDashboard.py")
    elif st.session_state["permissions"] == "supervisor":
        st.warning("👤 تم تسجيل الدخول كمشرف، سيتم تحويلك للتقارير...")
        st.switch_page("pages/SupervisorDashboard.py")
    else:
        st.error("⚠️ الصلاحية غير معروفة.")
    st.stop()

username = st.session_state["username"]
sheet_name = f"بيانات - {username}"
spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")
worksheet = spreadsheet.worksheet(sheet_name)

# ===== جلب الأعمدة من الصف الأول =====
columns = worksheet.row_values(1)

# ===== النموذج =====
with st.form("daily_form"):
    date = st.date_input("📅 التاريخ", datetime.today())
    values = [date.strftime("%Y-%m-%d")]

    for col in columns[1:]:  # تخطي "التاريخ"
        st.markdown(f"<div class='activity-label'>{col}</div>", unsafe_allow_html=True)
        with st.container():
            value = st.selectbox("", [""] + [str(n) for n in range(1, 11)], key=col, label_visibility="collapsed")
            values.append(value)

    submit = st.form_submit_button("💾 حفظ")

    if submit:
        all_dates = worksheet.col_values(1)
        date_str = date.strftime("%Y-%m-%d")

        try:
            row_index = all_dates.index(date_str) + 1
        except ValueError:
            row_index = len(all_dates) + 1
            worksheet.update_cell(row_index, 1, date_str)

        for i, val in enumerate(values[1:], start=2):
            worksheet.update_cell(row_index, i, val)

        st.success("✅ تم حفظ البيانات بنجاح")
