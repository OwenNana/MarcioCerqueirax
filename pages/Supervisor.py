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
st.set_page_config(page_title="📊 لوحة المشرف", page_icon="📊", layout="wide")
st.title(f"👋 أهلاً {username}")

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

# ===== تبويبات التقارير =====
tabs = st.tabs(["💬 المحادثات", "👤 تقرير إجمالي", "📋 تجميعي الكل", "📌 تجميعي بند", "👤 تقرير فردي", "📈 رسوم بيانية"])

with tabs[0]:
    show_chat_supervisor()
# ===== إعداد الفترة =====
default_start = datetime.today().replace(day=1)
default_end = datetime.today()

# ===== تحميل وتصفية البيانات =====
if permissions == "supervisor":
    filtered_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"] == username)]
elif permissions == "sp":
    supervised_supervisors = users_df[(users_df["role"] == "supervisor") & (users_df["Mentor"] == username)]["username"].tolist()
    filtered_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"].isin(supervised_supervisors))]

all_data = []
users_with_data = []
all_usernames = filtered_users["username"].tolist()

for _, user in filtered_users.iterrows():
    user_name = user["username"]
    sheet_name = user["sheet_name"]
    try:
        user_ws = spreadsheet.worksheet(sheet_name)
        user_records = user_ws.get_all_records()
        df = pd.DataFrame(user_records)
        if "التاريخ" in df.columns:
            df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
            df.insert(0, "username", user_name)
            all_data.append(df)
            users_with_data.append(user_name)
    except Exception as e:
        st.warning(f"⚠️ خطأ في تحميل بيانات {user_name}: {e}")

if not all_data:
    st.info("ℹ️ لا توجد بيانات.")
    st.stop()

merged_df = pd.concat(all_data, ignore_index=True)

# ===== تبويب 2: تقرير إجمالي =====
with tabs[1]:
    st.subheader("👤 مجموع درجات كل مستخدم")
    start = st.date_input("من تاريخ", default_start, key="start1")
    end = st.date_input("إلى تاريخ", default_end, key="end1")
    if st.button("🔄 تحديث", key="refresh1"):
        st.cache_data.clear()
        st.rerun()

    df = merged_df[(merged_df["التاريخ"] >= pd.to_datetime(start)) & (merged_df["التاريخ"] <= pd.to_datetime(end))]
    scores = df.drop(columns=["التاريخ", "username"], errors="ignore")
    grouped = df.groupby("username")[scores.columns].sum()
    grouped["المجموع"] = grouped.sum(axis=1)
    grouped = grouped.sort_values(by="المجموع", ascending=True)

    for user, row in grouped.iterrows():
        st.markdown(f"### <span style='color: #006400;'>{user} : {row['المجموع']} درجة</span>", unsafe_allow_html=True)

# ===== تبويب 3: تجميعي الكل =====
with tabs[2]:
    st.subheader("📋 مجموع الدرجات لكل مستخدم")
    start = st.date_input("من تاريخ", default_start, key="start2")
    end = st.date_input("إلى تاريخ", default_end, key="end2")
    df = merged_df[(merged_df["التاريخ"] >= pd.to_datetime(start)) & (merged_df["التاريخ"] <= pd.to_datetime(end))]
    scores = df.drop(columns=["التاريخ", "username"], errors="ignore")
    grouped = df.groupby("username")[scores.columns].sum()
    grouped["المجموع"] = grouped.sum(axis=1)
    st.dataframe(grouped, use_container_width=True)

# ===== تبويب 4: تجميعي بند =====
with tabs[3]:
    st.subheader("📌 مجموع بند معين لكل المستخدمين")
    start = st.date_input("من تاريخ", default_start, key="start3")
    end = st.date_input("إلى تاريخ", default_end, key="end3")
    df = merged_df[(merged_df["التاريخ"] >= pd.to_datetime(start)) & (merged_df["التاريخ"] <= pd.to_datetime(end))]
    col = st.selectbox("اختر البند", [c for c in df.columns if c not in ["التاريخ", "username"]])
    result = df.groupby("username")[col].sum().sort_values(ascending=True)
    st.dataframe(result, use_container_width=True)

# ===== تبويب 5: تقرير فردي =====
with tabs[4]:
    st.subheader("👤 تقرير تفصيلي لمستخدم")
    start = st.date_input("من تاريخ", default_start, key="start4")
    end = st.date_input("إلى تاريخ", default_end, key="end4")
    user = st.selectbox("اختر المستخدم", merged_df["username"].unique())
    df = merged_df[(merged_df["username"] == user) & (merged_df["التاريخ"] >= pd.to_datetime(start)) & (merged_df["التاريخ"] <= pd.to_datetime(end))]
    st.dataframe(df.reset_index(drop=True), use_container_width=True)

# ===== تبويب 6: رسوم بيانية =====
with tabs[5]:
    st.subheader("📈 رسوم بيانية")
    start = st.date_input("من تاريخ", default_start, key="start5")
    end = st.date_input("إلى تاريخ", default_end, key="end5")
    df = merged_df[(merged_df["التاريخ"] >= pd.to_datetime(start)) & (merged_df["التاريخ"] <= pd.to_datetime(end))]
    scores = df.drop(columns=["التاريخ", "username"], errors="ignore")
    grouped = df.groupby("username")[scores.columns].sum()
    grouped["المجموع"] = grouped.sum(axis=1)

    fig = go.Figure(go.Pie(
        labels=grouped.index,
        values=grouped["المجموع"],
        hole=0.4,
        title="مجموع الدرجات"
    ))
    st.plotly_chart(fig, use_container_width=True)
