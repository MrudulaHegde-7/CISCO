"""Pydantic request and response schemas."""

from pydantic import BaseModel, ConfigDict


class DepartmentCreate(BaseModel):
    department_name: str


class DepartmentOut(DepartmentCreate):
    model_config = ConfigDict(from_attributes=True)

    department_id: int


class StudentCreate(BaseModel):
    student_name: str
    department_id: int


class StudentOut(StudentCreate):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    department_name: str