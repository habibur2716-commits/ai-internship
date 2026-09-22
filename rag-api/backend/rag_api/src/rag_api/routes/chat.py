from fastapi import APIRouter, Depends, HTTPException
from ..models import User
from ..schemas import ChatRequest, ChatResponse
from ..routes.auth import get_current_user
from ..services import rag, search
from google import genai
import os

router = APIRouter(prefix="/chat", tags=["Chat"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@router.post("/ask", response_model=ChatResponse)
def ask(
    data: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Retrieve from Pinecone
        doc_texts, doc_sources = rag.retrieve_chunks(data.question, current_user.id)
        doc_context = "\n\n".join(doc_texts) if doc_texts else ""
        
        # Web search (optional)
        web_context = ""
        web_sources = []
        if data.enable_web_search:
            web_context, web_sources = search.web_search(data.question)
        
        if not doc_context and not web_context:
            return ChatResponse(
                answer="No relevant information found in documents or web search.",
                doc_sources=[],
                web_sources=[]
            )
        
        # System Prompt
        final_prompt = f"""You are a smart AI Assistant. Answer the question accurately using ONLY the provided contexts below.

STRICT INSTRUCTIONS:
1. Answer the question using the available context.
2. If the user's question has NOTHING to do with the "From documents" text, ignore the document text completely.

[Context From Documents]
{doc_context if doc_context else "(No matching context found in documents)"}

[Context From Web Search]
{web_context if web_context else "(Web search disabled or no results)"}

Question: {data.question}
Answer:"""

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=final_prompt
        )
        
        # FIX: Agar doc_context empty tha, toh doc_sources array bilkul empty send karein
        final_doc_sources = doc_sources if doc_context else []
        final_web_sources = web_sources if web_context else []

        return ChatResponse(
            answer=response.text,
            doc_sources=final_doc_sources,
            web_sources=final_web_sources
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))