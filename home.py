import streamlit as st
import requests

API_URL = "http://localhost:5000"  # عدّل لاحقًا إلى رابط نشر الـ API

st.set_page_config(page_title="تسجيل الدخول", page_icon="🔐")

st.title("🔐 تسجيل الدخول")

with st.form("login_form"):
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")
    submitted = st.form_submit_button("دخول")

    if submitted:
        if not username or not password:
            st.warning("الرجاء إدخال بيانات الدخول.")
        else:
            with st.spinner("جاري التحقق..."):
                try:
                    response = requests.post(f"{API_URL}/login", json={
                        "username": username,
                        "password": password
                    })

                    result = response.json()

                    if result["status"] == "success":
                        st.success("✅ تم تسجيل الدخول بنجاح")
                        st.session_state["username"] = username
                        st.session_state["sheet_url"] = result["sheetUrl"]
                        st.session_state["permissions"] = result["permissions"]

                        # إعادة توجيه حسب الصلاحيات
                        if result["permissions"] == "admin":
                            st.switch_page("pages/AdminDashboard.py")
                        else:
                            st.switch_page("pages/UserDashboard.py")
                    else:
                        st.error("❌ " + result["message"])
                except Exception as e:
                    st.error(f"⚠️ حدث خطأ: {str(e)}")
