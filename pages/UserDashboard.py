import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ===== إعادة التوجيه إلى صفحة تسجيل الدخول إذا لم يتم تسجيل الدخول =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("home.py")

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد الصفحة =====
st.set_page_config(page_title="تقييم اليوم", page_icon="📋", layout="wide")

# ===== تحقق من صلاحية المستخدم =====
if "username" not in st.session_state or "sheet_url" not in st.session_state:
    st.error("❌ يجب تسجيل الدخول أولاً.")
    st.stop()

if st.session_state["permissions"] != "user":
    if st.session_state["permissions"] == "admin":
        st.warning(" تم تسجيل الدخول كأدمن، سيتم تحويلك للوحة التحكم...")
        st.switch_page("pages/AdminDashboard.py")
    elif st.session_state["permissions"] in ["supervisor", "sp"]:
        st.warning(" تم تسجيل الدخول كمشرف، سيتم تحويلك للتقارير...")
        st.switch_page("pages/Supervisor.py")
    else:
        st.error("⚠️ صلاحية غير معروفة.")
    st.stop()

username = st.session_state["username"]
sheet_name = f"بيانات - {username}"
try:
    spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")
except Exception:
    st.error("❌ حدث خطأ أثناء الاتصال بقاعدة البيانات. حاول مرة أخرى.")
    st.markdown("""<script>
        setTimeout(function() {
            window.location.href = "/home";
        }, 1000);
    </script>""", unsafe_allow_html=True)
    st.stop()

worksheet = spreadsheet.worksheet(sheet_name)
columns = worksheet.row_values(1)

# ===== جلب اسم المشرف =====
admin_sheet = spreadsheet.worksheet("admin")
admin_data = pd.DataFrame(admin_sheet.get_all_records())
mentor_name = admin_data.loc[admin_data["username"] == username, "Mentor"].values[0]

# جلب السوبر مشرف إن وجد
sp_row = admin_data[(admin_data["username"] == mentor_name)]
sp_name = sp_row["Mentor"].values[0] if not sp_row.empty else None

if not columns:
    st.error("❌ لم يتم العثور على الأعمدة في ورقة البيانات.")
    st.stop()

def refresh_button(key):
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key=key):
        st.cache_data.clear()
        st.rerun()

def load_data():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# ===== دالة عرض المحادثة =====
def show_chat():
    st.markdown("### 💬 المحادثة مع المشرف أو السوبر مشرف")

    # تحديد الجهة: مشرف أو سوبر مشرف
    options = [mentor_name]
    if sp_name:
        options.append(sp_name)

    selected_mentor = st.selectbox("📨 اختر الشخص الذي ترغب بمراسلته", options, index=0, format_func=lambda x: f" {x}")

    chat_sheet = spreadsheet.worksheet("chat")
    raw_data = chat_sheet.get_all_records()
    chat_data = pd.DataFrame(raw_data) if raw_data else pd.DataFrame(columns=["timestamp", "from", "to", "message"])

    if not {"from", "to", "message", "timestamp"}.issubset(chat_data.columns):
        st.warning("⚠️ لم يتم العثور على الأعمدة الصحيحة في ورقة الدردشة.")
        return

    messages = chat_data[((chat_data["from"] == username) & (chat_data["to"] == selected_mentor)) |
                         ((chat_data["from"] == selected_mentor) & (chat_data["to"] == username))]
    messages = messages.sort_values(by="timestamp")

    if messages.empty:
        st.info("💬 لا توجد رسائل حالياً.")
    else:
        for _, msg in messages.iterrows():
            if msg["from"] == username:
                st.markdown(f"<p style='color:#000080'><b> أنت:</b> {msg['message']}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color:#8B0000'><b> {msg['from']}:</b> {msg['message']}</p>", unsafe_allow_html=True)

    new_msg = st.text_area("✏️ اكتب رسالتك هنا", height=100)
    if st.button("📨 إرسال الرسالة"):
        if new_msg.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            chat_sheet.append_row([timestamp, username, selected_mentor, new_msg])
            st.success("✅ تم إرسال الرسالة")
            st.rerun()
        else:
            st.warning("⚠️ لا يمكن إرسال رسالة فارغة.")

# ===== التبويبات =====
tabs = st.tabs(["💬 المحادثات", "📝 إدخال البيانات", "📊 تقارير المجموع"])

# ===== التبويب الأول: المحادثة =====
with tabs[0]:
    st.title(f"👋 أهلاً {username} |  مجموعتك / {mentor_name}")
    refresh_button("refresh_chat")
    show_chat()
