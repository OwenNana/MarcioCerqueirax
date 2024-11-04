import streamlit as st
import requests

API_URL = "http://localhost:5000"  # غيّر هذا لاحقًا إلى رابط API الحقيقي

# التحقق من صلاحية الأدمن
if st.session_state.get("permissions") != "admin":
    st.error("🚫 الوصول مرفوض. هذه الصفحة مخصصة للمشرفين فقط.")
    st.stop()

st.set_page_config(page_title="لوحة الأدمن", page_icon="🛠️")
st.title("🛠️ لوحة إدارة الأدمن")

# جلب المستخدمين
def load_users():
    try:
        res = requests.get(f"{API_URL}/users")
        return res.json()
    except Exception as e:
        st.error(f"خطأ أثناء جلب المستخدمين: {e}")
        return []

with st.spinner("جاري تحميل المستخدمين..."):
    users = load_users()

# عرض المستخدمين في جدول
st.subheader("📋 قائمة المستخدمين")
if users:
    st.table([
        {
            "اسم المستخدم": user["username"],
            "كلمة المرور": user["password"],
            "الرابط": user["sheetUrl"],
            "الصلاحيات": user["permissions"]
        } for user in users
    ])
else:
    st.info("لا يوجد مستخدمين مسجلين.")

# إنشاء مستخدم جديد
st.subheader("➕ إنشاء حساب جديد")

with st.form("create_user_form"):
    new_username = st.text_input("اسم المستخدم (الإيميل)")
    new_password = st.text_input("كلمة المرور")
    create_btn = st.form_submit_button("إنشاء")

    if create_btn:
        if not new_username or not new_password:
            st.warning("يرجى إدخال اسم المستخدم وكلمة المرور.")
        else:
            with st.spinner("جاري إنشاء الحساب..."):
                try:
                    res = requests.post(f"{API_URL}/create-user", json={
                        "username": new_username,
                        "password": new_password
                    })
                    result = res.json()
                    if result["status"] == "success":
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
                except Exception as e:
                    st.error(f"حدث خطأ: {e}")
