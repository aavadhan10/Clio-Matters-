import streamlit as st
import requests

# --- CONFIGURATION ---
AIRIA_ENDPOINT = "https://app.airia.ai/api/agents/28330c27-c35a-4d5f-9797-e59382f5d140/invoke"
BEARER_TOKEN = "11148-UFTY4rycrtPlZnkYPUT3dRwyUEFPam57A7"  # Your latest token

# --- Streamlit App UI ---
st.set_page_config(page_title="Clio Agent Chat", layout="centered")
st.title("🤖 Clio Matter Status Agent")
st.write("Ask a question about your Clio matters (e.g., 'What matters are open today?')")

# Chat history
if "history" not in st.session_state:
    st.session_state.history = []

# Input box
user_input = st.text_input("Your question", placeholder="Type here and press enter...")

if user_input:
    # Show loading while processing
    with st.spinner("Getting response..."):
        try:
            headers = {
                "Authorization": f"Bearer {BEARER_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": user_input
            }

            res = requests.post(AIRIA_ENDPOINT, headers=headers, json=payload)
            res.raise_for_status()

            data = res.json()
            answer = data.get("output", "No response received.")

            # Store history
            st.session_state.history.append((user_input, answer))

        except Exception as e:
            st.error(f"Something went wrong: {e}")

# Display chat
for question, answer in reversed(st.session_state.history):
    st.markdown(f"**You:** {question}")
    st.markdown(f"**Clio Agent:** {answer}")
    st.markdown("---")
