import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.graph_objects as go

# ===== التحقق من تسجيل الدخول =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("home.py")

permissions = st.session_state.get("permissions")
if permissions not in ["supervisor", "sp"]:
    if permissions == "admin":
        st.switch_page("pages/AdminDashboard.py")
    elif permissions == "user":
        st.switch_page("pages/UserDashboard.py")
    else:
        st.switch_page("home.py")

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")

# ===== تحميل بيانات المستخدمين =====
admin_sheet = spreadsheet.worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())
username = st.session_state.get("username")

# ===== قراءة ورقة المحادثات والتحقق من وجود رسائل جديدة =====
chat_sheet = spreadsheet.worksheet("chat")
chat_data = pd.DataFrame(chat_sheet.get_all_records())
unread_messages = chat_data[(chat_data["to"] == username) & (chat_data["is_read"] == "no")]
if not unread_messages.empty:
    st.toast(f"📩 لديك {len(unread_messages)} رسالة جديدة من الطلاب!")

# ===== إعداد الصفحة =====
st.set_page_config(page_title="📊 تقارير المشرف", page_icon="📊", layout="wide")
st.title(f"👋 أهلاً {username}")

# ===== تحديد المستخدمين المتاحين للمشرف =====
if permissions == "supervisor":
    assigned_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"] == username)]["username"].tolist()
elif permissions == "sp":
    my_supervisors = users_df[(users_df["role"] == "supervisor") & (users_df["Mentor"] == username)]["username"].tolist()
    assigned_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"].isin(my_supervisors))]["username"].tolist()
else:
    assigned_users = []

assigned_users.sort()

# ===== التبويبات =====
tabs = st.tabs(["💬 المحادثات", "👤 تقرير إجمالي", "📋 تجميعي الكل", "📌 تجميعي بند", "👤 تقرير فردي", "📈 رسوم بيانية"])
# ===== تبويب 1: المحادثات =====
with tabs[0]:
    st.subheader("💬 الدردشة مع الطلاب")
    if not assigned_users:
        st.info("⚠️ لا يوجد طلاب لعرض محادثاتهم.")
    else:
        selected_user = st.selectbox("اختر الطالب", assigned_users)
        messages = chat_data[((chat_data["from"] == username) & (chat_data["to"] == selected_user)) |
                             ((chat_data["from"] == selected_user) & (chat_data["to"] == username))]
        messages = messages.sort_values("timestamp")

        for _, msg in messages.iterrows():
            sender = msg["from"]
            color = "#8B0000" if sender == username else "#003366"
            name = "👨‍🏫 أنت" if sender == username else f"🙋‍♂️ {sender}"
            st.markdown(f"<div style='background-color:{color}; color:white; padding:10px; border-radius:10px; margin-bottom:5px; font-size:14px'>{name}: {msg['message']}</div>", unsafe_allow_html=True)

        # تحديث الرسائل إلى مقروءة
        for i, row in chat_data[(chat_data["to"] == username) & (chat_data["from"] == selected_user) & (chat_data["is_read"] == "no")].iterrows():
            chat_sheet.update_cell(i + 2, 5, "yes")

        # إرسال رسالة جديدة
        with st.form("send_message_form"):
            msg_text = st.text_area("✏️ اكتب رسالتك هنا:", height=100)
            send = st.form_submit_button("📨 إرسال")
            if send and msg_text.strip():
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                chat_sheet.append_row([timestamp, username, selected_user, msg_text, "no"])
                st.success("✅ تم إرسال الرسالة")
                st.rerun()

# ==== التبويبات الأخرى كما كانت سابقًا (التقارير...) ====
# بإمكاننا الإبقاء عليها كما هي بدون تغيير لأنها مستقرة.
