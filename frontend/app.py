# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt
import json
import os

# ---- Config ----
API_URL = "http://127.0.0.1:8000/analyze"
st.set_page_config(page_title="PriorityAI - Customer Service Routing", page_icon="💬")

# ---- Mock User Data ----
mock_users = {
    "user_001": {"name": "Alex Johnson", "account_balance": "$2,350.21", "card_status": "Active"},
    "user_002": {"name": "Jamie Patel", "account_balance": "$542.87", "card_status": "Frozen"},
    "user_003": {"name": "Riley Chen", "account_balance": "$7,129.42", "card_status": "Active"},
}

# ---- Session State ----
if "user_chats" not in st.session_state:
    st.session_state.user_chats = {uid: [] for uid in mock_users.keys()}
if "current_user" not in st.session_state:
    st.session_state.current_user = list(mock_users.keys())[0]

# ---- Helper Functions ----
def save_chats():
    os.makedirs("local_chats", exist_ok=True)
    for uid, chats in st.session_state.user_chats.items():
        with open(f"local_chats/{uid}.json", "w") as f:
            json.dump(chats, f, indent=2)

def load_chats():
    if os.path.exists("local_chats"):
        for fname in os.listdir("local_chats"):
            uid = fname.replace(".json", "")
            try:
                with open(f"local_chats/{fname}") as f:
                    st.session_state.user_chats[uid] = json.load(f)
            except Exception:
                pass

load_chats()

# ---- Sidebar ----
st.sidebar.header("👤 Select Active User")
user_id = st.sidebar.selectbox(
    "Choose a user:",
    options=list(mock_users.keys()),
    format_func=lambda uid: f"{mock_users[uid]['name']} ({uid})",
)
st.session_state.current_user = user_id

if st.sidebar.button("💾 Save Chats"):
    save_chats()
    st.sidebar.success("Chats saved locally!")

# ---- Main UI ----
user = mock_users[user_id]
st.title("💬 PriorityAI - Smart Customer Support")
st.caption(f"Logged in as **{user['name']}** | Balance: {user['account_balance']} | Card: {user['card_status']}")

user_message = st.text_input("Enter your message:")
if st.button("Send"):
    if user_message.strip():
        payload = {"user_id": user_id, "message": user_message}
        try:
            res = requests.post(API_URL, json=payload)
            data = res.json()
            st.session_state.user_chats[user_id].append(
                {
                    "user": user_message,
                    "priority": data["priority"],
                    "response": data["response"],
                    "confidence": data["confidence"],
                }
            )
        except Exception as e:
            st.error(f"Error contacting backend: {e}")
    else:
        st.warning("Please enter a message.")

# ---- Display Chat ----
st.divider()
st.subheader(f"Conversation with {user['name']}")

chat_history = st.session_state.user_chats[user_id]
if chat_history:
    for msg in reversed(chat_history):
        st.markdown(f"**You:** {msg['user']}")
        st.markdown(f"**Priority:** {msg['priority']} ({msg['confidence']*100:.0f}% confidence)")
        st.markdown(f"**Assistant:** {msg['response']}")
        st.markdown("---")
else:
    st.info("No messages yet for this user.")

# ---- Dashboard ----
st.divider()
st.subheader("📈 Message Priority Overview")

if chat_history:
    df = pd.DataFrame(st.session_state.user_chats[user_id])
    counts = df["priority"].value_counts().reset_index()
    counts.columns = ["Priority", "Count"]
    chart = (
        alt.Chart(counts)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Priority", sort=["HIGH", "MEDIUM", "LOW"]),
            y="Count",
            color="Priority"
        )
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.write("No messages analyzed yet.")
