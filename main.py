import streamlit as st
import requests
from datetime import datetime
import json

# === CONFIGURATION ===
def get_secrets():
    """Get secrets with proper error handling"""
    try:
        clio_client_id = st.secrets["clio"]["client_id"]
        clio_client_secret = st.secrets["clio"]["client_secret"]
        clio_refresh_token = st.secrets["clio"]["refresh_token"]
        claude_api_key = st.secrets["claude"]["api_key"]
        airia_api_key = st.secrets["airia"]["api_key"]
        airia_user_id = st.secrets["airia"]["user_id"]
        return clio_client_id, clio_client_secret, clio_refresh_token, claude_api_key, airia_api_key, airia_user_id
    except KeyError as e:
        st.error(f"Missing secret: {e}")
        return None, None, None, None, None, None

# Airia Configuration
AIRIA_API_URL = "https://api.airia.ai/v2/PipelineExecution/28330c27-c35a-4d5f-9797-e59382f5d140"

# Clio Configuration
CLIO_TOKEN_URL = "https://app.clio.com/oauth/token"
CLIO_MATTERS_URL = "https://app.clio.com/api/v4/matters"

# === CLIO FUNCTIONS ===
@st.cache_data(ttl=3600)
def refresh_clio_access_token(client_id, client_secret, refresh_token):
    """Refresh Clio access token"""
    try:
        response = requests.post(
            CLIO_TOKEN_URL,
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
        st.error(f"Failed to refresh Clio access token: {e}")
        return None

def fetch_clio_matters(access_token, per_page=100):
    """Fetch matters from Clio API"""
    try:
        response = requests.get(
            f"{CLIO_MATTERS_URL}?per_page={per_page}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch Clio matters: {e}")
        return []

# === AIRIA FUNCTIONS ===
def call_airia_agent(user_input, airia_api_key, airia_user_id, clio_data=None):
    """Call the Airia Clio Agent"""
    try:
        # Prepare the data for Airia
        prompt = user_input
        if clio_data:
            # Include Clio matter data as context
            context_lines = []
            for matter in clio_data:
                name = matter.get("display_number", "N/A")
                status = matter.get("status", "unknown")
                client = matter.get("client", {}).get("name", "No client") if matter.get("client") else "No client"
                attorney = matter.get("responsible_attorney", {}).get("name", "Unassigned") if matter.get("responsible_attorney") else "Unassigned"
                opened = matter.get("open_date", "Unknown")
                context_lines.append(f"{name} — {status} — {client} — {attorney} — opened on {opened}")
            
            clio_context = "\n".join(context_lines)
            prompt = f"User Question: {user_input}\n\nClio Matter Data:\n{clio_context}"
        
        # Call Airia API
        response = requests.post(
            AIRIA_API_URL,
            headers={
                "X-API-KEY": airia_api_key,
                "Content-Type": "application/json"
            },
            json={
                "userID": airia_user_id,
                "userInput": prompt,
                "asyncOutput": False
            }
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to call Airia agent: {e}")
        return None

# === STREAMLIT UI ===
st.set_page_config(page_title="Clio + Airia Legal Assistant", layout="wide")
st.title("⚖️ Clio + Airia Legal Assistant")

# Get secrets
clio_client_id, clio_client_secret, clio_refresh_token, claude_api_key, airia_api_key, airia_user_id = get_secrets()

# Check if we have all required secrets
if not all([clio_client_id, clio_client_secret, clio_refresh_token, airia_api_key, airia_user_id]):
    st.error("Missing required secrets. Please configure:")
    st.code("""
[clio]
client_id = "your_clio_client_id"
client_secret = "your_clio_client_secret"
refresh_token = "your_clio_refresh_token"

[claude]
api_key = "your_claude_api_key"

[airia]
api_key = "your_airia_api_key"
user_id = "your_airia_user_id"
    """)
    st.stop()

# Sidebar for options
with st.sidebar:
    st.header("🔧 Options")
    include_clio_data = st.checkbox("Include Clio matter data", value=True)
    show_raw_response = st.checkbox("Show raw Airia response", value=False)

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📋 Clio Matters")
    
    # Try to get Clio data
    clio_matters = []
    if include_clio_data:
        access_token = refresh_clio_access_token(clio_client_id, clio_client_secret, clio_refresh_token)
        if access_token:
            clio_matters = fetch_clio_matters(access_token)
            if clio_matters:
                st.success(f"✅ Connected to Clio! Found {len(clio_matters)} matters.")
                
                # Show matter summary
                with st.expander(f"📁 View {len(clio_matters)} Matters"):
                    for i, matter in enumerate(clio_matters[:10]):  # Show first 10
                        st.write(f"**{matter.get('display_number', 'N/A')}** - {matter.get('status', 'Unknown')} - {matter.get('client', {}).get('name', 'No client')}")
            else:
                st.warning("No matters found in Clio")
        else:
            st.error("Failed to connect to Clio")
            include_clio_data = False
    else:
        st.info("Clio integration disabled")

with col2:
    st.header("🤖 Airia Agent")
    
    # User input
    user_question = st.text_area(
        "Ask your legal assistant:",
        placeholder="e.g., What matters need urgent attention? Which clients have overdue tasks?",
        height=100
    )
    
    # Submit button
    if st.button("🚀 Ask Airia", type="primary"):
        if user_question:
            with st.spinner("Consulting Airia agent..."):
                # Call Airia with or without Clio data
                airia_response = call_airia_agent(
                    user_question, 
                    airia_api_key, 
                    airia_user_id,
                    clio_matters if include_clio_data else None
                )
                
                if airia_response:
                    st.success("✅ Response from Airia:")
                    
                    # Display the response
                    if "output" in airia_response:
                        st.markdown(airia_response["output"])
                    elif "result" in airia_response:
                        st.markdown(airia_response["result"])
                    else:
                        st.write(airia_response)
                    
                    # Show raw response if requested
                    if show_raw_response:
                        with st.expander("🔍 Raw Airia Response"):
                            st.json(airia_response)
                else:
                    st.error("Failed to get response from Airia")
        else:
            st.warning("Please enter a question")

# Footer with instructions
st.markdown("---")
with st.expander("ℹ️ How to use this app"):
    st.markdown("""
    **This app combines Clio legal matter data with Airia AI for intelligent legal assistance.**
    
    **Features:**
    - 📊 Fetches your live Clio matter data
    - 🤖 Sends questions to your custom Airia agent
    - 🔄 Provides context-aware responses using both systems
    
    **Example questions:**
    - "What matters are overdue and need immediate attention?"
    - "Which clients have the most active cases?"
    - "Summarize the status of all personal injury cases"
    - "What tasks should I prioritize today?"
    """)

st.markdown("*Powered by Clio API + Airia AI*")
