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

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")
admin_sheet = spreadsheet.worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())

username = st.session_state.get("username")

# ===== إعداد الصفحة =====
st.set_page_config(page_title="📊 تقارير المشرف", page_icon="📊", layout="wide")
st.title("📊 تقارير المشرف")

# ===== تحديد الطلاب =====
if permissions == "supervisor":
    assigned_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"] == username)]["username"].tolist()
elif permissions == "sp":
    my_supervisors = users_df[(users_df["role"] == "supervisor") & (users_df["Mentor"] == username)]["username"].tolist()
    assigned_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"].isin(my_supervisors))]["username"].tolist()
else:
    assigned_users = []

assigned_users.sort()

# ===== دالة عرض المحادثة =====
def show_chat_supervisor():
    st.markdown("### 💬 الدردشة مع الطلاب")
    if not assigned_users:
        st.info("⚠️ لا يوجد طلاب لعرض محادثاتهم.")
        return

    chat_sheet = spreadsheet.worksheet("chat")
    raw_data = chat_sheet.get_all_records()
    chat_data = pd.DataFrame(raw_data) if raw_data else pd.DataFrame(columns=["timestamp", "from", "to", "message"])

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
            if msg["from"] == username:
                st.markdown(f"<p style='color:#8B0000'><b>👨‍🏫 أنت:</b> {msg['message']}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color:#000080'><b>🙋‍♂️ {msg['from']}:</b> {msg['message']}</p>", unsafe_allow_html=True)

    new_msg = st.text_area("✏️ اكتب رسالتك للطالب", height=100)
    if st.button("📨 إرسال الرسالة"):
        if new_msg.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            chat_sheet.append_row([timestamp, username, selected_user, new_msg])
            st.success("✅ تم إرسال الرسالة")
            st.rerun()
        else:
            st.warning("⚠️ لا يمكن إرسال رسالة فارغة.")

# ===== التبويبات =====
tabs = st.tabs(["💬 المحادثات", "👤 تقرير إجمالي", "📋 تجميعي الكل", "📌 تجميعي بند", "👤 تقرير فردي", "📈 رسوم بيانية"])

with tabs[0]:
    show_chat_supervisor()
# ===== إعداد الفترة الزمنية لجميع التبويبات (ما عدا المحادثات) =====
default_start = datetime.today().replace(day=1)
default_end = datetime.today()

# ===== تبويب 2: تقرير إجمالي =====
with tabs[1]:
    st.subheader("👤 مجموع درجات كل مستخدم")
    start_date = st.date_input("من تاريخ", default_start, key="start_tab1")
    end_date = st.date_input("إلى تاريخ", default_end, key="end_tab1")
    if start_date > end_date:
        st.error("⚠️ تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
        st.stop()
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_tab1"):
        st.cache_data.clear()
        st.rerun()

# ===== تبويب 3: تجميعي الكل =====
with tabs[2]:
    st.subheader("📋 مجموع الدرجات لكل مستخدم")
    start_date = st.date_input("من تاريخ", default_start, key="start_tab2")
    end_date = st.date_input("إلى تاريخ", default_end, key="end_tab2")
    if start_date > end_date:
        st.error("⚠️ تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
        st.stop()
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_tab2"):
        st.cache_data.clear()
        st.rerun()
    st.dataframe(grouped, use_container_width=True)

# ===== تبويب 4: تجميعي بند =====
with tabs[3]:
    st.subheader("📌 مجموع بند معين لكل المستخدمين")
    start_date = st.date_input("من تاريخ", default_start, key="start_tab3")
    end_date = st.date_input("إلى تاريخ", default_end, key="end_tab3")
    if start_date > end_date:
        st.error("⚠️ تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
        st.stop()
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_tab3"):
        st.cache_data.clear()
        st.rerun()

    all_columns = [col for col in merged_df.columns if col not in ["التاريخ", "username"]]
    selected_activity = st.selectbox("اختر البند", all_columns)
    activity_sum = merged_df.groupby("username")[selected_activity].sum().sort_values(ascending=True)

    missing_users = set(all_usernames) - set(users_with_data)
    for user in missing_users:
        activity_sum[user] = 0

    st.dataframe(activity_sum, use_container_width=True)

# ===== تبويب 5: تقرير فردي =====
with tabs[4]:
    st.subheader("👤 تقرير تفصيلي لمستخدم")
    start_date = st.date_input("من تاريخ", default_start, key="start_tab4")
    end_date = st.date_input("إلى تاريخ", default_end, key="end_tab4")
    if start_date > end_date:
        st.error("⚠️ تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
        st.stop()
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_tab4"):
        st.cache_data.clear()
        st.rerun()

    selected_user = st.selectbox("اختر المستخدم", merged_df["username"].unique())
    user_df = merged_df[merged_df["username"] == selected_user]
    user_df = user_df[(user_df["التاريخ"] >= pd.to_datetime(start_date)) & (user_df["التاريخ"] <= pd.to_datetime(end_date))]
    user_df = user_df.sort_values("التاريخ")
    st.dataframe(user_df.reset_index(drop=True), use_container_width=True)

# ===== تبويب 6: رسوم بيانية =====
with tabs[5]:
    st.subheader("📈 رسوم بيانية")
    start_date = st.date_input("من تاريخ", default_start, key="start_tab5")
    end_date = st.date_input("إلى تاريخ", default_end, key="end_tab5")
    if start_date > end_date:
        st.error("⚠️ تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
        st.stop()
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_tab5"):
        st.cache_data.clear()
        st.rerun()

    filtered_df = merged_df[(merged_df["التاريخ"] >= pd.to_datetime(start_date)) & (merged_df["التاريخ"] <= pd.to_datetime(end_date))]
    scores = filtered_df.drop(columns=["التاريخ", "username"], errors="ignore")
    grouped_filtered = filtered_df.groupby("username")[scores.columns].sum()
    grouped_filtered["المجموع"] = grouped_filtered.sum(axis=1)

    pie_fig = go.Figure(go.Pie(
        labels=grouped_filtered.index,
        values=grouped_filtered["المجموع"],
        hole=0.4,
        title="مجموع الدرجات الكلية"
    ))
    st.plotly_chart(pie_fig, use_container_width=True)
