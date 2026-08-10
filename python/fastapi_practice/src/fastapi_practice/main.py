import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select

# .env file se DATABASE_URL load karna
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Database engine banana (connection setup)
engine = create_engine(DATABASE_URL)

# Table define karna (SQLModel class se)
class Student(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    age: int
    email: str

app = FastAPI()

# App start hote hi table create karo (agar na ho)
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Naya student database mein add karna
@app.post("/students", status_code=201)
def create_student(student: Student):
    with Session(engine) as session:
        session.add(student)
        session.commit()
        session.refresh(student)
        return student

# Saare students database se nikalna
@app.get("/students")
def get_all_students():
    with Session(engine) as session:
        students = session.exec(select(Student)).all()
        return students

# Ek specific student nikalna
@app.get("/students/{student_id}")
def get_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student