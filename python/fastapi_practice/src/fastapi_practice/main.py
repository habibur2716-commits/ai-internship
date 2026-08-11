import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from sqlmodel import SQLModel, Field, Session, create_engine, select

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

class Student(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    age: int
    email: str

# YAHAN app banta hai — ye sabse pehle hona chahiye baaki endpoints se
app = FastAPI()

# Secret key
API_KEY = "mysecretkey123"

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/students", status_code=201)
def create_student(student: Student):
    with Session(engine) as session:
        session.add(student)
        session.commit()
        session.refresh(student)
        return student

@app.get("/students")
def get_all_students():
    with Session(engine) as session:
        students = session.exec(select(Student)).all()
        return students

@app.get("/students/{student_id}")
def get_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student

# Naya endpoint - ye bhi app define hone ke BAAD hona chahiye
@app.get("/protected")
def protected_route(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return {"message": "You have access to protected data!"}