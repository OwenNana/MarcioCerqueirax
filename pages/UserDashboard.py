import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime

# ===== إعداد الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعادة التوجيه إذا لم يتم تسجيل الدخول =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("home.py")

username = st.session_state["username"]
sheet_url = st.session_state["sheet_url"]

# ===== فتح Google Sheet =====
try:
    spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")
except Exception:
    st.error("❌ حدث خطأ أثناء الاتصال بقاعدة البيانات. حاول مرة أخرى.")
    st.markdown("""<script>setTimeout(function() { window.location.href = "/home"; }, 1000);</script>""", unsafe_allow_html=True)
    st.stop()

# ===== تحميل بيانات المشرف =====
admin_sheet = spreadsheet.worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())

# تعريب أعمدة المستخدمين
users_df.rename(columns={
    "username": "اسم المستخدم",
    "password": "كلمة السر",
    "sheet_name": "الصفحة",
    "role": "الصلاحيات",
    "Mentor": "المرجع"
}, inplace=True)

# الحصول على اسم المشرف والمرجع
user_row = users_df[users_df["اسم المستخدم"] == username]
mentor_name = user_row["المرجع"].values[0] if not user_row.empty else "غير معروف"

sp_row = users_df[users_df["اسم المستخدم"] == mentor_name]
sp_name = sp_row["المرجع"].values[0] if not sp_row.empty else None

# ===== إعداد الصفحة =====
st.set_page_config(page_title="📋 تقييم المستخدم", layout="wide")

tabs = st.tabs(["💬 المحادثات", "📝 إدخال البيانات", "📊 التقارير"])

# ========== التبويب الأول: المحادثة ==========
with tabs[0]:
    st.subheader(f"أهلاً {username} | مجموعتك: {mentor_name}")
    st.button("🔄 جلب المعلومات من قاعدة البيانات", on_click=st.cache_data.clear)

    chat_sheet = spreadsheet.worksheet("chat")
    chat_raw = chat_sheet.get_all_records()

    chat_data = pd.DataFrame(chat_raw).rename(columns={
        "timestamp": "وقت الدردشة",
        "from": "من",
        "to": "إلى",
        "message": "الرسالة",
        "is_read": "تمت قراءتها"
    })

    options = []
    if sp_name:
        options.append((sp_name, "مسؤول"))
    options.append((mentor_name, "مشرف"))

    selected_option = st.selectbox("📨 اختر الشخص الذي ترغب بمراسلته", options, format_func=lambda x: f"{x[0]} ({x[1]})")
    selected_mentor = selected_option[0]

    if not chat_data.empty and {"من", "إلى", "الرسالة", "وقت الدردشة"}.issubset(chat_data.columns):
        msgs = chat_data[((chat_data["من"] == username) & (chat_data["إلى"] == selected_mentor)) |
                         ((chat_data["من"] == selected_mentor) & (chat_data["إلى"] == username))].sort_values("وقت الدردشة")

        for _, msg in msgs.iterrows():
            sender = "👤 أنت" if msg["من"] == username else f"🧑‍🏫 {msg['من']}"
            color = "#000080" if msg["من"] == username else "#8B0000"
            st.markdown(f"<p style='color:{color};'><b>{sender}:</b> {msg['الرسالة']}</p>", unsafe_allow_html=True)

    else:
        st.info("💬 لا توجد رسائل حالياً.")

    new_msg = st.text_area("✏️ اكتب رسالتك هنا", height=100, key="chat_message")
    if st.button("📨 إرسال الرسالة"):
        if new_msg.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            chat_sheet.append_row([timestamp, username, selected_mentor, new_msg, ""])
            st.session_state["chat_message"] = ""
            st.success("✅ تم إرسال الرسالة")
            st.rerun()
        else:
            st.warning("⚠️ لا يمكن إرسال رسالة فارغة.")


# ===== التبويبات =====
tabs = st.tabs(["💬 المحادثات", "📝 إدخال البيانات", "📊 تقارير المجموع"])

# ===== التبويب الأول: المحادثة =====
with tabs[0]:
    st.title(f"👋 أهلاً {username} | 🧑‍🏫 مجموعتك: {mentor_name}")
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
