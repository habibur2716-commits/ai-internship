import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Pehle RAG setup karte hain (jaisa pehle kiya tha)
loader = TextLoader("src/rag_practice/sample_data.txt", encoding="utf-8")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
chunks = text_splitter.split_documents(documents)

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
vector_store = Chroma.from_documents(chunks, embeddings)
retriever = vector_store.as_retriever()

# STEP: RAG ko ek FUNCTION bana dete hain
def search_company_documents(query: str) -> str:
    """Company ke documents (jaise leave policy, employee details, company info) mein se relevant information dhoondta hai. Isay tab use karo jab sawal company, employees, ya policies ke baare mein ho."""
    retrieved_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    return context

# Ab is function ko AI ko "tool" ke taur pe dete hain
client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="Company ki leave policy kya hai?",
    config={
        "tools": [search_company_documents]
    }
)

print("Jawab:", response.text)

print("\n---\n")

# Ab ek general sawal try karte hain (jisme documents ki zaroorat nahi)
response2 = client.models.generate_content(
    model="gemini-flash-latest",
    contents="2 + 2 kitna hota hai?",
    config={
        "tools": [search_company_documents]
    }
)

print("Jawab:", response2.text)