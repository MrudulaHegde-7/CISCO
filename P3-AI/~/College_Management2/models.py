"""SQLAlchemy models for departments and their students."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Department(Base):
    __tablename__ = "departments"

    department_id: Mapped[int] = mapped_column(primary_key=True)
    department_name: Mapped[str] = mapped_column(String, nullable=False)
    students: Mapped[list["Student"]] = relationship(back_populates="department")


class Student(Base):
    __tablename__ = "students"

    student_id: Mapped[int] = mapped_column(primary_key=True)
    student_name: Mapped[str] = mapped_column(String, nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.department_id"), nullable=False)
    department: Mapped["Department"] = relationship(back_populates="students")

    @property
    def department_name(self) -> str:
        return self.department.department_name