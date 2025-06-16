import streamlit as st
import requests
from datetime import datetime
import anthropic

# === CONFIGURATION ===
CLIO_CLIENT_ID = st.secrets["clio"]["client_id"]
CLIO_CLIENT_SECRET = st.secrets["clio"]["client_secret"]
CLIO_REFRESH_TOKEN = st.secrets["clio"]["refresh_token"]
CLAUDE_API_KEY = st.secrets["claude"]["api_key"]

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

# === SUMMARIZE WITH CLAUDE ===
def summarize_matters_with_claude(matters, prompt):
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

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=800,
        temperature=0.7,
        system="You are a helpful legal assistant summarizing Clio matter data.",
        messages=[
            {"role": "user", "content": f"Prompt: {prompt}\n\nMatter data:\n{context}"}
        ]
    )
    return message.content[0].text.strip()

# === STREAMLIT UI ===
st.set_page_config(page_title="Clio + Claude Matter Assistant", layout="centered")
st.title("🤖 Clio Matter Agent (Claude-powered)")

access_token = refresh_access_token()
matters = fetch_matters(access_token)

st.subheader("📝 Ask your Clio Agent:")
prompt = st.text_input("Enter a natural language question:", placeholder="e.g. What matters are open and who is working on them?")

if st.button("Submit"):
    if not prompt:
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Thinking with Claude..."):
            summary = summarize_matters_with_claude(matters, prompt)
            st.markdown("### 🧠 Summary:")
            st.markdown(summary)
