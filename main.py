from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import httpx
import threading

app = FastAPI()

# Thread-safe storage
lock = threading.Lock()
students = {}
current_id = 1

# Pydantic Model
class Student(BaseModel):
    name: str
    age: int
    email: EmailStr

# Create student
@app.post("/students")
def create_student(student: Student):
    global current_id
    with lock:
        student_data = student.dict()
        student_data["id"] = current_id
        students[current_id] = student_data
        current_id += 1
    return student_data

# Read all students
@app.get("/students")
def get_all_students():
    return list(students.values())

# Read one student
@app.get("/students/{student_id}")
def get_student(student_id: int):
    student = students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

# Update student
@app.put("/students/{student_id}")
def update_student(student_id: int, student: Student):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    with lock:
        student_data = student.dict()
        student_data["id"] = student_id
        students[student_id] = student_data
    return student_data

# Delete student
@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    with lock:
        del students[student_id]
    return {"detail": "Student deleted"}

# Generate summary using Ollama
@app.get("/students/{student_id}/summary")
async def generate_summary(student_id: int):
    student = students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    prompt = (
        f"Summarize this student profile:\n"
        f"Name: {student['name']}\n"
        f"Age: {student['age']}\n"
        f"Email: {student['email']}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt}
        )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ollama API error")

    result = response.json()
    return {"summary": result.get("response", "No summary generated")}
