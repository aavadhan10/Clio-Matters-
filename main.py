import streamlit as st
import requests
import json

# Page config
st.set_page_config(
    page_title="Clio Agent Interface",
    page_icon="🤖",
    layout="centered"
)

# Title and description
st.title("🤖 Clio Agent")
st.write("Use this interface to interact with the Clio Agent from Airia.")

# Agent info
with st.expander("Agent Information"):
    st.code("Agent GUID: 28330c27-c35a-4d5f-9797-e59382f5d140")
    st.code("API Endpoint: https://api.airia.ai/v2/PipelineExecution/28330c27-c35a-4d5f-9797-e59382f5d140")

# Input fields
st.subheader("Configuration")

# API Key input
api_key = st.text_input(
    "Airia API Key",
    type="password",
    help="Enter your AIRIA_API_KEY"
)

# User ID input
user_id = st.text_input(
    "User ID",
    value="aavadhani@briedlylegal.com",
    help="Your Airia user ID (this should be your email)"
)

# User input
st.subheader("Ask Clio")
user_input = st.text_area(
    "Your Question/Input",
    placeholder="Enter your question or input for the Clio Agent...",
    height=120
)

# Submit button
if st.button("Send to Clio Agent", type="primary"):
    if not api_key:
        st.error("Please enter your Airia API Key")
    elif not user_id:
        st.error("Please enter your User ID")
    elif not user_input:
        st.error("Please enter your question/input")
    else:
        # Show loading spinner
        with st.spinner("Processing your request..."):
            try:
                # Prepare the API call
                url = "https://api.airia.ai/v2/PipelineExecution/28330c27-c35a-4d5f-9797-e59382f5d140"
                
                payload = {
                    "userID": user_id,  # Note: capital ID
                    "userInput": user_input,
                    "asyncOutput": False
                }
                
                headers = {
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json"
                }
                
                # Make the API call
                st.write("**Debug Info:**")
                st.write(f"User ID being sent: `{user_id}`")
                st.write(f"Payload: `{payload}`")
                
                response = requests.post(url, headers=headers, json=payload)
                
                # Display results
                if response.status_code == 200:
                    st.success("Agent Response:")
                    st.write(response.text)
                else:
                    st.error(f"Error (Status {response.status_code}):")
                    st.write(response.text)
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Request Error: {str(e)}")
            except Exception as e:
                st.error(f"Unexpected Error: {str(e)}")

# Sidebar with instructions
with st.sidebar:
    st.header("How to Use")
    st.write("""
    1. **Enter your Airia API Key** - This authenticates your requests
    2. **Verify your User ID** - Should be your email address
    3. **Ask your question** - Type what you want to ask Clio
    4. **Click Send** - The agent will process your request
    """)
    
    st.header("Tips")
    st.write("""
    - Your API key is stored securely during this session
    - The User ID is pre-filled with your email
    - Try asking specific questions for better responses
    """)
    
    st.header("About Clio Agent")
    st.write("""
    This agent is hosted on Airia and can help with various tasks. 
    The specific capabilities depend on how the agent was configured.
    """)

# Footer
st.markdown("---")
st.markdown("*Powered by Airia API*")
