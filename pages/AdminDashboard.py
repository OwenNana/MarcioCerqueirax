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

# ===== إعدادات الشيت الرئيسي =====
ADMIN_SHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"
spreadsheet = client.open_by_key(ADMIN_SHEET_ID)
admin_sheet = spreadsheet.worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())

st.set_page_config(page_title="لوحة الأدمن", page_icon="🛠️")
st.title("🛠️ لوحة إدارة المستخدمين")

# ===== تحقق من صلاحيات الأدمن =====
if st.session_state.get("permissions") != "admin":
    st.error("🚫 هذه الصفحة مخصصة للأدمن فقط")
    st.stop()

# ===== عرض المستخدمين =====
st.subheader("📋 قائمة المستخدمين")
data = admin_sheet.get_all_records()
df = pd.DataFrame(data)
st.dataframe(df)

# ===== الأعمدة الافتراضية لكل مستخدم جديد =====
def get_default_columns():
    return [
        "التاريخ",
        "ورد النووي",
        "مختصر الإشراق",
        "الضحى",
        "التهليل",
        "استغفار",
        "صلاة على الحبيب",
        "السنن الرواتب",
        "تلاوة قرآن (لا يقل عن ثمن)",
        "حضور درس",
        "قراءة كتاب",
        "الوتر",
        "دعاء",
        "صلاة الفجر",
        "صلاة الظهر",
        "صلاة العصر",
        "صلاة المغرب",
        "صلاة العشاء"
    ]

# ===== إنشاء مستخدم جديد =====
st.subheader("➕ إنشاء حساب جديد")
with st.form("create_user_form"):
    username = st.text_input("Username")
    password = st.text_input("Password")
    role = st.selectbox("Role", ["user", "supervisor"])
    create = st.form_submit_button("Create")

    if create:
        if not username or not password:
            st.warning("Please enter a username and password")
        elif username in users_df["username"].values:
            st.error("🚫 Username already exists")
        else:
            worksheet_name = f"بيانات - {username}"
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="1000", cols="30")
            columns = get_default_columns()
            worksheet.insert_row(columns, 1)
            admin_sheet.append_row([username, password, worksheet_name, role])
            st.success("✅ User and worksheet created successfully")
            st.rerun()
