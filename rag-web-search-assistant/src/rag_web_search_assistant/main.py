import streamlit as st
import os
import re
import chromadb
from google import genai
import requests
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from bs4 import BeautifulSoup

# ============ PAGE CONFIG ============
st.set_page_config(page_title="RAG Web Search Assistant", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .main { padding: 2rem; }
    h1 { color: #4A90D9; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 RAG Web Search Assistant")

# ============ SESSION STATE INITIALIZE ============
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = None
if "collection" not in st.session_state:
    chroma_client = chromadb.PersistentClient(path="./chroma_data")
    st.session_state.collection = chroma_client.get_or_create_collection("knowledge_base")

# ============ HELPER FUNCTIONS (PHASE 3) ============
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def process_and_store(text, source_name, collection):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)

    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=st.session_state.llm_api_key
    )

    for i, chunk in enumerate(chunks):
        embedding = embeddings_model.embed_query(chunk)
        collection.add(
            embeddings=[embedding],
            metadatas=[{"source": source_name, "chunk_index": i}],
            ids=[f"{source_name}_chunk_{i}"]
        )

    return len(chunks)

def fetch_webpage(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text

def extract_readable_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return text

# ============ SIDEBAR (PHASE 1 + 2) ============
with st.sidebar:
    st.header("⚙️ Configuration")

    llm_api_key = st.text_input("Gemini API Key", type="password")
    serper_api_key = st.text_input("Serper API Key (Optional)", type="password")

    init_button = st.button("Initialize APIs")

    st.divider()
    st.subheader("Status")
    status_placeholder = st.empty()

    if init_button:
        st.session_state.llm_api_key = llm_api_key
        st.session_state.serper_api_key = serper_api_key

        if not llm_api_key:
            st.error("Gemini API Key is mandatory!")
            st.session_state.initialized = False
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
                st.session_state.initialized = False

            serper_valid = True
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

            if gemini_valid:
                st.session_state.initialized = True
                st.success("APIs initialized successfully!")

    if st.session_state.initialized:
        status_placeholder.success("✅ Initialized")
    else:
        status_placeholder.info("Not initialized")

# ============ TABS ============
tab1, tab2, tab3, tab4 = st.tabs(["📄 Document Upload", "🌐 Web Content", "🎥 YouTube", "💬 Chat"])

# ---- TAB 1: DOCUMENT UPLOAD (PHASE 3) ----
with tab1:
    st.header("📄 Document Upload")

    if not st.session_state.initialized:
        st.warning("First, initialize the APIs from the sidebar.")
    else:
        uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

        if uploaded_files and st.button("Process PDFs"):
            progress_bar = st.progress(0)
            total_chunks = 0

            for idx, file in enumerate(uploaded_files):
                st.write(f"Processing: {file.name}")

                raw_text = extract_text_from_pdf(file)
                clean = clean_text(raw_text)
                chunk_count = process_and_store(clean, file.name, st.session_state.collection)

                total_chunks += chunk_count
                progress_bar.progress((idx + 1) / len(uploaded_files))

            st.success(f"✅ Done! {total_chunks} chunks created from {len(uploaded_files)} file(s)")

with tab2:
    st.header("🌐 Web Content")
    
    if not st.session_state.initialized:
        st.warning("First, initialize the APIs from the sidebar.")
    else:
        url_input = st.text_input("Website URL")
        
        if st.button("Process URL"):
            if not url_input:
                st.error("Enter the URL first")
            else:
                try:
                    with st.spinner("Fetching page..."):
                        html = fetch_webpage(url_input)
                        raw_text = extract_readable_text(html)
                        clean = clean_text(raw_text)
                        chunk_count = process_and_store(clean, url_input, st.session_state.collection)
                    
                    st.success(f"✅ Done! {chunk_count} chunks created from this URL")
                
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not fetch the URL: {str(e)}")
                except Exception as e:
                    st.error(f"There was an issue:{str(e)}")

with tab3:
    st.write("YouTube - Coming Soon")

with tab4:
    st.write("Chat - Coming Soon")