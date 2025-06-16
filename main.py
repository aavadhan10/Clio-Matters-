import streamlit as st
import requests
import json

# === CONFIGURATION ===
def get_airia_secrets():
    """Get Airia secrets"""
    try:
        airia_api_key = st.secrets["airia"]["api_key"]
        return airia_api_key
    except KeyError as e:
        st.error(f"Missing Airia secret: {e}")
        return None

# Airia Configuration
AIRIA_API_URL = "https://api.airia.ai/v2/PipelineExecution/28330c27-c35a-4d5f-9797-e59382f5d140"

# === AIRIA FUNCTIONS ===
def call_airia_agent(user_input, airia_api_key):
    """Call the Airia Clio Agent"""
    try:
        # Extract user ID from the API key if possible
        # Your API key format: ak-MzQ0MDQ3Nzc4MnwxNzUwMTE1NTUxNzQ0fENhcmF2ZWwgTGF3LXwxfDI4NDEzNjAxMDQg
        # Try to extract user ID from the key
        user_id = "default_user"  # Fallback
        try:
            import base64
            # Decode the API key to extract user info
            key_parts = airia_api_key.split('-', 2)
            if len(key_parts) > 2:
                encoded_part = key_parts[2]
                # Try to decode and extract user ID
                decoded = base64.b64decode(encoded_part + '==').decode('utf-8', errors='ignore')
                if '|' in decoded:
                    parts = decoded.split('|')
                    if len(parts) > 0:
                        user_id = parts[0]  # First part might be user ID
        except:
            user_id = "default_user"
        
        # Call Airia API
        response = requests.post(
            AIRIA_API_URL,
            headers={
                "X-API-KEY": airia_api_key,
                "Content-Type": "application/json"
            },
            json={
                "userID": user_id,
                "userInput": user_input,
                "asyncOutput": False
            }
        )
        
        st.info(f"Request sent with userID: {user_id}")
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to call Airia agent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"Response text: {e.response.text}")
        return None

# === STREAMLIT UI ===
st.set_page_config(page_title="Clio Legal Assistant (Airia-Powered)", layout="centered")

# Header
st.title("⚖️ Clio Legal Assistant")
st.markdown("*Powered by Airia AI with direct Clio integration*")

# Get Airia API key
airia_api_key = get_airia_secrets()

if not airia_api_key:
    st.error("Missing Airia API key. Please configure:")
    st.code("""
[airia]
api_key = "your_airia_api_key"
    """)
    st.stop()

# Main interface
st.header("🤖 Legal Assistant")
st.markdown("Ask questions about your Clio matters, clients, tasks, and more. The AI agent has direct access to your Clio data.")

# User input
user_question = st.text_area(
    "Ask your legal assistant:",
    placeholder="""Try these diagnostic questions:
• Hello, can you hear me?
• What is your purpose?
• Do you have access to Clio?
• Tell me about yourself
• What can you help me with?""",
    height=120
)

# Quick test buttons
st.markdown("**Quick Tests:**")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Test: Hello"):
        user_question = "Hello, what can you help me with?"
with col2:
    if st.button("Test: Clio Access"):
        user_question = "Do you have access to Clio data?"
with col3:
    if st.button("Test: Purpose"):
        user_question = "What is your purpose and what can you do?"

# Submit button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ask_button = st.button("🚀 Ask Assistant", type="primary", use_container_width=True)

if ask_button:
    if user_question:
        with st.spinner("Consulting your legal assistant..."):
            # Call Airia agent
            airia_response = call_airia_agent(user_question, airia_api_key)
            
            if airia_response:
                st.success("✅ Response:")
                
                # Display the response
                if "result" in airia_response and airia_response["result"]:
                    result = airia_response["result"]
                    if result and result.lower() != user_question.lower():  # Don't show if it's just echoing
                        st.markdown(result)
                    else:
                        st.warning("⚠️ The agent returned an echo response. This might indicate:")
                        st.write("• The Airia agent needs more configuration")
                        st.write("• The agent doesn't have proper Clio connection")
                        st.write("• Try asking a more specific legal question")
                elif "output" in airia_response and airia_response["output"]:
                    st.markdown(airia_response["output"])
                else:
                    st.warning("⚠️ Received empty or unclear response from agent")
                    st.write("Raw response:", airia_response)
                
                # Optional: Show raw response
                with st.expander("🔍 View Raw Response"):
                    st.json(airia_response)
            else:
                st.error("Failed to get response from assistant")
    else:
        st.warning("Please enter a question")

# Example queries section
with st.expander("💡 Example Questions You Can Ask"):
    st.markdown("""
    **Matter Management:**
    - "What matters are overdue and need immediate attention?"
    - "Show me all active litigation cases"
    - "Which matters were opened this week?"
    
    **Client Insights:**
    - "Which clients have the most active cases?"
    - "Show me clients with overdue invoices"
    - "What's the status of [Client Name]'s matters?"
    
    **Task & Calendar Management:**
    - "What tasks are due today?"
    - "What should I prioritize this week?"
    - "Show me upcoming court dates"
    
    **Reporting & Analytics:**
    - "Summarize this month's new matters"
    - "Which practice areas are most active?"
    - "Show me attorney workload distribution"
    
    **Specific Actions:**
    - "Create a new matter for [Client Name]"
    - "Update the status of matter [Matter Number]"
    - "Schedule a follow-up task for [Matter]"
    """)

# Info section
st.markdown("---")
st.info("💡 This assistant has direct access to your Clio data and can help with queries, updates, and insights about your legal practice.")

# Footer
st.markdown("*Built with Streamlit + Airia AI*")
