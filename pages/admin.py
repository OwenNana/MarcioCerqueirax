import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials

# ===== التحقق من تسجيل الدخول =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔐 يجب تسجيل الدخول أولاً")
    st.switch_page("home.py")

# ===== إعداد صفحة Streamlit =====
st.set_page_config(layout="wide", page_title="⚙️ إعدادات المستخدم")

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)
SHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"
admin_ws = client.open_by_key(SHEET_ID).worksheet("admin")

# ===== تحميل بيانات المستخدمين =====
data = admin_ws.get_all_records()
df = pd.DataFrame(data)

username = st.session_state.get("username")
user_row = df[df["username"] == username]

if user_row.empty:
    st.error("⚠️ لم يتم العثور على المستخدم.")
    st.stop()

# ===== عرض العنوان =====
st.title(f"👋 أهلاً {username}")

row_index = user_row.index[0] + 2  # +2 لأن get_all_records يبدأ من الصف 2

# ===== تغيير كلمة المرور =====
st.subheader("🔒 تغيير كلمة المرور")
with st.form("change_password_form"):
    current_pass = st.text_input("كلمة المرور الحالية", type="default")
    new_pass = st.text_input("كلمة المرور الجديدة", type="default")
    confirm_pass = st.text_input("تأكيد كلمة المرور الجديدة", type="default")
    submit_pass = st.form_submit_button("تحديث كلمة المرور")

    if submit_pass:
        actual_pass = user_row.iloc[0]["password"]
        if current_pass != actual_pass:
            st.error("❌ كلمة المرور الحالية غير صحيحة.")
        elif new_pass != confirm_pass:
            st.error("❌ كلمة المرور الجديدة وتأكيدها غير متطابقتين.")
        elif new_pass == "":
            st.error("❌ لا يمكن أن تكون كلمة المرور فارغة.")
        else:
            admin_ws.update_cell(row_index, 2, new_pass)
            st.success("✅ تم تحديث كلمة المرور بنجاح.")
