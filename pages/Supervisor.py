import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.graph_objects as go

# ===== إعداد الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد الصفحة =====
st.set_page_config(page_title="📊 تقارير المشرف", page_icon="📊", layout="wide")
st.title("📊 تقارير المشرف")

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
    scores = merged_df.drop(columns=["التاريخ", "username"], errors="ignore")
    grouped = merged_df.groupby("username")[scores.columns].sum()
    grouped["المجموع"] = grouped.sum(axis=1)
    # نقل عمود "المجموع" ليكون في البداية
    cols = grouped.columns.tolist()
    if "المجموع" in cols:
        cols.insert(0, cols.pop(cols.index("المجموع")))
        grouped = grouped[cols]
    st.dataframe(grouped)

# ========== تبويب 2: تقرير بند معين ==========
with tabs[1]:
    st.subheader("📌 مجموع بند معين لكل المستخدمين")
    all_columns = [col for col in merged_df.columns if col not in ["التاريخ", "username"]]
    selected_activity = st.selectbox("اختر البند", all_columns)
    activity_sum = merged_df.groupby("username")[selected_activity].sum()
    st.dataframe(activity_sum)

# ========== تبويب 3: تقرير فردي ==========
with tabs[2]:
    st.subheader("👤 تقرير تفصيلي لمستخدم")
    selected_user = st.selectbox("اختر المستخدم", merged_df["username"].unique())
    user_df = merged_df[merged_df["username"] == selected_user].sort_values("التاريخ")
    st.dataframe(user_df.reset_index(drop=True))

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
