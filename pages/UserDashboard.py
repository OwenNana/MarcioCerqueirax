import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ===== التحقق من تسجيل الدخول =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("home.py")

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")

# ===== إعداد الصفحة =====
st.set_page_config(page_title="تقييم اليوم", page_icon="📋", layout="wide")

if st.session_state["permissions"] != "user":
    role = st.session_state["permissions"]
    if role == "admin":
        st.switch_page("pages/AdminDashboard.py")
    elif role in ["supervisor", "sp"]:
        st.switch_page("pages/Supervisor.py")
    else:
        st.error("⚠️ صلاحية غير معروفة.")
        st.stop()

username = st.session_state["username"]
sheet_name = f"بيانات - {username}"
worksheet = spreadsheet.worksheet(sheet_name)
columns = worksheet.row_values(1)

admin_sheet = spreadsheet.worksheet("admin")
admin_data = pd.DataFrame(admin_sheet.get_all_records())
mentor_name = admin_data.loc[admin_data["username"] == username, "Mentor"].values[0]
notification_setting = admin_data.loc[admin_data["username"] == username, "notifications"].values[0]

# ===== عرض إشعار الرسائل الجديدة =====
chat_sheet = spreadsheet.worksheet("chat")
chat_data = pd.DataFrame(chat_sheet.get_all_records())
if notification_setting == "on":
    unread_msgs = chat_data[(chat_data["to"] == username) & (chat_data["is_read"] == "no")]
    if not unread_msgs.empty:
        st.toast(f"📩 لديك {len(unread_msgs)} رسالة جديدة من المشرف!")

# ===== تبويبات الصفحة =====
tabs = st.tabs(["💬 الدردشات", "📝 تعبئة البيانات", "📈 التقارير"])

def refresh_button(key):
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key=key):
        st.cache_data.clear()
        st.rerun()
# ===== تبويب 1: الدردشات =====
with tabs[0]:
    st.subheader("💬 محادثتك مع المشرف أو السوبر مشرف")

    recipient = st.radio("اختر جهة التواصل:", [mentor_name, "sp"], horizontal=True)
    current_messages = chat_data[((chat_data["from"] == username) & (chat_data["to"] == recipient)) |
                                 ((chat_data["from"] == recipient) & (chat_data["to"] == username))]
    current_messages = current_messages.sort_values("timestamp")

    # عرض الرسائل
    for _, msg in current_messages.iterrows():
        sender = msg["from"]
        color = "#003366" if sender == username else "#8B0000"
        name = "🧑‍🎓 أنت" if sender == username else f"👨‍🏫 {sender}"
        st.markdown(f"<div style='background-color:{color}; color:white; padding:10px; border-radius:10px; margin-bottom:5px; font-size:14px'>{name}: {msg['message']}</div>", unsafe_allow_html=True)

    # تحديث حالة الرسائل إلى مقروءة
    for i, row in chat_data[(chat_data["to"] == username) & (chat_data["from"] == recipient) & (chat_data["is_read"] == "no")].iterrows():
        chat_sheet.update_cell(i + 2, 5, "yes")  # العمود الخامس = is_read

    # كتابة رسالة جديدة
    with st.form("send_message"):
        new_msg = st.text_area("✏️ اكتب رسالتك هنا:", height=100)
        send = st.form_submit_button("📨 إرسال")
        if send and new_msg.strip():
            timestamp = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
            chat_sheet.append_row([timestamp, username, recipient, new_msg, "no"])
            st.success("✅ تم إرسال الرسالة")
            st.rerun()

# ===== تبويب 2: تعبئة البيانات =====
with tabs[1]:
    st.subheader("📝 تقييم اليوم")
    refresh_button("refresh_tab_form")
    data_df = pd.DataFrame(worksheet.get_all_records())
    today_str = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d")
    today_row = data_df[data_df["التاريخ"] == today_str]

    if today_row.empty:
        st.info("📌 لا توجد بيانات لهذا اليوم، يمكنك البدء بالتعبئة.")
        input_data = {}
        with st.form("daily_form"):
            for col in columns[1:]:
                input_data[col] = st.slider(col, 0, 5, 0)
            submitted = st.form_submit_button("حفظ")
            if submitted:
                row_values = [today_str] + [input_data[col] for col in columns[1:]]
                worksheet.append_row(row_values)
                st.success("✅ تم حفظ البيانات بنجاح.")
    else:
        st.success("✅ تم تعبئة بيانات هذا اليوم بالفعل.")

# ===== تبويب 3: التقارير =====
with tabs[2]:
    st.subheader("📈 تقرير الأداء")
    refresh_button("refresh_tab_report")
    if not data_df.empty:
        scores = data_df.drop(columns=["التاريخ"])
        summary = scores.sum().sort_values(ascending=False)
        st.bar_chart(summary)
    else:
        st.info("ℹ️ لا توجد بيانات بعد لعرض التقرير.")
