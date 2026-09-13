from fastapi import FastAPI
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

app.include_router(router)

@app.get("/")
def root():
    return {"message": "FastAPI Auth System is running!"}