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
# ===== تحديد الفترة الزمنية =====
start_date = st.date_input("من تاريخ", datetime.today())
end_date = st.date_input("إلى تاريخ", datetime.today())
if start_date > end_date:
    st.error("⚠️ تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
    st.stop()

# ===== تصفية المستخدمين حسب الصلاحيات =====
if permissions == "supervisor":
    filtered_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"] == username)]
elif permissions == "sp":
    supervised_supervisors = users_df[(users_df["role"] == "supervisor") & (users_df["Mentor"] == username)]["username"].tolist()
    filtered_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"].isin(supervised_supervisors))]

if filtered_users.empty:
    st.info("ℹ️ لا يوجد طلاب لعرض تقاريرهم.")
    st.stop()

# ===== جلب البيانات لكل طالب =====
all_data = []
users_with_data = []
all_usernames = filtered_users["username"].tolist()

for _, user in filtered_users.iterrows():
    username = user["username"]
    sheet_name = user["sheet_name"]
    try:
        user_ws = spreadsheet.worksheet(sheet_name)
        user_records = user_ws.get_all_records()
        df = pd.DataFrame(user_records)
        if "التاريخ" in df.columns:
            df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
            df = df[(df["التاريخ"] >= pd.to_datetime(start_date)) & (df["التاريخ"] <= pd.to_datetime(end_date))]
            if not df.empty:
                df.insert(0, "username", username)
                all_data.append(df)
                users_with_data.append(username)
            else:
                empty_df = pd.DataFrame(columns=df.columns)
                empty_df["username"] = [username]
                empty_df["التاريخ"] = pd.NaT
                for col in empty_df.columns:
                    if col not in ["username", "التاريخ"]:
                        empty_df[col] = 0
                all_data.append(empty_df)
                users_with_data.append(username)
    except Exception as e:
        st.warning(f"⚠️ خطأ في تحميل بيانات {username}: {e}")

if not all_data:
    st.info("ℹ️ لا توجد بيانات في الفترة المحددة.")
    st.stop()

merged_df = pd.concat(all_data, ignore_index=True)

# ========== تبويب 2: تقرير إجمالي ==========
with tabs[1]:
    st.subheader("👤 مجموع درجات كل مستخدم")
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_tab1"):
        st.cache_data.clear()
        st.rerun()
    scores = merged_df.drop(columns=["التاريخ", "username"], errors="ignore")
    grouped = merged_df.groupby("username")[scores.columns].sum()
    grouped["المجموع"] = grouped.sum(axis=1)
    cols = grouped.columns.tolist()
    if "المجموع" in cols:
        cols.insert(0, cols.pop(cols.index("المجموع")))
        grouped = grouped[cols]
    grouped = grouped.sort_values(by="المجموع", ascending=True)
    for index, row in grouped.iterrows():
        st.markdown(f"### <span style='color: #006400;'>{index} : {row['المجموع']} درجة</span>", unsafe_allow_html=True)

# ========== تبويب 3: تجميعي الكل ==========
with tabs[2]:
    st.subheader("📋 مجموع الدرجات لكل مستخدم")
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_tab2"):
        st.cache_data.clear()
        st.rerun()
    st.dataframe(grouped, use_container_width=True)

# ========== تبويب 4: تجميعي بند ==========
with tabs[3]:
    st.subheader("📌 مجموع بند معين لكل المستخدمين")
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

# ========== تبويب 5: تقرير فردي ==========
with tabs[4]:
    st.subheader("👤 تقرير تفصيلي لمستخدم")
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_tab4"):
        st.cache_data.clear()
        st.rerun()
    selected_user = st.selectbox("اختر المستخدم", merged_df["username"].unique())
    user_df = merged_df[merged_df["username"] == selected_user].sort_values("التاريخ")
    st.dataframe(user_df.reset_index(drop=True), use_container_width=True)

# ========== تبويب 6: رسوم بيانية ==========
with tabs[5]:
    st.subheader("📈 رسوم بيانية")
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_tab5"):
        st.cache_data.clear()
        st.rerun()
    pie_fig = go.Figure(go.Pie(
        labels=grouped.index,
        values=grouped["المجموع"],
        hole=0.4,
        title="مجموع الدرجات الكلية"
    ))
    st.plotly_chart(pie_fig, use_container_width=True)
