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
        st.switch_page("pages/Supervisor.py")
    else:
        st.error("⚠️ الصلاحية غير معروفة.")
    st.stop()

username = st.session_state["username"]
sheet_name = f"بيانات - {username}"
spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")
worksheet = spreadsheet.worksheet(sheet_name)
columns = worksheet.row_values(1)

# ===== دالة جلب البيانات من جوجل شيت =====
def load_data():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# ===== تبويبات المستخدم =====
tabs = st.tabs(["📝 إدخال البيانات", "📊 تقارير المجموع"])

# ===== التبويب الأول: إدخال البيانات =====
with tabs[0]:
    st.title(f"👋 أهلاً {username}")

    with st.form("daily_form"):
        today = datetime.today().date()
        allowed_dates = [today - timedelta(days=i) for i in range(7)]
        date = st.date_input("📅 التاريخ", today)

        if date not in allowed_dates:
            st.warning("⚠️ يمكن تعبئة البيانات خلال أسبوع سابق من اليوم فقط.")

        values = [date.strftime("%Y-%m-%d")]

        # الأعمدة الخمسة الأولى
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
            st.markdown(f"<h4 style='font-weight: bold;'>{col}</h4>", unsafe_allow_html=True)  # العنوان بخط أكبر
            rating = st.radio(col, options=options_1, index=0, key=col)
            values.append(str(ratings_1[rating]))

        # الأعمدة الخمسة التالية
        st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>الاختيارات الثانية</h3>", unsafe_allow_html=True)
        options_2 = ["نعم", "ليس كاملاً", "لا"]
        ratings_2 = {
            "نعم": 5,
            "ليس كاملاً": 3,
            "لا": 0
        }

        for i, col in enumerate(columns[6:11]):
            st.markdown(f"<h4 style='font-weight: bold;'>{col}</h4>", unsafe_allow_html=True)  # العنوان بخط أكبر
            rating = st.radio(col, options=options_2, index=0, key=col)
            values.append(str(ratings_2[rating]))

        # الأعمدة المتبقية
        st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>الاختيارات الأخيرة</h3>", unsafe_allow_html=True)
        options_3 = ["نعم", "لا"]
        ratings_3 = {
            "نعم": 3,
            "لا": 0
        }

        for i, col in enumerate(columns[11:]):
            st.markdown(f"<h4 style='font-weight: bold;'>{col}</h4>", unsafe_allow_html=True)  # العنوان بخط أكبر
            rating = st.radio(col, options=options_3, index=0, key=col)
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

                # بعد الحفظ مباشرةً جلب البيانات الجديدة
                st.cache_data.clear()  # تفريغ الذاكرة المخبأة
                data = load_data()  # جلب البيانات الجديدة من جوجل شيت

                # عرض رسالة النجاح فقط
                st.success("✅ تم الحفظ بنجاح والاتصال بقاعدة البيانات")

# ===== التبويب الثاني: تقارير المجموع =====
with tabs[1]:  # التبويب الثاني
    st.title("📊 مجموع البنود للفترة")
    
    # زيادة حجم الخط للعناوين في هذا التبويب أيضًا
    st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>التقارير</h3>", unsafe_allow_html=True)

    df = pd.DataFrame(worksheet.get_all_records())
    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")

    # إزالة الأعمدة غير المسماة التي تحتوي على أرقام تسلسلية (أو أي عمود غير ضروري)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # إزالة الأعمدة التي تبدأ بـ 'Unnamed' (غالبًا تحتوي على أرقام تسلسلية)

    # إزالة الصفوف التي تحتوي على بيانات فارغة في "البند" أو "المجموع"
    if "البند" in df.columns and "المجموع" in df.columns:
        df = df.dropna(subset=["البند", "المجموع"])

    # إزالة عمود الأرقام التسلسلية إذا كان موجودًا
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
    total_score = totals.sum()  # حساب مجموع جميع الدرجات

    # عرض مجموع الدرجات الكلي
    st.metric(label="📌 مجموعك الكلي لجميع البنود", value=int(total_score))

    # الآن عرض مجموع البنود للفترة
    result_df = pd.DataFrame(totals, columns=["المجموع"])
    result_df.index.name = "البند"
    result_df = result_df.reset_index()
    result_df = result_df.sort_values(by="المجموع", ascending=True)

    # عكس ترتيب الأعمدة: نعرض المجموع أولًا ثم اسم البند
    result_df = result_df[["المجموع", "البند"]]  # ترتيب الأعمدة بحيث يظهر المجموع أولًا

    # تغيير ترتيب الأعمدة وعكسهم مع الألوان والتوسيط
    result_df["البند"] = result_df["البند"].apply(lambda x: f"<p style='color:#8B0000; text-align:center'>{x}</p>")  # اسم البند باللون الأحمر العنابي
    result_df["المجموع"] = result_df["المجموع"].apply(lambda x: f"<p style='color:#000080; text-align:center'>{x}</p>")  # الدرجة المكتسبة باللون الأزرق الكحلي

    # عرض الجدول مع التنسيق
    st.markdown(result_df.to_html(escape=False), unsafe_allow_html=True)
