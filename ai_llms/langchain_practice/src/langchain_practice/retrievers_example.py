import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

texts = ["Uqba Lahore mein rehti hai", "Habib Karachi mein rehta hai", "Saim Islamabad mein rehta hai"]
vector_store = Chroma.from_texts(texts, embeddings)
retriever = vector_store.as_retriever()

results = retriever.invoke("Uqba kahan rehti hai?")
for doc in results:
    print(doc.page_content)