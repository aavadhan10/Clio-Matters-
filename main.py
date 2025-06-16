
import streamlit as st
import requests
from datetime import datetime
import openai

# === CONFIGURATION ===
CLIO_CLIENT_ID = st.secrets["clio"]["client_id"]
CLIO_CLIENT_SECRET = st.secrets["clio"]["client_secret"]
CLIO_REFRESH_TOKEN = st.secrets["clio"]["refresh_token"]
OPENAI_API_KEY = st.secrets["openai"]["api_key"]

TOKEN_URL = "https://app.clio.com/oauth/token"
MATTERS_URL = "https://app.clio.com/api/v4/matters"

# === GET ACCESS TOKEN ===
@st.cache_data(ttl=3600)
def refresh_access_token():
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": CLIO_REFRESH_TOKEN,
            "client_id": CLIO_CLIENT_ID,
            "client_secret": CLIO_CLIENT_SECRET
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json().get("access_token")

# === FETCH CLIO MATTERS ===
def fetch_matters(access_token, per_page=100):
    response = requests.get(
        f"{MATTERS_URL}?per_page={per_page}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response.json().get("data", [])

# === SUMMARIZE WITH OPENAI ===
def summarize_matters_with_llm(matters, prompt):
    openai.api_key = OPENAI_API_KEY
    if not matters:
        return "No matter data available to summarize."

    context_lines = []
    for m in matters:
        name = m.get("display_number", "N/A")
        status = m.get("status", "unknown")
        client = m.get("client", {}).get("name", "No client")
        attorney = m.get("responsible_attorney", {}).get("name", "Unassigned")
        opened = m.get("open_date", "Unknown")
        context_lines.append(f"{name} — {status} — {client} — {attorney} — opened on {opened}")

    context = "\n".join(context_lines)

    messages = [
        {"role": "system", "content": "You are a helpful legal assistant summarizing Clio matter data."},
        {"role": "user", "content": f"Prompt: {prompt}\n\nData:\n{context}"}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message.content.strip()

# === STREAMLIT UI ===
st.set_page_config(page_title="Clio Agent (Prompt + Summary)", layout="centered")
st.title("🤖 Clio Matter Assistant")

access_token = refresh_access_token()
matters = fetch_matters(access_token)

st.subheader("📝 Ask your Clio Agent:")
prompt = st.text_input("Enter a natural language question:", placeholder="e.g. What matters are open and who is working on them?")

if st.button("Submit"):
    if not prompt:
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Thinking..."):
            summary = summarize_matters_with_llm(matters, prompt)
            st.markdown("### 🧠 Summary:")
            st.markdown(summary)

