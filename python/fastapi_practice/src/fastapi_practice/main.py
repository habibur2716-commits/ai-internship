from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio

app = FastAPI()

class Student(BaseModel):
    name: str
    age: int
    email: str

# Fake database (practice ke liye)
students_db = {}

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# POST - status code 201 (Created)
@app.post("/students/{student_id}", status_code=201)
def create_student(student_id: int, student: Student):
    students_db[student_id] = student
    return {"message": f"Student {student.name} created successfully"}

# GET - agar student na mile to 404 error
@app.get("/students/{student_id}")
def get_student(student_id: int):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    return students_db[student_id]

@app.get("/async-test")
async def async_test():
    await asyncio.sleep(5)
    return {"message": "This was async Waited 5 seconds without blocking."}
