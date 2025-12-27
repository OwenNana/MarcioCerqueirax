import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# إعداد صفحة Streamlit
st.set_page_config(layout="wide", page_title="📊 تقارير المشرف")

# الاتصال بـ Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# تحميل بيانات التقارير
def load_data():
    sheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY").worksheet("admin")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

data = load_data()

# التبويبات
tab1, tab2, tab3, tab4 = st.tabs(["📋 التقرير التجميعي", "📊 تقرير بند معين", "📅 تقرير فردي", "📈 رسوم بيانية"])

# التقرير التجميعي
with tab1:
    st.header("📋 التقرير التجميعي")
    st.write("تقرير تجميعي لجميع الأشخاص بمجموع الدرجات لفترة محددة")
    
    start_date = st.date_input("ابدأ من تاريخ", datetime.today())
    end_date = st.date_input("انتهِ إلى تاريخ", datetime.today())
    
    if start_date <= end_date:
        # استخراج البيانات في الفترة المحددة
        filtered_data = data[(data['التاريخ'] >= start_date.strftime('%Y-%m-%d')) & (data['التاريخ'] <= end_date.strftime('%Y-%m-%d'))]
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
        filtered_data = data[(data['التاريخ'] >= start_date.strftime('%Y-%m-%d')) & (data['التاريخ'] <= end_date.strftime('%Y-%m-%d'))]
        selected_bund_data = filtered_data.groupby('الاسم')[selected_bund].sum()
        st.write(selected_bund_data)
    else:
        st.warning("تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")

# تقرير فردي
with tab3:
    st.header("📅 التقرير الفردي")
    st.write("تقرير فردي لشخص معين مع تفصيل جميع البنود")

    username = st.selectbox("اختر الشخص", data['الاسم'].unique())
    start_date = st.date_input("ابدأ من تاريخ", datetime.today())
    end_date = st.date_input("انتهِ إلى تاريخ", datetime.today())

    if start_date <= end_date:
        # استخراج البيانات في الفترة المحددة
        filtered_data = data[(data['الاسم'] == username) & (data['التاريخ'] >= start_date.strftime('%Y-%m-%d')) & (data['التاريخ'] <= end_date.strftime('%Y-%m-%d'))]
        st.write(filtered_data)
    else:
        st.warning("تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")

# رسوم بيانية
with tab4:
    st.header("📈 الرسوم البيانية")
    st.write("توزيع تقارير المشرف عبر الرسوم البيانية")

    # رسم بياني عن تقرير تجميعي
    fig = px.pie(data, names='الاسم', values='الدرجات', title="مجموع الدرجات لجميع الأشخاص")
    st.plotly_chart(fig, use_container_width=True)
    
    # رسم بياني عن بند معين
    selected_bund = st.selectbox("اختر البند لعرضه في الرسم البياني", ['صلاة الفجر', 'الوضوء', 'الصلاة', 'التلاوة'])
    fig_bund = px.bar(data, x='الاسم', y=selected_bund, title=f"مجموع {selected_bund} لكل الأشخاص")
    st.plotly_chart(fig_bund, use_container_width=True)
