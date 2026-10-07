import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from .database import create_db_and_tables
from .routes import auth, documents, chat

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="RAG Web Search Assistant API",
    description="FastAPI backend for RAG with authentication",
    version="1.0.0",
    lifespan=lifespan
)

# 1. Exact origins list
origins = [
    "https://ai-internship-ivory.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# 2. Add CORS Middleware RIGHT AFTER app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "RAG Web Search Assistant API is running!"}