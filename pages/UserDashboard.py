import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials

# ===== دالة جلب البيانات من جوجل شيت =====
def load_data():
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    
    SHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"  # معرف الشيت
    sheet = client.open_by_key(SHEET_ID).worksheet("admin")  # ورقة العمل
    data = sheet.get_all_records()  # جلب البيانات
    df = pd.DataFrame(data)  # تحويل البيانات إلى DataFrame
    return df

# ===== التبويب الأول: إدخال البيانات =====
with tabs[0]:
    st.title("📝 إدخال البيانات اليومية")
    with st.form("daily_form"):
        today = datetime.today().date()
        allowed_dates = [today - timedelta(days=i) for i in range(7)]
        date = st.date_input("📅 التاريخ", today)

        if date not in allowed_dates:
            st.warning("⚠️ يمكن تعبئة البيانات خلال أسبوع سابق من اليوم فقط.")

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
                st.success("✅ تم حفظ البيانات بنجاح و جلب البيانات من قاعدة البيانات")
