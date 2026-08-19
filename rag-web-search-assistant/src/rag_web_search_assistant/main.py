import streamlit as st

# Step 1: Page Config
st.set_page_config(
    page_title="RAG Web Search Assistant",
    page_icon="🔍",
    layout="wide"
)

# Step 5: Basic Styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    h1 {
        color: #4A90D9;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🔍 RAG Web Search Assistant")

# Step 2 & 3: Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    llm_api_key = st.text_input("Gemini API Key", type="password")
    serper_api_key = st.text_input("Serper API Key (Optional)", type="password")
    
    init_button = st.button("Initialize APIs")
    
    st.divider()
    st.subheader("Status")
    st.info("Not initialized")

# Step 4: Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📄 Document Upload", "🌐 Web Content", "🎥 YouTube", "💬 Chat"])

with tab1:
    st.write("Document Upload - Coming Soon")

with tab2:
    st.write("Web Content - Coming Soon")

with tab3:
    st.write("YouTube - Coming Soon")

with tab4:
    st.write("Chat - Coming Soon")