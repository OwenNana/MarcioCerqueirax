import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:5000"  # عدّل للرابط النهائي لـ API

# التحقق من أن المستخدم مسجّل دخول
if "sheet_url" not in st.session_state:
    st.error("⚠️ يجب تسجيل الدخول أولاً.")
    st.stop()

st.set_page_config(page_title="تقييم الأنشطة", page_icon="📊")
st.title("📊 تقييم الأنشطة اليومية")

sheet_url = st.session_state["sheet_url"]

# جلب الأنشطة (رؤوس الأعمدة من Google Sheet)
with st.spinner("جاري تحميل الأنشطة..."):
    try:
        response = requests.post(f"{API_URL}/get-headers", json={"sheetUrl": sheet_url})
        headers = response.json()
        if isinstance(headers, list) and len(headers) > 1:
            activities = headers[1:]  # تجاهل أول عمود (عادة التاريخ)
        else:
            st.error("⚠️ لم يتم العثور على أنشطة.")
            st.stop()
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        st.stop()

# النموذج
with st.form("rating_form"):
    date = st.date_input("📅 اختر التاريخ", datetime.today())
    activity = st.selectbox("🎯 اختر النشاط", activities)
    rating = st.slider("📈 قيّم من 1 إلى 10", min_value=1, max_value=10)
    submitted = st.form_submit_button("حفظ التقييم")

    if submitted:
        with st.spinner("جاري الحفظ..."):
            try:
                res = requests.post(f"{API_URL}/submit-rating", json={
                    "sheetUrl": sheet_url,
                    "date": date.strftime("%Y-%m-%d"),
                    "activity": activity,
                    "rating": rating
                })
                result = res.json()
                if result["status"] == "success":
                    st.success(result["message"])
                else:
                    st.error(result["message"])
            except Exception as e:
                st.error(f"حدث خطأ: {e}")
