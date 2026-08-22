import streamlit as st
import gspread
import pandas as pd
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
        st.warning("👤 تم تسجيل الدخول كأدمن، سيتم تحويلك للوحة التحكم...")
        st.switch_page("pages/AdminDashboard.py")
    elif st.session_state["permissions"] == "supervisor":
        st.warning("👤 تم تسجيل الدخول كمشرف، سيتم تحويلك للتقارير...")
        st.switch_page("pages/SupervisorDashboard.py")
    else:
        st.error("⚠️ الصلاحية غير معروفة.")
    st.stop()

username = st.session_state["username"]
sheet_name = f"بيانات - {username}"
spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")
worksheet = spreadsheet.worksheet(sheet_name)
columns = worksheet.row_values(1)

# ===== تبويبات المستخدم =====
tabs = st.tabs(["📝 إدخال البيانات", "📊 تقارير المجموع", "📈 مجموع كلي"])

# ===== التبويب الأول: إدخال البيانات =====
with tabs[0]:
    st.title("📝 إدخال البيانات اليومية")
    with st.form("daily_form"):
        today = datetime.today().date()
        allowed_dates = [today - timedelta(days=i) for i in range(3)]
        date = st.date_input("📅 التاريخ", today)

        if date not in allowed_dates:
            st.warning("⚠️ يمكنك إدخال البيانات لليوم الحالي أو يومين سابقين فقط.")

        values = [date.strftime("%Y-%m-%d")]

        # الأعمدة الخمسة الأولى
        options_1 = ["في المسجد جماعة", "في المنزل جماعة", "في المسجد منفرد", "في المنزل منفرد", "خارج الوقت"]
        ratings_1 = {
            "في المسجد جماعة": 5,
            "في المنزل جماعة": 4,
            "في المسجد منفرد": 3,
            "في المنزل منفرد": 2,
            "خارج الوقت": 0
        }

        for i, col in enumerate(columns[1:6]):
            rating = st.radio(col, options=options_1, index=0, key=col)
            values.append(str(ratings_1[rating]))

        # الأعمدة الخمسة التالية
        options_2 = ["نعم", "ليس كاملاً", "لا"]
        ratings_2 = {
            "نعم": 5,
            "ليس كاملاً": 3,
            "لا": 0
        }

        for i, col in enumerate(columns[6:11]):
            rating = st.radio(col, options=options_2, index=0, key=col)
            values.append(str(ratings_2[rating]))

        # الأعمدة المتبقية
        options_3 = ["نعم", "لا"]
        ratings_3 = {
            "نعم": 3,
            "لا": 0
        }

        for i, col in enumerate(columns[11:]):
            rating = st.radio(col, options=options_3, index=0, key=col)
            values.append(str(ratings_3[rating]))

        submit = st.form_submit_button("💾 حفظ")

        if submit:
            if date not in allowed_dates:
                st.error("❌ التاريخ غير صالح. لا يمكن حفظ البيانات لغير اليوم أو اليومين السابقين.")
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
                st.success("✅ تم حفظ البيانات بنجاح")


# ===== التبويب الثاني: مجموع البنود للفترة =====
with tabs[1]:
    st.title("📊 مجموع البنود للفترة")
    df = pd.DataFrame(worksheet.get_all_records())
    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("من تاريخ", datetime.today().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("إلى تاريخ", datetime.today().date())

    mask = (df["التاريخ"] >= pd.to_datetime(start_date)) & (df["التاريخ"] <= pd.to_datetime(end_date))
    filtered = df[mask].drop(columns=["التاريخ"], errors="ignore")

    totals = filtered.sum(numeric_only=True)
    result_df = pd.DataFrame(totals, columns=["المجموع"])
    result_df.index.name = "البند"
    result_df = result_df.reset_index()
    result_df = result_df.sort_values(by="المجموع", ascending=True)

    # تغيير ترتيب الأعمدة وعكسهم مع الألوان والتوسيط
    # تعديل الأعمدة بحيث يتم عرض اسم البند أولاً ثم الدرجة المكتسبة
    result_df["البند"] = result_df["البند"].apply(lambda x: f"<p style='color:#8B0000; text-align:center'>{x}</p>")  # اسم البند باللون الأحمر العنابي
    result_df["المجموع"] = result_df["المجموع"].apply(lambda x: f"<p style='color:#000080; text-align:center'>{x}</p>")  # الدرجة المكتسبة باللون الأزرق الكحلي

    # عرض الجدول مع التنسيق
    st.markdown(result_df.to_html(escape=False), unsafe_allow_html=True)



# ===== التبويب الثالث: مجموع كلي لكافة البنود للفترة =====
with tabs[2]:
    st.title("📈 مجموع كلي لكافة البنود")
    df = pd.DataFrame(worksheet.get_all_records())
    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("من", datetime.today().date() - timedelta(days=7), key="start3")
    with col2:
        end_date = st.date_input("إلى", datetime.today().date(), key="end3")

    mask = (df["التاريخ"] >= pd.to_datetime(start_date)) & (df["التاريخ"] <= pd.to_datetime(end_date))
    filtered = df[mask].drop(columns=["التاريخ"], errors="ignore")

    total_score = filtered.sum(numeric_only=True).sum()
    st.metric(label="📌 مجموعك الكلي لجميع البنود", value=int(total_score))
