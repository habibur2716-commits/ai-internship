import streamlit as st
import time
import os
import re
import chromadb
from google import genai
import requests
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

# ============ PAGE CONFIG ============
st.set_page_config(page_title="RAG Web Search Assistant", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .main { padding: 2rem; }
    h1 { color: #4A90D9; }
    
    /* Title sticky top */
    .stAppViewContainer .main .block-container {
        padding-top: 1rem !important;
    }
    
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:first-child {
        position: sticky;
        top: 0;
        background-color: #0e1117;
        z-index: 997;
        padding-bottom: 0.5rem;
    }
    
    /* Tabs sticky top */
    [data-testid="stTabs"] {
        position: sticky;
        top: 0;
        background-color: #0e1117;
        z-index: 998;
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
    
    /* Chat input fixed bottom */
    .stChatInput {
        position: fixed;
        bottom: 0;
        right: 0;
        left: 0;
        padding: 1rem 2rem;
        background-color: #0e1117;
        z-index: 999;
        border-top: 1px solid #2d2d2d;
        transition: left 0.3s ease;
    }
    
    /* Sidebar khula ho to left shift */
    [data-testid="stSidebar"][aria-expanded="true"] ~ .main .stChatInput,
    [data-testid="stSidebar"][aria-expanded="true"] ~ * .stChatInput {
        left: 300px;
    }
    
    /* Chat messages ke liye padding */
    [data-testid="stChatMessageContainer"] {
        padding-bottom: 100px;
    }
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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ============ HELPER FUNCTIONS (PHASE 3) ============
def extract_text_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        
        if len(reader.pages) == 0:
            raise ValueError("There are no pages in the PDF.")
        
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF — it is likely a scanned or image-based PDF.")
        
        return text
    
    except Exception as e:
        raise Exception(f"PDF processing error: {str(e)}")

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
            documents=[chunk],
            metadatas=[{"source": source_name, "chunk_index": i}],
            ids=[f"{source_name}_chunk_{i}"]
        )
        time.sleep(0.7)  # ← Ye line add ki, har request ke beech thoda wait

    return len(chunks)

def fetch_webpage(url):
    if not url.startswith(("http://", "https://")):
        raise ValueError("Not a valid URL — must start with 'http://'")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        raise Exception("The website did not respond within 10 seconds — Timeout.")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not access the website — check your internet connection or the URL is incorrect.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"The website granted access: {str(e)}")

def extract_readable_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return text

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_youtube_transcript(video_id):
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.fetch(video_id)
        
        if not transcript_list:
            raise ValueError("The transcript is empty.")
        
        full_text = " ".join([entry.text for entry in transcript_list])
        return full_text
    
    except Exception as e:
        error_msg = str(e).lower()
        if "no transcript" in error_msg or "could not retrieve" in error_msg:
            raise Exception("Is video ka transcript available nahi hai — ya to private hai, ya transcript disabled hai")
        elif "video unavailable" in error_msg:
            raise Exception("Ye video available nahi hai — deleted ya private ho sakta hai")
        else:
            raise Exception(f"Transcript fetch error: {str(e)}")

def retrieve_relevant_chunks(query, collection, n_results=4):
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=st.session_state.llm_api_key
    )
    query_embedding = embeddings_model.embed_query(query)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results

