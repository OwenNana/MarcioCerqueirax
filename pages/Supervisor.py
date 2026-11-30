import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.graph_objects as go

# ===== التحقق من تسجيل الدخول وإعادة التوجيه =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔐 يجب تسجيل الدخول أولاً")
    st.switch_page("home.py")

if st.session_state.get("permissions") != "supervisor":
    permission = st.session_state.get("permissions")
    if permission == "admin":
        st.switch_page("pages/AdminDashboard.py")
    elif permission == "user":
        st.switch_page("pages/UserDashboard.py")
    else:
        st.switch_page("home.py")

# ===== إعداد الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد الصفحة =====
st.set_page_config(page_title="📊 تقارير المشرف", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: 'Arial', sans-serif;
        background-color: white !important;
        color: black !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 18px;
        padding: 10px;
    }
    .stDataFrame div[role='table'] {
        overflow-x: auto;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 تقارير المشرف")
if st.button("🔄 جلب المعلومات من قاعدة البيانات"):
    st.rerun()

# ===== تحقق من صلاحية الدخول =====
if "permissions" not in st.session_state or st.session_state["permissions"] != "supervisor":
    st.error("🚫 هذه الصفحة مخصصة للمشرف فقط.")
    st.stop()

# ===== تحديد الفترة الزمنية =====
st.sidebar.header("📅 تحديد الفترة")
start_date = st.sidebar.date_input("من تاريخ", datetime.today())
end_date = st.sidebar.date_input("إلى تاريخ", datetime.today())

if start_date > end_date:
    st.error("⚠️ تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
    st.stop()

# ===== قراءة ورقة admin وتجاهل أول 5 صفوف =====
admin_sheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY").worksheet("admin")
admin_data = admin_sheet.get_all_records()
users = admin_data[5:]  # الصفوف من السادس فما فوق

# ===== تبويبات التقارير =====
tabs = st.tabs(["📋 تجميعي الكل", "📌 تجميعي بند", "👤 تقرير فردي", "📈 رسوم بيانية"])

# ====== تجميع البيانات من جميع أوراق المستخدمين ======
all_data = []
for user in users:
    username = user.get("username")
    sheet_name = user.get("sheet_name")
    try:
        user_ws = admin_sheet.spreadsheet.worksheet(sheet_name)
        user_records = user_ws.get_all_records()
        df = pd.DataFrame(user_records)
        
        # تحقق من تواريخ البيانات
        if "التاريخ" in df.columns:
            df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
            df = df[(df["التاريخ"] >= pd.to_datetime(start_date)) & (df["التاريخ"] <= pd.to_datetime(end_date))]
            df.insert(0, "username", username)
            all_data.append(df)
    except Exception as e:
        st.warning(f"⚠️ حدث خطأ أثناء قراءة بيانات {username}: {e}")

if not all_data:
    st.info("ℹ️ لا توجد بيانات في الفترة المحددة.")
    st.stop()

merged_df = pd.concat(all_data, ignore_index=True)

# ========== تبويب 1: التقرير التجميعي ==========
with tabs[0]:
    st.subheader("📋 مجموع الدرجات لكل مستخدم")

    # إيجاد الأشخاص الذين لديهم حقول فارغة ضمن الفترة الزمنية
    missing_data = []
    for user in merged_df['username'].unique():
        user_data = merged_df[merged_df['username'] == user]
        empty_fields = user_data.isnull().sum(axis=1)
        if empty_fields.any():
            missing_fields = user_data.columns[empty_fields > 0]
            missing_data.append((user, missing_fields.tolist()))

    # عرض الأشخاص الذين لم يعبئوا البيانات باللون الأحمر
    if missing_data:
        st.markdown("### الأشخاص الذين لم يعبئوا البيانات:")
        for user, fields in missing_data:
            st.markdown(f"<span style='color:red;'><strong>{user}</strong></span> (الحقول الفارغة: {', '.join(fields)})", unsafe_allow_html=True)

    # عرض البيانات الأخرى
    scores = merged_df.drop(columns=["التاريخ", "username"], errors="ignore")
    grouped = merged_df.groupby("username")[scores.columns].sum()
    grouped["المجموع"] = grouped.sum(axis=1)
    cols = grouped.columns.tolist()
    if "المجموع" in cols:
        cols.insert(0, cols.pop(cols.index("المجموع")))
        grouped = grouped[cols]
    grouped = grouped.sort_values(by="المجموع", ascending=True)
    st.dataframe(grouped, use_container_width=True)

# ========== تبويب 2: تقرير بند معين ==========
with tabs[1]:
    st.subheader("📌 مجموع بند معين لكل المستخدمين")
    all_columns = [col for col in merged_df.columns if col not in ["التاريخ", "username"]]
    selected_activity = st.selectbox("اختر البند", all_columns)
    activity_sum = merged_df.groupby("username")[selected_activity].sum().sort_values(ascending=True)

    st.dataframe(activity_sum, use_container_width=True)

# ========== تبويب 3: تقرير فردي ==========
with tabs[2]:
    st.subheader("👤 تقرير تفصيلي لمستخدم")
    selected_user = st.selectbox("اختر المستخدم", merged_df["username"].unique())
    user_df = merged_df[merged_df["username"] == selected_user].sort_values("التاريخ")
    st.dataframe(user_df.reset_index(drop=True), use_container_width=True)

# ========== تبويب 4: رسوم بيانية ==========
with tabs[3]:
    st.subheader("📈 رسوم بيانية")
    pie_fig = go.Figure(go.Pie(
        labels=grouped.index,
        values=grouped["المجموع"],
        hole=0.4,
        title="مجموع الدرجات الكلية"
    ))
    st.plotly_chart(pie_fig, use_container_width=True)
