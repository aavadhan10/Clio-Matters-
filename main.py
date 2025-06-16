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
        # Call Airia API - the agent handles Clio integration internally
        response = requests.post(
            AIRIA_API_URL,
            headers={
                "X-API-KEY": airia_api_key,
                "Content-Type": "application/json"
            },
            json={
                "userInput": user_input,
                "asyncOutput": False
            }
        )
        
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
    placeholder="""Examples:
• What matters need urgent attention?
• Which clients have overdue tasks?
• Summarize all active personal injury cases
• What should I prioritize today?
• Show me matters opened this month
• Which attorneys are handling the most cases?""",
    height=120
)

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
                if "output" in airia_response:
                    st.markdown(airia_response["output"])
                elif "result" in airia_response:
                    st.markdown(airia_response["result"])
                elif isinstance(airia_response, str):
                    st.markdown(airia_response)
                else:
                    st.write(airia_response)
                
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
