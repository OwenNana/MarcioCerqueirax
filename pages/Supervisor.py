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

# ===== إعداد الصفحة =====
st.set_page_config(page_title="التقارير", page_icon="📊")
st.title("📊 تقارير المستخدمين")

# ===== تحقق من صلاحية المشرف =====
if "permissions" not in st.session_state or st.session_state["permissions"] != "supervisor":
    st.error("🚫 هذه الصفحة مخصصة للمشرف فقط.")
    st.stop()

# ===== عرض تقارير المستخدمين =====
st.subheader("📋 قائمة التقارير")
admin_sheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY").worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())

# جلب أسماء أو روابط الشيتات من العامود الثالث
user_sheets = users_df["sheet_name"].values  # هنا نتعامل مع العامود الثالث الذي يحتوي على روابط الشيتات

# عرض تقارير جميع المستخدمين
for sheet_url in user_sheets:
    try:
        # فتح الشيت باستخدام الرابط المخزن في العامود الثالث
        user_sheet = client.open_by_url(sheet_url)  # فتح الشيت باستخدام الرابط الفعلي
        user_data = pd.DataFrame(user_sheet.get_all_records())
        sheet_name = user_sheet.title  # الحصول على اسم الشيت
        st.subheader(f"التقرير: {sheet_name}")
        st.dataframe(user_data)
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"❌ الورقة {sheet_url} غير موجودة.")
