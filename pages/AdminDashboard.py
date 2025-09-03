import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد الصفحة =====
st.set_page_config(page_title="لوحة الإدارة", page_icon="🛠️")
st.title("🛠️ لوحة إدارة المستخدمين")

# ===== تحقق من صلاحية الأدمن =====
if "permissions" not in st.session_state or st.session_state["permissions"] != "admin":
    st.error("🚫 هذه الصفحة مخصصة للأدمن فقط.")
    st.stop()

# ===== عرض المستخدمين =====
st.subheader("📋 قائمة المستخدمين")
admin_sheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY").worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())
st.dataframe(users_df)

# ===== إضافة مستخدم جديد =====
st.subheader("➕ إنشاء حساب جديد")
with st.form("create_user_form"):
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور")
    role = st.selectbox("الصلاحية", ["user", "supervisor"])
    create = st.form_submit_button("إنشاء")

    if create:
        if username in users_df["username"].values:
            st.error("🚫 اسم المستخدم موجود مسبقًا.")
        else:
            worksheet_name = f"بيانات - {username}"
            worksheet = client.create(worksheet_name).sheet1
            columns = [
                "التاريخ", "ورد النووي", "مختصر الإشراق", "الضحى", "التهليل", 
                "استغفار", "صلاة على الحبيب", "السنن الرواتب", "تلاوة قرآن", 
                "حضور درس", "قراءة كتاب", "الوتر", "دعاء", "صلاة الفجر", 
                "صلاة الظهر", "صلاة العصر", "صلاة المغرب", "صلاة العشاء"
            ]
            worksheet.insert_row(columns, 1)
            admin_sheet.append_row([username, password, worksheet_name, role])
            st.success("✅ تم إنشاء الحساب بنجاح")
            st.rerun()
