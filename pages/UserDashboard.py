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

st.set_page_config(page_title="تقييم الأنشطة", page_icon="📊")
st.title("📊 تقييم الأنشطة")

# ===== تحقق من تسجيل الدخول =====
if "sheet_url" not in st.session_state:
    st.error("يجب تسجيل الدخول أولاً")
    st.stop()

sheet_url = st.session_state["sheet_url"]
sheet_id = sheet_url.split("/d/")[1].split("/")[0]
sheet = client.open_by_key(sheet_id).sheet1

headers = sheet.row_values(1)
if len(headers) < 2:
    st.warning("لا توجد أنشطة في الشيت")
    st.stop()

activities = headers[1:]  # بدون العمود الأول (التاريخ)

# ===== النموذج =====
with st.form("rating_form"):
    date = st.date_input("📅 التاريخ", datetime.today())
    activity = st.selectbox("🎯 اختر النشاط", activities)
    rating = st.slider("قيم من 1 إلى 10", 1, 10)
    submit = st.form_submit_button("💾 حفظ")

    if submit:
        values = sheet.col_values(1)
        date_str = date.strftime("%Y-%m-%d")

        # إيجاد الصف المناسب للتاريخ
        try:
            row = values.index(date_str) + 1
        except ValueError:
            row = len(values) + 1
            sheet.update_cell(row, 1, date_str)

        col_index = headers.index(activity) + 1
        sheet.update_cell(row, col_index, rating)
        st.success("✅ تم حفظ التقييم")
