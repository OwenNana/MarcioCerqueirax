import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.graph_objects as go

# ===== التحقق من تسجيل الدخول =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔐 يجب تسجيل الدخول أولاً")
    st.switch_page("home.py")

permissions = st.session_state.get("permissions")
if permissions not in ["supervisor", "sp"]:
    if permissions == "admin":
        st.switch_page("pages/AdminDashboard.py")
    elif permissions == "user":
        st.switch_page("pages/UserDashboard.py")
    else:
        st.switch_page("home.py")

# ===== إعداد الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== تحميل بيانات المستخدمين من admin sheet =====
spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")
admin_sheet = spreadsheet.worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())

username = st.session_state.get("username")

# ===== تحديد الطلاب تحت إشراف هذا المشرف =====
if permissions == "supervisor":
    assigned_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"] == username)]["username"].tolist()
elif permissions == "sp":
    my_supervisors = users_df[(users_df["role"] == "supervisor") & (users_df["Mentor"] == username)]["username"].tolist()
    assigned_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"].isin(my_supervisors))]["username"].tolist()
else:
    assigned_users = []

assigned_users.sort()

# ===== واجهة الصفحة =====
st.set_page_config(page_title="📊 تقارير المشرف", page_icon="📊", layout="wide")
st.title("📊 تقارير المشرف")

# ===== دالة الدردشة =====
def show_chat_supervisor():
    st.markdown("### 💬 الدردشة مع الطلاب")
    if not assigned_users:
        st.info("⚠️ لا يوجد طلاب لعرض محادثاتهم.")
        return

    chat_sheet = spreadsheet.worksheet("chat")
    raw_data = chat_sheet.get_all_records()
    if not raw_data:
        chat_data = pd.DataFrame(columns=["timestamp", "from", "to", "message"])
    else:
        chat_data = pd.DataFrame(raw_data)

    if not {"from", "to", "message", "timestamp"}.issubset(chat_data.columns):
        st.warning("⚠️ لم يتم العثور على الأعمدة الصحيحة في ورقة الدردشة.")
        return

    selected_user = st.selectbox("اختر الطالب", assigned_users)
    messages = chat_data[((chat_data["from"] == username) & (chat_data["to"] == selected_user)) |
                         ((chat_data["from"] == selected_user) & (chat_data["to"] == username))]

    messages = messages.sort_values(by="timestamp")
    if messages.empty:
        st.info("💬 لا توجد رسائل بعد.")
    else:
        for _, msg in messages.iterrows():
            sender = "👨‍🏫 أنت" if msg["from"] == username else f"🙋‍♂️ {msg['from']}"
            st.markdown(f"**{sender}**: {msg['message']}")

    new_msg = st.text_input("✏️ اكتب رسالتك للطالب")
    if st.button("📨 إرسال الرسالة"):
        if new_msg.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            chat_sheet.append_row([timestamp, username, selected_user, new_msg])
            st.success("✅ تم إرسال الرسالة")
            st.rerun()
        else:
            st.warning("⚠️ لا يمكن إرسال رسالة فارغة.")

# ===== تبويبات المشرف =====
tabs = st.tabs(["💬 المحادثات", "👤 تقرير إجمالي", "📋 تجميعي الكل", "📌 تجميعي بند", "👤 تقرير فردي", "📈 رسوم بيانية"])

with tabs[0]:
    show_chat_supervisor()
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_chat"):
        st.cache_data.clear()
        st.rerun()
