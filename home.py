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

# ===== إعداد صفحة تسجيل الدخول =====
st.set_page_config(page_title="تسجيل الدخول", page_icon="🔐")
st.title("🔐 تسجيل الدخول")

# ===== زر التحديث اليدوي =====
if st.button("🔄 جلب المعلومات من قاعدة البيانات"):
    st.cache_data.clear()
    st.success("✅ تم تحديث البيانات")

# إضافة حقول وهمية مخفية لمنع تعبئة iCloud Keychain على iOS
st.markdown(
    """
    <input type="text" name="fake_username" style="opacity:0; position:absolute; top:-1000px;">
    <input type="password" name="fake_password" style="opacity:0; position:absolute; top:-1000px;">
    """,
    unsafe_allow_html=True
)

# تحقق من صلاحية المستخدم
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# التحقق من تسجيل الدخول
if not st.session_state["authenticated"]:
    with st.form("login_form"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول")

        if submitted:
            # جلب البيانات من شيت الأدمن
            admin_sheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY").worksheet("admin")
            users_df = pd.DataFrame(admin_sheet.get_all_records())
            
            # التحقق من وجود المستخدم وكلمة المرور
            matched = users_df[
                (users_df["username"] == username) &
                (users_df["password"] == password)
            ]
            if not matched.empty:
                user_row = matched.iloc[0]
                full_name = user_row["full_name"]  # جلب الاسم الكامل
                st.session_state["authenticated"] = True
                st.session_state["username"] = username  # الاحتفاظ بـ username لتسجيل الدخول
                st.session_state["full_name"] = full_name  # تخزين الاسم الكامل في الجلسة
                st.session_state["sheet_url"] = user_row["sheet_name"]
                st.session_state["permissions"] = user_row["role"]
                st.success("✅ تم تسجيل الدخول")

                # إعادة التوجيه بناءً على الصلاحية
                if st.session_state["permissions"] in ["supervisor", "sp"]:
                    st.switch_page("pages/Supervisor.py")
                elif st.session_state["permissions"] == "admin":
                    st.switch_page("pages/AdminDashboard.py")
                elif st.session_state["permissions"] == "user":
                    st.switch_page("pages/UserDashboard.py")
                else:
                    st.error("⚠️ صلاحية غير معروفة.")
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
else:
    # إعادة التوجيه حسب الصلاحية
    permission = st.session_state.get("permissions")
    if permission in ["supervisor", "sp"]:
        st.switch_page("pages/Supervisor.py")
    elif permission == "admin":
        st.switch_page("pages/AdminDashboard.py")
    elif permission == "user":
        st.switch_page("pages/UserDashboard.py")
    else:
        st.error("⚠️ صلاحية غير معروفة.")
