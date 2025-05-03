import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ===== إعداد صفحة Streamlit =====
st.set_page_config(layout="wide", page_title="📊 جلب المعلومات")
st.title("📊 معلومات المستخدمين")

# ===== شعار قابل للنقر =====
st.markdown("""
<style>
@media (max-width: 768px) {
    .responsive-logo {
        height: 100px !important;
    }
}
@media (min-width: 769px) {
    .responsive-logo {
        height: 200px !important;
    }
}
</style>
<div style="text-align: center; margin-top: 20px;">
    <a href="https://self-discipline.streamlit.app/" target="_blank">
        <img class="responsive-logo" src="https://drive.google.com/thumbnail?id=1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY" alt="الصفحة الرئيسية">
    </a>
</div>
""", unsafe_allow_html=True)

# ===== تحميل البيانات من Google Sheets =====
@st.cache_data
def load_data():
    SCOPE = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    SHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"
    sheet = client.open_by_key(SHEET_ID).worksheet("admin")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# ===== عرض البيانات =====
data = load_data()
st.dataframe(data)

if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_top"):
    st.cache_data.clear()
    data = load_data()
    st.rerun()
