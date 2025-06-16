import streamlit as st
import requests

# === CONFIGURATION ===
API_URL = "https://api.airia.ai/v2/PipelineExecution/28330c27-c35a-4d5f-9797-e59382f5d140"
API_KEY = "ak-MzQ0MDQ3Nzc4MnwxNzUwMTE1NTUxNzQ0fENhcmF2ZWwgTGF3LXwxfDI4NDEzNjAxMDQg"

# Optional: set user_id manually if known, otherwise fetch once from successful response
USER_ID = None  # or paste a known ID like "123e4567-e89b-12d3-a456-426614174000"

st.set_page_config(page_title="Clio Matters Overview", layout="centered")
st.title("🔍 Clio Matter Status Agent")

query = st.text_input("Ask about your matters (e.g., 'What matters are open today?')")

if st.button("Run Agent"):
    if not query:
        st.warning("Please enter a question.")
    else:
        headers = {
            "X-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "userInput": query,
            "asyncOutput": False
        }

        # Include userId if known
        if USER_ID:
            payload["userId"] = USER_ID

        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # On first run, extract and save userId if needed
            if not USER_ID and "userId" in data:
                USER_ID = data["userId"]
                st.success(f"Retrieved and cached user ID: `{USER_ID}`")

            st.subheader("🔎 Agent Response")
            st.markdown(data.get("output", "No output found."))

        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")

