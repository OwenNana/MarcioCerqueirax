# ===== دالة عرض المحادثة =====
def show_chat():
    st.markdown("### 💬 المحادثة مع المشرف أو السوبر مشرف")

    # تحديد الجهة: مشرف أو سوبر مشرف
    options = []
    if sp_name:
        options.append((sp_name, "مسؤول"))
    options.append((mentor_name, "مشرف"))

    selected_option = st.selectbox(
        "📨 اختر الشخص الذي ترغب بمراسلته",
        options,
        index=0,
        format_func=lambda x: f"{x[0]} ({x[1]})"
    )
    selected_mentor = selected_option[0]

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
                st.markdown(f"<p style='color:#000080'><b>🙋‍♂️ أنت:</b> {msg['message']}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color:#8B0000'><b>🧑‍🏫 {msg['from']}:</b> {msg['message']}</p>", unsafe_allow_html=True)
    new_msg = st.text_area("✏️ اكتب رسالتك هنا", height=100, key="chat_message")

    if st.button("📨 إرسال الرسالة"):
        if new_msg.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            chat_sheet.append_row([timestamp, username, selected_mentor, new_msg])
            st.session_state["chat_message"] = ""  # ← تفريغ الرسالة بعد الإرسال
            st.success("✅ تم إرسال الرسالة")
            st.rerun()
        else:
            st.warning("⚠️ لا يمكن إرسال رسالة فارغة.")
