import streamlit as st
import os
from google import genai
import requests

# Page Config
st.set_page_config(page_title="RAG Web Search Assistant", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .main { padding: 2rem; }
    h1 { color: #4A90D9; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 RAG Web Search Assistant")

# STEP: Session State Initialize Karna
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    llm_api_key = st.text_input("Gemini API Key", type="password")
    serper_api_key = st.text_input("Serper API Key (Optional)", type="password")
    
    init_button = st.button("Initialize APIs")
    
    st.divider()
    st.subheader("Status")
    status_placeholder = st.empty()  # Ye baad mein update hoga

    # STEP: Button Click Hone Par Kya Karna Hai
    if init_button:
        # Step 1: Key Capture (Session Mein Save)
        st.session_state.llm_api_key = llm_api_key
        st.session_state.serper_api_key = serper_api_key
        
        # Step 2: Gemini Key Validate Karna
        if not llm_api_key:
            st.error("Gemini API Key is mandatory!")
        else:
            try:
                test_client = genai.Client(api_key=llm_api_key)
                test_response = test_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents="Hi"
                )
                st.session_state.gemini_client = test_client
                gemini_valid = True
            except Exception as e:
                st.error(f"Gemini key invalid: {str(e)}")
                gemini_valid = False
                st.session_state.initialized = False   # ← Ye naya add kiya
            
            # Step 3: Serper Key Validate Karna (Agar Di Ho)
            serper_valid = True  # default True kyunke ye optional hai
            if serper_api_key:
                try:
                    test_serper = requests.post(
                        "https://google.serper.dev/search",
                        headers={"X-API-KEY": serper_api_key},
                        json={"q": "test"}
                    )
                    if test_serper.status_code != 200:
                        st.warning("Serper key invalid, web search is not working")
                        serper_valid = False
                except Exception as e:
                    st.warning(f"Serper key check fail: {str(e)}")
                    serper_valid = False
            
            # Step 5: Sab Sahi Hai To Initialized Mark Karo
            if gemini_valid:
                st.session_state.initialized = True
                st.success("APIs initialized successfully!")

    # Status Dikhana
    if st.session_state.initialized:
        status_placeholder.success("✅ Initialized")
    else:
        status_placeholder.info("Not initialized")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📄 Document Upload", "🌐 Web Content", "🎥 YouTube", "💬 Chat"])

with tab1:
    st.write("Document Upload - Coming Soon")

with tab2:
    st.write("Web Content - Coming Soon")

with tab3:
    st.write("YouTube - Coming Soon")

with tab4:
    st.write("Chat - Coming Soon")