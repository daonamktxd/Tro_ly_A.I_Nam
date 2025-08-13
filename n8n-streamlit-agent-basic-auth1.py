import json
import streamlit as st
from typing import List, Dict

def parse_row_to_message(row: Dict):
    # trả về dict chuẩn: {"role":..., "content":..., "image_url":..., "created_at":...}
    content = row.get("content") or ""
    role = row.get("role")
    image_url = row.get("image_url") or row.get("url") or None
    created_at = row.get("created_at") or row.get("createdAt") or None

    # Nếu chưa có content/role, thử lấy từ cột message (jsonb)
    m_field = row.get("message")
    if (not content or not role) and m_field:
        try:
            m_json = m_field if isinstance(m_field, dict) else json.loads(m_field)
        except Exception:
            m_json = {}
        if not content:
            content = m_json.get("content") or m_json.get("text") or content
        if not role:
            typ = (m_json.get("type") or m_json.get("role") or "").lower()
            if typ in ("human", "user"):
                role = "user"
            elif typ in ("ai", "assistant", "bot"):
                role = "assistant"

    # fallback
    if not role:
        role = "user" if "human" in (row.get("source") or "").lower() else "assistant" if "ai" in (row.get("source") or "").lower() else "user"

    return {"role": role, "content": content, "image_url": image_url, "created_at": created_at}

def load_messages_for_session(session_id: str) -> List[Dict]:
    # cố gắng query có order bằng created_at (desc=False)
    try:
        resp = supabase.table("n8n_chat_histories") \
            .select("*") \
            .eq("session_id", session_id) \
            .order("created_at", desc=False) \
            .execute()
    except TypeError as e:
        # nếu thư viện không chấp nhận desc param, thử without order
        st.warning("Warning: .order(..., desc=...) raised TypeError, retrying without order. Error: " + str(e))
        resp = supabase.table("n8n_chat_histories") \
            .select("*") \
            .eq("session_id", session_id) \
            .execute()
    except Exception as e:
        st.error("Lỗi khi gọi Supabase: " + str(e))
        return []

    # Debug helper: hiển thị resp nếu cần (bỏ comment khi đã ổn)
    # st.write("DEBUG - supabase response:", resp)

    # Kiểm tra lỗi từ supabase client
    # resp có thể có resp.error hoặc resp.status_code tuỳ version
    if getattr(resp, "error", None):
        st.error(f"Supabase returned error: {resp.error}")
        return []
    # resp.data là list hoặc None
    rows = resp.data or []

    messages = []
    for r in rows:
        try:
            msg = parse_row_to_message(r)
            if msg["content"]:   # chỉ thêm nếu có nội dung
                messages.append(msg)
        except Exception as e:
            # không để crash app nếu 1 row bị lỗi
            st.write("Lỗi khi parse row:", e, r)
            continue

    return messages
