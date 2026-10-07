import os
import re
import time
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
from pypdf import PdfReader
from bs4 import BeautifulSoup
import requests
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "rag-index")

# Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

def get_embeddings_model():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GEMINI_API_KEY,
        output_dimensionality=768
    )

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_and_store(text: str, source_name: str, user_id: int, session_id: int) -> int:
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    chunks = splitter.split_text(text)

    if not chunks:
        return 0

    embeddings_model = get_embeddings_model()
    embeddings = []

    for chunk in chunks:
        emb = embeddings_model.embed_query(chunk)
        embeddings.append(emb)
        time.sleep(0.7)  # Pause to respect rate limits

    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vectors.append({
            "id": f"{user_id}_{session_id}_{source_name}_chunk_{i}",
            "values": embedding,
            "metadata": {
                "source": source_name,
                "chunk_index": i,
                "user_id": str(user_id),
                "session_id": str(session_id),  # Chat Session Isolation
                "text": chunk
            }
        })

    index.upsert(vectors=vectors, namespace=f"user_{user_id}")
    print(f"✅ Upserted {len(chunks)} chunks to namespace: user_{user_id} for session: {session_id}")
    return len(chunks)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    import io
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return clean_text(text)

def extract_text_from_url(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    return clean_text(soup.get_text(separator=" "))

def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def extract_youtube_transcript(url: str) -> str:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")
    
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    text = " ".join([entry["text"] for entry in transcript_list])
    return clean_text(text)

def retrieve_chunks(question: str, user_id: int, session_id: int, n_results: int = 5, min_score: float = 0.35):
    embeddings_model = get_embeddings_model()
    query_embedding = embeddings_model.embed_query(question)

    # Filter strictly by session_id
    filter_query = {"session_id": {"$eq": str(session_id)}}

    results = index.query(
        vector=query_embedding,
        top_k=n_results,
        namespace=f"user_{user_id}",
        filter=filter_query,
        include_metadata=True
    )

    matches = getattr(results, "matches", []) or results.get("matches", [])
    
    print(f"\n--- RAG RETRIEVAL DEBUG ---")
    print(f"Namespace: user_{user_id} | Session: {session_id} | Matches found in Pinecone: {len(matches)}")

    if not matches:
        return [], []

    texts = []
    sources = []

    for match in matches:
        score = match.score if hasattr(match, 'score') else match.get("score", 0.0)
        metadata = match.metadata if hasattr(match, 'metadata') else match.get("metadata", {})
        
        print(f"Chunk Score: {score:.4f} | Source: {metadata.get('source')}")

        if score >= min_score:
            text = metadata.get("text")
            source = metadata.get("source") or metadata.get("source_name")
            
            if text:
                texts.append(text)
            if source:
                sources.append(source)

    unique_sources = list(set(sources))
    print(f"Accepted Chunks: {len(texts)} / {len(matches)}")
    return texts, unique_sources

def delete_doc_chunks(source_name: str, user_id: int):
    try:
        index.delete(
            filter={"source": {"$eq": source_name}},
            namespace=f"user_{user_id}"
        )
        print(f"Deleted chunks for source '{source_name}' in namespace user_{user_id}")
    except Exception as e:
        print(f"Error deleting chunks from Pinecone: {e}")