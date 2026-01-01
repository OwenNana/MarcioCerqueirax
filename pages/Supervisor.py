import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.graph_objects as go

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد الصفحة =====
st.set_page_config(page_title="التقارير", page_icon="📊")
st.title("📊 التقارير")

# ===== تحقق من صلاحية المشرف =====
if "permissions" not in st.session_state or st.session_state["permissions"] != "supervisor":
    st.error("🚫 هذه الصفحة مخصصة للمشرف فقط.")
    st.stop()

# ===== عرض التقارير =====
st.subheader("📋 قائمة التقارير")

# جلب بيانات المستخدمين
admin_sheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY").worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())
user_sheets = users_df["sheet_name"].values  # هنا نتعامل مع العامود الثالث الذي يحتوي على روابط الشيتات

# تاريخ بداية ونهاية الفترات
start_date = st.date_input("تاريخ البداية", datetime(2025, 1, 1))
end_date = st.date_input("تاريخ النهاية", datetime.today())

# التبويبات
tab1, tab2, tab3, tab4 = st.tabs(["📋 التقرير التجميعي", "📊 تقرير بند معين", "📅 تقرير فردي", "📈 الرسوم البيانية"])

# التقرير التجميعي
with tab1:
    st.header("📋 التقرير التجميعي")
    st.write("تقرير تجميعي لجميع الأشخاص بمجموع الدرجات لفترة محددة")
    
    if start_date <= end_date:
        # استخراج البيانات في الفترة المحددة
        filtered_data = users_df[(users_df['التاريخ'] >= start_date.strftime('%Y-%m-%d')) & 
                                 (users_df['التاريخ'] <= end_date.strftime('%Y-%m-%d'))]
        total_scores = filtered_data.groupby('الاسم')['الدرجات'].sum()
        st.write(total_scores)
    else:
        st.warning("تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")

# تقرير بند معين
with tab2:
    st.header("📊 تقرير بند معين")
    st.write("تقرير لكل الأشخاص وبند معين فقط")
    
    selected_bund = st.selectbox("اختر البند", ['صلاة الفجر', 'الوضوء', 'الصلاة', 'التلاوة'])
    start_date = st.date_input("ابدأ من تاريخ", datetime.today())
    end_date = st.date_input("انتهِ إلى تاريخ", datetime.today())
    
    if start_date <= end_date:
        # استخراج البيانات في الفترة المحددة للبند المختار
        filtered_data = users_df[(users_df['التاريخ'] >= start_date.strftime('%Y-%m-%d')) & 
                                 (users_df['التاريخ'] <= end_date.strftime('%Y-%m-%d'))]
        selected_bund_data = filtered_data.groupby('الاسم')[selected_bund].sum()
        st.write(selected_bund_data)
    else:
        st.warning("تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")

# تقرير فردي
with tab3:
    st.header("📅 التقرير الفردي")
    st.write("تقرير فردي لشخص معين مع تفصيل جميع البنود")

    username = st.selectbox("اختر الشخص", users_df['الاسم'].unique())
    start_date = st.date_input("ابدأ من تاريخ", datetime.today())
    end_date = st.date_input("انتهِ إلى تاريخ", datetime.today())

    if start_date <= end_date:
        # استخراج البيانات في الفترة المحددة
        filtered_data = users_df[(users_df['الاسم'] == username) & 
                                 (users_df['التاريخ'] >= start_date.strftime('%Y-%m-%d')) & 
                                 (users_df['التاريخ'] <= end_date.strftime('%Y-%m-%d'))]
        st.write(filtered_data)
    else:
        st.warning("تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")

# رسوم بيانية
with tab4:
    st.header("📈 الرسوم البيانية")
    st.write("توزيع تقارير المشرف عبر الرسوم البيانية")

    # رسم بياني عن تقرير تجميعي
    fig = go.Figure(data=[go.Pie(labels=users_df['الاسم'], values=users_df['الدرجات'], title="مجموع الدرجات لجميع الأشخاص")])
    st.plotly_chart(fig, use_container_width=True)
    
    # رسم بياني عن بند معين
    selected_bund = st.selectbox("اختر البند لعرضه في الرسم البياني", ['صلاة الفجر', 'الوضوء', 'الصلاة', 'التلاوة'])
    fig_bund = go.Figure(data=[go.Bar(x=users_df['الاسم'], y=users_df[selected_bund], title=f"مجموع {selected_bund} لكل الأشخاص")])
    st.plotly_chart(fig_bund, use_container_width=True)
