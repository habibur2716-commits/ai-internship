import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# STEP 1: Document Load Karna
loader = TextLoader("src/rag_practice/sample_data.txt", encoding="utf-8")
documents = loader.load()

# STEP 2: Chunking
text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
chunks = text_splitter.split_documents(documents)
print(f"Total chunks bane: {len(chunks)}")

# STEP 3: Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

# STEP 4: Vector Database
vector_store = Chroma.from_documents(chunks, embeddings)
retriever = vector_store.as_retriever()

# STEP 5: AI Model
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=api_key)

# STEP 6: Sawal Poochna (Manual RAG - Step by Step)
question = "Habib kahan rehta hai aur uska favorite language kya hai?"

# 6a: Retrieval - relevant chunks dhoondo
retrieved_docs = retriever.invoke(question)
print(f"\n{len(retrieved_docs)} relevant chunks mile")

# 6b: Un chunks ko ek text mein jodo (context banao)
context = "\n\n".join([doc.page_content for doc in retrieved_docs])

# 6c: Augmented - context + sawal ko mila ke prompt banao
final_prompt = f"""Neeche diye gaye context ki madad se sawal ka jawab do:

Context:
{context}

Sawal: {question}
"""

# 6d: Generation - AI se jawab lo
response = llm.invoke(final_prompt)

if isinstance(response.content, list):
    print("\nJawab:", response.content[0]["text"])
else:
    print("\nJawab:", response.content)