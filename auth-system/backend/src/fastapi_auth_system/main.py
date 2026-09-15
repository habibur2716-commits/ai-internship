from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="FastAPI Auth System",
    description="Complete Authentication & Authorization",
    version="1.0.0",
    lifespan=lifespan
)

# CORS allow karna taake frontend backend se baat kar sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Har origin se request allow ki hai
    allow_credentials=True,
    allow_methods=["*"], # GET, POST, PUT, DELETE sab allow hain
    allow_headers=["*"], # Sab headers (like Authorization) allow hain
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "FastAPI Auth System is running!"}