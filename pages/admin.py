import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ===== إعداد صفحة Streamlit =====
st.set_page_config(layout="wide", page_title="📊 جلب المعلومات")

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

# ===== تنسيقات إضافية =====
st.markdown("""
<style>
div[data-testid="stCheckbox"] > label {
    display: flex;
    justify-content: center;
    font-size: 20px !important;
    color: #ff0000 !important;
    font-weight: bold;
    margin: 10px auto;
}
html, body, .main { background-color: #ffffff !important; }
.zoom-container {
    display: flex !important;
    justify-content: center !important;
    gap: 15px !important;
    margin-top: 20px !important;
}
.selected-card {
    padding: 25px;
    border-radius: 18px;
    border: 3px solid #28a745 !important;
    box-shadow: 0 0 15px rgba(40,167,69,0.5);
    margin-top: 10px;
    transition: 0.3s ease;
}
</style>
""", unsafe_allow_html=True)

# ===== تحميل البيانات من Google Sheets =====
@st.cache_data
def load_data():
    SCOPE = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    SHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"  # الشيت الرئيسي الحالي
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