#=====phase 7
def search_web(query, serper_key, num_results=3):
    headers = {
        "X-API-KEY": serper_key,
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    
    response = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    
    results = []
    if "organic" in data:
        for item in data["organic"][:num_results]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            results.append({"title": title, "snippet": snippet, "link": link})
    
    return results

def format_web_results(results):
    if not results:
        return ""
    
    formatted = ""
    for r in results:
        formatted += f"Title: {r['title']}\nSnippet: {r['snippet']}\nSource: {r['link']}\n\n"
    
    return formatted



# ============ SIDEBAR (PHASE 1 + 2) ============
with st.sidebar:
    st.header("⚙️ Configuration")

    llm_api_key = st.text_input("Gemini API Key", type="password")
    serper_api_key = st.text_input("Serper API Key (Optional)", type="password")

    init_button = st.button("Initialize APIs")

    st.divider()
    st.subheader("Status")
    status_placeholder = st.empty()

    st.divider()
    if st.session_state.initialized:
        st.session_state.web_search_enabled = st.checkbox(
            "🌐 Enable web search",
            value=bool(st.session_state.get("serper_api_key")),
            key="web_search_checkbox"
        )

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
                    model="models/gemini-3.5-flash-lite",
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
    
            # Size check — 10MB se bara file warn karo
            for file in uploaded_files:
                if file.size > 10 * 1024 * 1024:  # 10MB
                    st.warning(f"⚠️ '{file.name}' bohot bara hai ({file.size // (1024*1024)}MB) — processing slow ho sakti hai")
    
            progress_bar = st.progress(0)
            total_chunks = 0
            errors = []
    
            for idx, file in enumerate(uploaded_files):
                try:
                    st.write(f"Processing: {file.name}...")
                    raw_text = extract_text_from_pdf(file)
                    clean = clean_text(raw_text)
            
                    if len(clean) < 50:
                       st.warning(f"'{file.name}' mein bohot kam text hai — skip kar raha hoon")
                       continue
            
                    chunk_count = process_and_store(clean, file.name, st.session_state.collection)
                    total_chunks += chunk_count
                except Exception as e:
                    errors.append(f"{file.name}: {str(e)}")
           
                progress_bar.progress((idx + 1) / len(uploaded_files))
    
            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
    
            if total_chunks > 0:
                st.success(f"✅ Done! {total_chunks} chunks created from {len(uploaded_files) - len(errors)} file(s)")

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
    st.header("🎥 YouTube")
    
    if not st.session_state.initialized:
        st.warning("First, initialize the APIs from the sidebar.")
    else:
        yt_url = st.text_input("YouTube Video URL")
        
        if st.button("Process Video"):
            if not yt_url:
                st.error("Enter the URL first.")
            else:
                try:
                    with st.spinner("Fetching transcript..."):
                        video_id = extract_video_id(yt_url)
                        
                        if not video_id:
                            st.error("Not a valid YouTube URL.")
                        else:
                            transcript_text = fetch_youtube_transcript(video_id)
                            clean = clean_text(transcript_text)
                            chunk_count = process_and_store(clean, yt_url, st.session_state.collection)
                            
                            st.success(f"✅ Done! {chunk_count} chunks created from this video")
                
                except Exception as e:
                    st.error(f"Transcript could not be found: {str(e)}")

with tab4:
    st.header("💬 Chat")
    
    if not st.session_state.initialized:
        st.warning("First, initialize the APIs from the sidebar.")
    else:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Purani conversation dikhana
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Naya message input
        user_question = st.chat_input("Ask your question...")
        
        if user_question:
            with st.chat_message("user"):
                st.write(user_question)
            st.session_state.chat_history.append({"role": "user", "content": user_question})
    
            with st.chat_message("assistant"):
                with st.spinner("I am thinking..."):
                    try:
                        enable_web_search = st.session_state.get("web_search_enabled", False)
                        count = st.session_state.collection.count()
                
                        # Document context nikalna
                        doc_context = ""
                        sources = []
                        if count > 0:
                            results = retrieve_relevant_chunks(user_question, st.session_state.collection)
                            retrieved_texts = results["documents"][0]
                            retrieved_metadatas = results["metadatas"][0]
                            doc_context = "\n\n".join(retrieved_texts)
                            sources = list(set([meta["source"] for meta in retrieved_metadatas]))
                
                        # Web search context nikalna (agar enabled hai)
                        web_context = ""
                        web_links = []
                        
                        if enable_web_search and st.session_state.get("serper_api_key"):
                            try:
                                web_results = search_web(user_question, st.session_state.serper_api_key)
                                web_context = format_web_results(web_results)
                                web_links = [r["link"] for r in web_results]
                            except Exception as e:
                                st.warning(f"Web search fail : {str(e)}")
                
                        # Check karo koi context mila bhi ya nahi
                        if not doc_context and not web_context:
                            answer = "I couldn't find any information to answer this question. Please upload the documents first or perform a web search."
                        else:
                            final_prompt = f"""Answer the question using the provided context. The context may come from two sources: your documents and a live web search. Use both to provide the best possible answer.

        From your documents:
        {doc_context if doc_context else "(No document context found.)"}

        From the web:
        {web_context if web_context else "(Web search was not enabled, or nothing was found.)"}

        Sawal: {user_question}
        """
                            response = st.session_state.gemini_client.models.generate_content(
                                model="models/gemini-3.5-flash-lite",
                                contents=final_prompt
                            )
                            answer = response.text
                
                        st.write(answer)
                
                        if doc_context and sources:
                            st.caption("📚 From your documents: " + ", ".join(sources))
                        if web_links:
                            st.caption("🌐 From the web: " + ", ".join(web_links))
                
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
            
                    except Exception as e:
                        error_msg = str(e)
                        if "503" in error_msg or "UNAVAILABLE" in error_msg:
                            st.error("⚠️ Gemini API abhi busy hai — thodi der baad dobara try karo")
                        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                            st.error("⚠️ API rate limit ho gayi — 1-2 minute wait karo phir try karo")
                        elif "401" in error_msg or "403" in error_msg:
                            st.error("⚠️ API key expire ya invalid ho gayi — sidebar se dobara initialize karo")
                        else:
                            st.error(f"❌ Error: {error_msg}")