# ===== التبويب الثاني: إدخال البيانات =====
with tabs[1]:
    st.title("📝 تعبئة النموذج اليومي")
    refresh_button("refresh_tab1")

    with st.form("daily_form"):
        today = datetime.today().date()
        allowed_dates = [today - timedelta(days=i) for i in range(7)]
        date = st.date_input("📅 التاريخ", today)

        if date not in allowed_dates:
            st.warning("⚠️ يمكن تعبئة البيانات خلال أسبوع سابق من اليوم فقط.")

        values = [date.strftime("%Y-%m-%d")]

        # الاختيارات الأولى
        st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>الاختيارات الأولى</h3>", unsafe_allow_html=True)
        options_1 = ["في المسجد جماعة", "في المنزل جماعة", "في المسجد منفرد", "في المنزل منفرد", "خارج الوقت"]
        ratings_1 = {
            "في المسجد جماعة": 5,
            "في المنزل جماعة": 4,
            "في المسجد منفرد": 3,
            "في المنزل منفرد": 2,
            "خارج الوقت": 0
        }

        for i, col in enumerate(columns[1:6]):
            st.markdown(f"<h4 style='font-weight: bold;'>{col}</h4>", unsafe_allow_html=True)
            rating = st.radio(col, options_1, index=0, key=col)
            values.append(str(ratings_1[rating]))

        # الاختيارات الثانية
        st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>الاختيارات الثانية</h3>", unsafe_allow_html=True)
        options_2 = ["نعم", "ليس كاملاً", "لا"]
        ratings_2 = {
            "نعم": 5,
            "ليس كاملاً": 3,
            "لا": 0
        }

        for i, col in enumerate(columns[6:11]):
            st.markdown(f"<h4 style='font-weight: bold;'>{col}</h4>", unsafe_allow_html=True)
            rating = st.radio(col, options_2, index=0, key=col)
            values.append(str(ratings_2[rating]))

        # الاختيارات الأخيرة
        st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>الاختيارات الأخيرة</h3>", unsafe_allow_html=True)
        options_3 = ["نعم", "لا"]
        ratings_3 = {
            "نعم": 3,
            "لا": 0
        }

        for i, col in enumerate(columns[11:]):
            st.markdown(f"<h4 style='font-weight: bold;'>{col}</h4>", unsafe_allow_html=True)
            rating = st.radio(col, options_3, index=0, key=col)
            values.append(str(ratings_3[rating]))

        submit = st.form_submit_button("💾 حفظ")

        if submit:
            if date not in allowed_dates:
                st.error("❌ التاريخ غير صالح. لا يمكن حفظ البيانات لأكثر من أسبوع سابق فقط")
            else:
                all_dates = worksheet.col_values(1)
                date_str = date.strftime("%Y-%m-%d")
                try:
                    row_index = all_dates.index(date_str) + 1
                except ValueError:
                    row_index = len(all_dates) + 1
                    worksheet.update_cell(row_index, 1, date_str)
                for i, val in enumerate(values[1:], start=2):
                    worksheet.update_cell(row_index, i, val)

                st.cache_data.clear()
                data = load_data()
                st.success("✅ تم الحفظ بنجاح والاتصال بقاعدة البيانات")

# ===== التبويب الثالث: تقارير المجموع =====
with tabs[2]:
    st.title("📊 مجموع البنود للفترة")
    refresh_button("refresh_tab2")

    st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>التقارير</h3>", unsafe_allow_html=True)

    df = pd.DataFrame(worksheet.get_all_records())
    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    if "البند" in df.columns and "المجموع" in df.columns:
        df = df.dropna(subset=["البند", "المجموع"])

    if "رقم التسلسل" in df.columns:
        df = df.drop(columns=["رقم التسلسل"])

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("من تاريخ", datetime.today().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("إلى تاريخ", datetime.today().date())

    mask = (df["التاريخ"] >= pd.to_datetime(start_date)) & (df["التاريخ"] <= pd.to_datetime(end_date))
    filtered = df[mask].drop(columns=["التاريخ"], errors="ignore")

    totals = filtered.sum(numeric_only=True)
    total_score = totals.sum()

    st.metric(label="📌 مجموعك الكلي لجميع البنود", value=int(total_score))

    result_df = pd.DataFrame(totals, columns=["المجموع"])
    result_df.index.name = "البند"
    result_df = result_df.reset_index()
    result_df = result_df.sort_values(by="المجموع", ascending=True)

    result_df = result_df[["المجموع", "البند"]]
    result_df["البند"] = result_df["البند"].apply(lambda x: f"<p style='color:#8B0000; text-align:center'>{x}</p>")
    result_df["المجموع"] = result_df["المجموع"].apply(lambda x: f"<p style='color:#000080; text-align:center'>{x}</p>")

    st.markdown(result_df.to_html(escape=False, index=False), unsafe_allow_html=True)
