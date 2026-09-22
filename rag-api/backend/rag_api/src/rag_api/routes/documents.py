from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from ..database import get_session
from ..models import User, Document
from ..schemas import DocumentResponse, URLRequest, YouTubeRequest
from ..routes.auth import get_current_user
from ..services import rag

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload-pdf", response_model=DocumentResponse, status_code=201)
def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    try:
        file_bytes = file.file.read()
        text = rag.extract_text_from_pdf(file_bytes)
        
        if len(text) < 50:
            raise HTTPException(status_code=400, detail="PDF text too short or empty")
        
        chunks_count = rag.chunk_and_store(text, file.filename, current_user.id)
        
        doc = Document(
            user_id=current_user.id,
            source_type="pdf",
            source_name=file.filename,
            chunks_count=chunks_count
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-url", response_model=DocumentResponse, status_code=201)
def process_url(
    data: URLRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        text = rag.extract_text_from_url(data.url)
        chunks_count = rag.chunk_and_store(text, data.url, current_user.id)
        
        doc = Document(
            user_id=current_user.id,
            source_type="url",
            source_name=data.url,
            chunks_count=chunks_count
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-youtube", response_model=DocumentResponse, status_code=201)
def process_youtube(
    data: YouTubeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        text = rag.extract_youtube_transcript(data.url)
        chunks_count = rag.chunk_and_store(text, data.url, current_user.id)
        
        doc = Document(
            user_id=current_user.id,
            source_type="youtube",
            source_name=data.url,
            chunks_count=chunks_count
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=list[DocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    docs = session.exec(
        select(Document).where(Document.user_id == current_user.id)
    ).all()
    return docs

@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete chunks from Vector DB (ChromaDB)
    rag.delete_doc_chunks(source_name=doc.source_name, user_id=current_user.id)

    session.delete(doc)
    session.commit()
    return {"message": "Document and its chunks deleted successfully"}