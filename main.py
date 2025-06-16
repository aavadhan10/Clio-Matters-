import streamlit as st
import requests
from datetime import datetime
import anthropic

# === CONFIGURATION WITH ERROR HANDLING ===
def get_secrets():
    """Get secrets with proper error handling"""
    try:
        clio_client_id = st.secrets["clio"]["client_id"]
        clio_client_secret = st.secrets["clio"]["client_secret"]
        clio_refresh_token = st.secrets["clio"]["refresh_token"]
        claude_api_key = st.secrets["claude"]["api_key"]
        return clio_client_id, clio_client_secret, clio_refresh_token, claude_api_key
    except KeyError as e:
        st.error(f"Missing secret: {e}")
        st.info("Please configure your secrets in Streamlit. See the setup instructions below.")
        return None, None, None, None

TOKEN_URL = "https://app.clio.com/oauth/token"
MATTERS_URL = "https://app.clio.com/api/v4/matters"

# === GET ACCESS TOKEN ===
@st.cache_data(ttl=3600)
def refresh_access_token(client_id, client_secret, refresh_token):
    """Refresh Clio access token"""
    try:
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to refresh access token: {e}")
        return None

# === FETCH CLIO MATTERS ===
def fetch_matters(access_token, per_page=100):
    """Fetch matters from Clio API"""
    try:
        response = requests.get(
            f"{MATTERS_URL}?per_page={per_page}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Debug: Show response status
        st.info(f"Clio API Response Status: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()
        
        # Debug: Show raw response structure
        st.info(f"Response keys: {list(data.keys())}")
        matters = data.get("data", [])
        
        # Debug: Show matter count and sample
        st.info(f"Found {len(matters)} matters")
        if matters:
            st.info(f"Sample matter keys: {list(matters[0].keys())}")
        
        return matters
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch matters: {e}")
        return []

# === SUMMARIZE WITH CLAUDE ===
def summarize_matters_with_claude(matters, prompt, claude_api_key):
    """Summarize matters using Claude API"""
    if not matters:
        return "No matter data available to summarize."
    
    # Prepare context
    context_lines = []
    for m in matters:
        name = m.get("display_number", "N/A")
        status = m.get("status", "unknown")
        client = m.get("client", {}).get("name", "No client") if m.get("client") else "No client"
        attorney = m.get("responsible_attorney", {}).get("name", "Unassigned") if m.get("responsible_attorney") else "Unassigned"
        opened = m.get("open_date", "Unknown")
        context_lines.append(f"{name} — {status} — {client} — {attorney} — opened on {opened}")
    
    context = "\n".join(context_lines)
    
    try:
        client = anthropic.Anthropic(api_key=claude_api_key)
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
    except Exception as e:
        st.error(f"Failed to get Claude response: {e}")
        return "Error generating summary with Claude."

# === STREAMLIT UI ===
st.set_page_config(page_title="Clio + Claude Matter Assistant", layout="centered")
st.title("🤖 Clio Matter Agent (Claude-powered)")

# Get secrets
clio_client_id, clio_client_secret, clio_refresh_token, claude_api_key = get_secrets()

# Only proceed if we have all secrets
if all([clio_client_id, clio_client_secret, clio_refresh_token, claude_api_key]):
    # Get access token
    access_token = refresh_access_token(clio_client_id, clio_client_secret, clio_refresh_token)
    
    if access_token:
        # Fetch matters
        matters = fetch_matters(access_token)
        
        if matters:
            st.success(f"✅ Connected to Clio! Found {len(matters)} matters.")
            
            # Add expandable section to show matter details
            with st.expander("🔍 View Matter Details"):
                for i, matter in enumerate(matters[:5]):  # Show first 5 matters
                    st.write(f"**Matter {i+1}:**")
                    st.json(matter)
            
            st.subheader("📝 Ask your Clio Agent:")
            prompt = st.text_input(
                "Enter a natural language question:", 
                placeholder="e.g. What matters are open and who is working on them?"
            )
            
            if st.button("Submit"):
                if not prompt:
                    st.warning("Please enter a prompt.")
                else:
                    with st.spinner("Thinking with Claude..."):
                        summary = summarize_matters_with_claude(matters, prompt, claude_api_key)
                        st.markdown("### 🧠 Summary:")
                        st.markdown(summary)
        else:
            st.warning("⚠️ No matters found. This could mean:")
            st.write("- Your Clio account has no matters")
            st.write("- The API permissions don't include matter access")
            st.write("- The refresh token needs to be regenerated")
            st.write("- Check the debug info above for API response details")
    else:
        st.error("Failed to get access token. Check your Clio credentials.")
else:
    st.markdown("""
    ## 🔧 Setup Instructions
    
    To use this app, you need to configure secrets in Streamlit:
    
    ### 1. Create a `.streamlit/secrets.toml` file (local development):
    ```toml
    [clio]
    client_id = "your_clio_client_id"
    client_secret = "your_clio_client_secret"
    refresh_token = "your_clio_refresh_token"
    
    [claude]
    api_key = "your_claude_api_key"
    ```
    
    ### 2. For Streamlit Cloud deployment:
    - Go to your app settings
    - Navigate to "Secrets"
    - Add the same TOML format secrets
    
    ### 3. Getting Clio API credentials:
    - Log into your Clio account
    - Go to Settings > API Credentials
    - Create a new application
    - Use the authorization flow to get your refresh token
    
    ### 4. Getting Claude API key:
    - Visit https://console.anthropic.com
    - Create an account and get your API key
    """)

# Optional: Add a debug section
if st.checkbox("Debug: Show available secrets"):
    st.write("Available secret keys:", list(st.secrets.keys()) if hasattr(st, 'secrets') else "No secrets available")
