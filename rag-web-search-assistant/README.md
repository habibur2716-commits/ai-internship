# RAG Web Search Assistant

A Streamlit-based RAG (Retrieval Augmented Generation) application that lets you 
chat with your PDF documents, websites, and YouTube videos — with optional live web search.

## Features
- Upload PDF documents
- Process any website URL
- Process YouTube video transcripts
- Chat with all sources combined
- Optional live web search (via Serper API)

## Setup

1. Clone/download the project
2. Install dependencies: `poetry install`
3. Run: `poetry run streamlit run src/rag_web_search_assistant/main.py`

## Required API Keys
- **Gemini API Key** (required) — get from [aistudio.google.com](https://aistudio.google.com)
- **Serper API Key** (optional, for web search) — get from [serper.dev](https://serper.dev)

## LLM Provider
This app uses **Google Gemini** (gemini-3.6-flash model).
To switch to another provider (OpenAI, Anthropic, etc.), update the 
`gemini_client` initialization and `generate_content` calls in `main.py`.

## Security Notes
- API keys are stored in session state only, never written to disk
- Only embeddings are persisted in ChromaDB, not raw document text