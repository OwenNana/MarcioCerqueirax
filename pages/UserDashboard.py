# ===== التبويب الأول: المحادثة =====
with tabs[0]:

    st.markdown(
        """
        <style>
        body, .stTextInput, .stTextArea, .stSelectbox, .stButton, .stMarkdown, .stDataFrame {
            direction: rtl;
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title(f"👋 أهلاً {username} |  مجموعتك / {mentor_name}")
    refresh_button("refresh_chat")

    # ===== تنبيه بالرسائل غير المقروءة =====
    chat_sheet = spreadsheet.worksheet("chat")
    chat_data = pd.DataFrame(chat_sheet.get_all_records())

    if "read_by_receiver" in chat_data.columns:
        unread_msgs = chat_data[
            (chat_data["to"] == username) &
            (chat_data["message"].notna()) &
            (chat_data["read_by_receiver"].astype(str).str.strip() == "")
        ]
        senders = unread_msgs["from"].unique().tolist()
        if senders:
            sender_list = "، ".join(senders)
            st.markdown(f"""
<table style="width:100%;">
<tr>
<td style="direction: rtl; text-align: right; color: red; font-weight: bold; font-size: 16px;">
📬 يوجد لديك رسائل لم تطلع عليها من: ({sender_list})
</td>
</tr>
</table>
""", unsafe_allow_html=True)

    show_chat()
