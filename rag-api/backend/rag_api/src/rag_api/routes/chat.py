from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from typing import List, TypedDict, Optional
from datetime import datetime
import time
import os
import json

from ..models import User, ChatSession, ChatMessage
from ..schemas import (
    ChatRequest, 
    ChatResponse, 
    ChatSessionResponse, 
    MessageResponse, 
    ChatUpdateTitle
)
from ..routes.auth import get_current_user
from ..services import rag, search
from ..database import get_session
from google import genai

from langgraph.graph import StateGraph, END

router = APIRouter(prefix="/chat", tags=["Chat & Session Management"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_with_fallback(client, contents):
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.8-flash",
        "gemini-2.5-flash"
    ]
    
    last_exception = None
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                print(f"[AI Router] Trying model: {model_name} (Attempt {attempt + 1})")
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                if response and response.text:
                    print(f"[AI Router] Success with model: {model_name}")
                    return response
            except Exception as e:
                last_exception = e
                print(f"[AI Router Warning] {model_name} attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2)
                continue
            
    print(f"[AI Router CRITICAL] All models failed. Last error: {last_exception}")
    raise HTTPException(
        status_code=503, 
        detail="Google Gemini API is temporarily busy. Please try again in a few seconds."
    )

def generate_stream_chunks_with_fallback(client, contents):
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.8-flash",
        "gemini-2.5-flash"
    ]
    
    last_exception = None
    for model_name in models_to_try:
        for attempt in range(1, 4):
            try:
                print(f"[AI Stream Router] Trying stream: {model_name} (Attempt {attempt})")
                stream_response = client.models.generate_content_stream(
                    model=model_name,
                    contents=contents
                )
                
                chunks = []
                stream_iter = iter(stream_response)
                try:
                    first_chunk = next(stream_iter)
                    chunks.append(first_chunk)
                except StopIteration:
                    pass

                print(f"[AI Stream Router] Success with stream: {model_name}")
                for c in chunks:
                    yield c
                for chunk in stream_iter:
                    yield chunk
                return

            except Exception as e:
                last_exception = e
                print(f"[AI Stream Router Warning] {model_name} attempt {attempt} failed: {str(e)}")
                time.sleep(attempt * 2)
                continue
            
    print(f"[AI Stream Router CRITICAL] All streaming models failed. Last error: {last_exception}")
    raise Exception(f"Streaming failed after retries: {last_exception}")

# ==================== LANGGRAPH QUERY ROUTER ARCHITECTURE ====================

class GraphState(TypedDict):
    question: str
    user_id: int
    session_id: int
    doc_context: str
    doc_sources: List[str]
    web_context: str
    web_sources: List[str]
    route_decision: str

def retriever_node(state: GraphState) -> GraphState:
    print("\n--- [LangGraph Node] Retrieving Document Chunks ---")
    doc_texts, doc_sources = rag.retrieve_chunks(
        question=state["question"], 
        user_id=state["user_id"],
        session_id=state["session_id"]
    )
    doc_context = "\n\n".join(doc_texts) if doc_texts else ""
    return {
        "doc_context": doc_context,
        "doc_sources": doc_sources
    }

def router_node(state: GraphState) -> GraphState:
    print("--- [LangGraph Node] Analyzing Context for Web Search Routing ---")
    doc_context = state.get("doc_context", "")
    question = state["question"]

    if not doc_context.strip():
        print(" -> Decision: WEB_SEARCH (No Local Context Found)")
        return {"route_decision": "WEB_SEARCH"}

    client = genai.Client(api_key=GEMINI_API_KEY)
    router_prompt = f"""You are an Autonomous Decision Router Agent.
Your task is to analyze the User Question and the retrieved Local Document Context to decide if a Web Search is required.

Rules:
1. Return 'WEB_SEARCH' if local context is completely missing, irrelevant, incomplete, or if the question demands live/current real-world info.
2. Return 'LOCAL_ONLY' if the local document context is fully sufficient to answer the user's question accurately.
3. Respond ONLY with 'WEB_SEARCH' or 'LOCAL_ONLY'. Do not write any other explanation.

[Local Document Context]
{doc_context[:1500]}

[User Question]
{question}

Decision:"""

    try:
        decision_resp = generate_with_fallback(client, router_prompt)
        decision = decision_resp.text.strip().upper()
        if "WEB_SEARCH" in decision:
            print(" -> Decision: WEB_SEARCH (Context Incomplete or Live Info Requested)")
            return {"route_decision": "WEB_SEARCH"}
        else:
            print(" -> Decision: LOCAL_ONLY (Document Context Sufficient)")
            return {"route_decision": "LOCAL_ONLY"}
    except Exception as err:
        print(f"Router Node Error: {err}")
        return {"route_decision": "LOCAL_ONLY"}

def web_search_node(state: GraphState) -> GraphState:
    print("--- [LangGraph Node] Executing Live Web Search ---")
    web_context, web_sources = search.web_search(state["question"])
    return {
        "web_context": web_context,
        "web_sources": web_sources
    }

def route_decision_edge(state: GraphState) -> str:
    if state.get("route_decision") == "WEB_SEARCH":
        return "web_search"
    return "end"

graph_builder = StateGraph(GraphState)

graph_builder.add_node("retriever", retriever_node)
graph_builder.add_node("router", router_node)
graph_builder.add_node("web_search", web_search_node)

graph_builder.set_entry_point("retriever")
graph_builder.add_edge("retriever", "router")

graph_builder.add_conditional_edges(
    "router",
    route_decision_edge,
    {
        "web_search": "web_search",
        "end": END
    }
)

graph_builder.add_edge("web_search", END)
graph_app = graph_builder.compile()

# ==================== SESSION MANAGEMENT ENDPOINTS ====================

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    new_session = ChatSession(user_id=current_user.id, title="New Chat")
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_user_sessions(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    statement = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return db.exec(statement).all()

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    session_obj = db.get(ChatSession, session_id)
    if not session_obj or session_obj.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return db.exec(statement).all()

@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
def rename_session(
    session_id: int,
    payload: ChatUpdateTitle,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    session_obj = db.get(ChatSession, session_id)
    if not session_obj or session_obj.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session_obj.title = payload.title
    session_obj.updated_at = datetime.utcnow()
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return session_obj

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    session_obj = db.get(ChatSession, session_id)
    if not session_obj or session_obj.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    ).all()
    
    for msg in messages:
        db.delete(msg)
        
    db.delete(session_obj)
    db.commit()
    return None

# ==================== QUERY ENDPOINTS USING LANGGRAPH ====================

@router.post("/ask", response_model=ChatResponse)
def ask(
    data: ChatRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        session_obj = db.get(ChatSession, data.session_id)
        if not session_obj or session_obj.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Invalid chat session")

        user_msg = ChatMessage(
            session_id=data.session_id,
            sender="user",
            content=data.question
        )
        db.add(user_msg)

        if session_obj.title == "New Chat":
            session_obj.title = data.question[:30] + ("..." if len(data.question) > 30 else "")

        initial_state = {
            "question": data.question,
            "user_id": current_user.id,
            "session_id": data.session_id,
            "doc_context": "",
            "doc_sources": [],
            "web_context": "",
            "web_sources": [],
            "route_decision": ""
        }
        
        final_graph_state = graph_app.invoke(initial_state)

        doc_context = final_graph_state.get("doc_context", "")
        doc_sources = final_graph_state.get("doc_sources", [])
        web_context = final_graph_state.get("web_context", "")
        web_sources = final_graph_state.get("web_sources", [])

        if not doc_context and not web_context:
            answer_text = "I couldn't find any relevant information in your uploaded documents or via live web search."
            
            ai_msg = ChatMessage(session_id=data.session_id, sender="assistant", content=answer_text)
            session_obj.updated_at = datetime.utcnow()
            db.add(ai_msg)
            db.add(session_obj)
            db.commit()

            return ChatResponse(
                answer=answer_text,
                session_id=data.session_id,
                doc_sources=[],
                web_sources=[]
            )

        final_prompt = f"""You are an advanced Autonomous AI Assistant. Answer the question accurately using the provided contexts.

INSTRUCTIONS:
1. Prioritize answers based on facts available in the context.
2. Clearly synthesize responses if information spans across both document and web contexts.

[Context From Documents]
{doc_context if doc_context else "(No relevant document context)"}

[Context From Live Web Search]
{web_context if web_context else "(Web search was not required or returned no results)"}

Question: {data.question}
Answer:"""

        response = generate_with_fallback(client, final_prompt)

        ai_msg = ChatMessage(
            session_id=data.session_id,
            sender="assistant",
            content=response.text
        )
        session_obj.updated_at = datetime.utcnow()
        db.add(ai_msg)
        db.add(session_obj)
        db.commit()

        return ChatResponse(
            answer=response.text,
            session_id=data.session_id,
            doc_sources=doc_sources if doc_context else [],
            web_sources=web_sources if web_context else []
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask-stream")
def ask_stream(
    data: ChatRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        session_obj = db.get(ChatSession, data.session_id)
        if not session_obj or session_obj.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Invalid chat session")

        user_msg = ChatMessage(
            session_id=data.session_id,
            sender="user",
            content=data.question
        )
        db.add(user_msg)

        if session_obj.title == "New Chat":
            session_obj.title = data.question[:30] + ("..." if len(data.question) > 30 else "")
        
        db.commit()

        initial_state = {
            "question": data.question,
            "user_id": current_user.id,
            "session_id": data.session_id,
            "doc_context": "",
            "doc_sources": [],
            "web_context": "",
            "web_sources": [],
            "route_decision": ""
        }
        
        final_graph_state = graph_app.invoke(initial_state)

        doc_context = final_graph_state.get("doc_context", "")
        doc_sources = final_graph_state.get("doc_sources", [])
        web_context = final_graph_state.get("web_context", "")
        web_sources = final_graph_state.get("web_sources", [])

        final_prompt = f"""You are an advanced Autonomous AI Assistant. Answer the question accurately using the provided contexts.

INSTRUCTIONS:
1. Prioritize answers based on facts available in the context.
2. Clearly synthesize responses if information spans across both document and web contexts.

[Context From Documents]
{doc_context if doc_context else "(No relevant document context)"}

[Context From Live Web Search]
{web_context if web_context else "(Web search was not required or returned no results)"}

Question: {data.question}
Answer:"""

        def event_generator():
            try:
                full_reply = ""

                meta_payload = {
                    "doc_sources": doc_sources if doc_context else [],
                    "web_sources": web_sources if web_context else []
                }
                yield f"data: {json.dumps({'meta': meta_payload})}\n\n"

                stream_generator = generate_stream_chunks_with_fallback(client, final_prompt)
                for chunk in stream_generator:
                    if hasattr(chunk, 'text') and chunk.text:
                        full_reply += chunk.text
                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"

                if full_reply:
                    ai_msg = ChatMessage(
                        session_id=data.session_id,
                        sender="assistant",
                        content=full_reply
                    )
                    session_obj.updated_at = datetime.utcnow()
                    db.add(ai_msg)
                    db.add(session_obj)
                    db.commit()

                yield "data: [DONE]\n\n"

            except Exception as stream_err:
                print(f"[Streaming Error Safe-Catch]: {stream_err}")
                err_text = "Google Gemini servers high traffic face kar rahe hain. Retrying automatically, please wait a moment."
                yield f"data: {json.dumps({'text': err_text})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))