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
    st.session_state["supabase_session"] = {"user": {"id": "00000000-0000-0000-0000-000000000000"}}  # test ID

user_id = get_current_user_id()

if not user_id:
    st.warning("Bạn cần đăng nhập để chat.")
else:
    message = st.text_input("Nhập tin nhắn:")
    role = st.selectbox("Vai trò", ["user", "assistant"])

    if st.button("Gửi"):
        resp = save_message(user_id, role, message)
        if resp.data:
            st.success("Đã lưu tin nhắn vào Supabase!")
        else:
            st.error("Lưu thất bại.")
