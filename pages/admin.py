import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

# ===== إعداد صفحة Streamlit =====
st.set_page_config(layout="wide", page_title="📊 جلب المعلومات")
st.title("📊 معلومات المستخدمين")

# ===== تحميل البيانات من Google Sheets =====
@st.cache_data
def load_data():
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    SHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"
    sheet = client.open_by_key(SHEET_ID).worksheet("admin")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# ===== جلب البيانات دون عرضها =====
data = load_data()

# ===== زر التحديث فقط =====
if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_top"):
    st.cache_data.clear()
    data = load_data()
    st.success("✅ تم جلب البيانات بنجاح")
