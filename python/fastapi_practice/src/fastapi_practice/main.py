from fastapi import FastAPI

app = FastAPI()

# GET - data lena
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# GET - specific item lena (URL mein parameter ke sath)
@app.get("/students/{student_id}")
def get_student(student_id: int):
    return {"student_id": student_id, "name": "Ali"}

# POST - naya data bhejna
@app.post("/students")
def create_student(name: str):
    return {"message": f"Student {name} created successfully"}

# PUT - data update karna
@app.put("/students/{student_id}")
def update_student(student_id: int, name: str):
    return {"message": f"Student {student_id} updated to {name}"}

# DELETE - data mitana
@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    return {"message": f"Student {student_id} deleted"}