import os
import sys
from dotenv import load_dotenv
from sqlmodel import create_engine, Session, SQLModel

load_dotenv()

# ===== CONFIG VALIDATION =====
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL is not set in .env file")
    sys.exit(1)

if not SECRET_KEY:
    print("ERROR: SECRET_KEY is not set in .env file")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session