import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# ---- Cấu hình Supabase ----
SUPABASE_URL = "https://pdftmixflpeqbzatdjij.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBkZnRtaXhmbHBlcWJ6YXRkamlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI4MDEwNDksImV4cCI6MjA2ODM3NzA0OX0.qR3HNj12dyb6dELGnoUe5je2KgkOqRHQrjne4f-AScQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- Hàm lấy user_id từ session đăng nhập ----
def get_current_user_id():
    session = st.session_state.get("supabase_session")
    if session and "user" in session:
        return session["user"]["id"]
    return None

# ---- Hàm tải lịch sử hội thoại ----
def load_messages(user_id: str):
    response = (
        supabase.table("n8n_chat_histories")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)  # lấy theo thứ tự thời gian
        .execute()
    )
    return response.data or []

# ---- Hàm lưu tin nhắn ----
def save_message(user_id: str, role: str, content: str):
    data = {
        "user_id": user_id,
        "role": role,
        "content": content
    }
    response = supabase.table("n8n_chat_histories").insert(data).execute()
    return response

# ---- Giao diện Streamlit ----
st.title("Chatbot với lưu lịch sử vào Supabase")

# Giả sử đã login và lưu session vào st.session_state["supabase_session"]
# Ở đây mình test tạm
if "supabase_session" not in st.session_state:
    st.session_state["supabase_session"] = {
        "user": {"id": "00000000-0000-0000-0000-000000000000"}  # test ID
    }

user_id = get_current_user_id()

if not user_id:
    st.warning("Bạn cần đăng nhập để chat.")
else:
    # Lần đầu load lịch sử từ Supabase
    if "messages" not in st.session_state:
        st.session_state.messages = load_messages(user_id)

    # Hiển thị lịch sử hội thoại
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Ô nhập tin nhắn
    if prompt := st.chat_input("Nhập tin nhắn"):
        # Hiển thị ngay trên UI
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Lưu vào Supabase
        save_message(user_id, "user", prompt)
