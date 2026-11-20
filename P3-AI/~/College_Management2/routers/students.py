"""Endpoints for listing and creating students."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Department, Student
from schemas import StudentCreate, StudentOut

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("/", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    statement = select(Student).options(selectinload(Student.department)).order_by(Student.student_id)
    return db.scalars(statement).all()


@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    department = db.get(Department, student.department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    db_student = Student(student_name=student.student_name, department=department)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student