import streamlit as st
from supabase import create_client, Client
import uuid
import json
from typing import List, Dict

# cấu hình supabase (không đưa key thật lên public)
SUPABASE_URL = st.secrets.get("SUPABASE_URL") or "https://pdftmixflpeqbzatdjij.supabase.co"
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or "YeyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBkZnRtaXhmbHBlcWJ6YXRkamlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI4MDEwNDksImV4cCI6MjA2ODM3NzA0OX0.qR3HNj12dyb6dELGnoUe5je2KgkOqRHQrjne4f-AScQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# đảm bảo có session_id (dùng để phân biệt mỗi cuộc hội thoại)
def get_session_id():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

# parse 1 row từ supabase -> trả về (role, content, image_url, created_at)
def parse_row_to_message(row: Dict):
    # ưu tiên cột 'content' và 'role' nếu đã có
    content = row.get("content") or ""
    role = row.get("role")
    image_url = row.get("image_url") or row.get("url") or None
    created_at = row.get("created_at") or row.get("createdAt") or None

    # nếu chưa có content hoặc role, thử parse cột 'message' (jsonb)
    if (not content or not role) and row.get("message") is not None:
        m = row.get("message")
        # supabase-py thường trả dict cho jsonb, nhưng nếu là str thì load
        m_json = {}
        if isinstance(m, str):
            try:
                m_json = json.loads(m)
            except:
                m_json = {}
        elif isinstance(m, dict):
            m_json = m
        # nhiều cấu trúc có key 'content' và 'type' (human/ai)
        if not content:
            content = m_json.get("content") or m_json.get("text") or content
        if not role:
            typ = (m_json.get("type") or m_json.get("role") or "").lower()
            if typ in ("human", "user"):
                role = "user"
            elif typ in ("ai", "assistant", "bot"):
                role = "assistant"
            else:
                # thử map theo field khác
                role = row.get("role") or "assistant"

    # fallback role
    if not role:
        role = "assistant" if "ai" in (row.get("source") or "").lower() else "user" if "human" in (row.get("source") or "").lower() else "user"

    return {"role": role, "content": content, "image_url": image_url, "created_at": created_at}

# load messages theo session_id
def load_messages_for_session(session_id: str) -> List[Dict]:
    resp = supabase.table("n8n_chat_histories") \
        .select("*") \
        .eq("session_id", session_id) \
        .order("created_at", asc=True) \
        .execute()
    rows = resp.data or []
    msgs = []
    for r in rows:
        msg = parse_row_to_message(r)
        # nếu content rỗng thì bỏ qua
        if msg["content"]:
            msgs.append(msg)
    return msgs

# lưu tin nhắn (nên ghi cả session_id + json message + content + role)
def save_message(session_id: str, role: str, content: str, image_url: str = None):
    payload = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "message": {"type": "human" if role == "user" else "ai", "content": content}
    }
    if image_url:
        payload["image_url"] = image_url
    res = supabase.table("n8n_chat_histories").insert(payload).execute()
    return res

# ------------------ UI đơn giản để test ------------------
st.title("Chat - load/save via session_id")

session_id = get_session_id()
st.sidebar.write("Session id:")
st.sidebar.code(session_id)

# load once vào session_state
if "messages" not in st.session_state:
    st.session_state.messages = load_messages_for_session(session_id)

# hiển thị hiện có
for m in st.session_state.messages:
    if m["role"] == "user":
        st.markdown(f"**Bạn:** {m['content']}")
    else:
        st.markdown(f"🤖 {m['content']}")
    if m.get("image_url"):
        st.image(m["image_url"])

# nhập tin nhắn mới
if prompt := st.chat_input("Nhập tin nhắn..."):
    # show ngay
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    # lưu DB
    save_message(session_id, "user", prompt)
    st.experimental_rerun()
