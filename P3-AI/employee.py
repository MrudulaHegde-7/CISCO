
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Tuple

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
import mysql.connector
from pydantic import BaseModel, Field


app = FastAPI(title="Employee Management System")


# -------------------------------
# Pydantic Model and Validation
# -------------------------------

class Employee(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=3, max_length=30)
    age: int = Field(ge=18, le=60)
    salary: float = Field(ge=25000)
    desig: str = Field(min_length=3, max_length=30)


# Salary update validation
class SalaryUpdate(BaseModel):
    salary: float = Field(ge=25000)


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "employee_management"),
    )


@contextmanager
def database_cursor() -> Iterator[Tuple[object, object]]:
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            yield connection, cursor
        finally:
            cursor.close()
    finally:
        connection.close()


def employee_from_row(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "age": row["age"],
        "salary": float(row["salary"]),
        "desig": row["desig"],
    }


@app.on_event("startup")
def create_employee_table():
    with database_cursor() as (connection, cursor):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INT NOT NULL PRIMARY KEY,
                name VARCHAR(30) NOT NULL,
                age INT NOT NULL,
                salary DECIMAL(12, 2) NOT NULL,
                desig VARCHAR(30) NOT NULL
            ) CHARACTER SET utf8mb4
            """
        )
        connection.commit()


# -------------------------------
# Custom Global Exception
# -------------------------------

class EmployeeException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


@app.exception_handler(EmployeeException)
async def employee_exception_handler(
    request: Request, exc: EmployeeException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )


# Global Pydantic Validation Exception
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Failed",
            "details": exc.errors()
        }
    )


# -------------------------------
# 1. GET - Welcome Message
# -------------------------------

@app.get("/")
def welcome():
    return {"message": "Welcome to Employee Management System"}


@app.get("/ui", include_in_schema=False)
def frontend():
    return FileResponse(Path(__file__).parent / "frontend" / "index.html")


# -------------------------------
# 2. POST - Add Employee
# -------------------------------

@app.post("/addEmployee", status_code=201)
def add_employee(emp: Employee):
    try:
        with database_cursor() as (connection, cursor):
            cursor.execute(
                """
                INSERT INTO employees (id, name, age, salary, desig)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (emp.id, emp.name, emp.age, emp.salary, emp.desig),
            )
            connection.commit()
    except mysql.connector.IntegrityError as error:
        if error.errno == 1062:
            raise EmployeeException(
                400, "Employee ID Already Exists"
            ) from error
        raise

    return {
        "message": "Employee Added Successfully",
        "employee": emp
    }


# -------------------------------
# 3. GET - Get All Employees
# -------------------------------

@app.get("/getAllEmployees")
def get_all_employees():
    with database_cursor() as (_, cursor):
        cursor.execute("SELECT id, name, age, salary, desig FROM employees ORDER BY id")
        employees = cursor.fetchall()
    if not employees:
        raise EmployeeException(
            404, "No Employees Available"
        )

    return [employee_from_row(employee) for employee in employees]


# -------------------------------
# 4. GET - Search Employee By ID
# -------------------------------

@app.get("/employeeByID/{id}")
def employee_by_id(id: int):
    with database_cursor() as (_, cursor):
        cursor.execute(
            "SELECT id, name, age, salary, desig FROM employees WHERE id = %s",
            (id,),
        )
        employee = cursor.fetchone()
    if employee:
        return employee_from_row(employee)

    raise EmployeeException(
        404, "Employee Not Found"
    )


# -------------------------------
# 5. GET - Search Employee By Name
# -------------------------------

@app.get("/employeeByName/{name}")
def employee_by_name(name: str):
    with database_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT id, name, age, salary, desig FROM employees
            WHERE LOWER(name) = LOWER(%s)
            ORDER BY id
            """,
            (name,),
        )
        result = cursor.fetchall()

    if not result:
        raise EmployeeException(
            404, "Employee Name Not Found"
        )

    return [employee_from_row(employee) for employee in result]


# -------------------------------
# 6. GET - Search Employee By Designation
# -------------------------------

@app.get("/employeeByDesignation/{desig}")
def employee_by_designation(desig: str):
    with database_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT id, name, age, salary, desig FROM employees
            WHERE LOWER(desig) = LOWER(%s)
            ORDER BY id
            """,
            (desig,),
        )
        result = cursor.fetchall()

    if not result:
        raise EmployeeException(
            404, "Designation Not Found"
        )

    return [employee_from_row(employee) for employee in result]


# -------------------------------
# 7. PUT - Update Complete Employee
# -------------------------------

@app.put("/updateEmployee/{id}")
def update_employee(id: int, emp: Employee):
    if emp.id != id:
        raise EmployeeException(
            400, "Employee ID Cannot Be Changed"
        )

    with database_cursor() as (connection, cursor):
        cursor.execute("SELECT id FROM employees WHERE id = %s", (id,))
        if cursor.fetchone() is None:
            raise EmployeeException(404, "Employee Not Found")
        cursor.execute(
            """
            UPDATE employees
            SET name = %s, age = %s, salary = %s, desig = %s
            WHERE id = %s
            """,
            (emp.name, emp.age, emp.salary, emp.desig, id),
        )
        connection.commit()

    return {
        "message": "Employee Updated Successfully",
        "employee": emp
    }


# -------------------------------
# 8. PATCH - Update Employee Salary
# -------------------------------

@app.patch("/updateSalary/{id}")
def update_salary(id: int, data: SalaryUpdate):
    with database_cursor() as (connection, cursor):
        cursor.execute("SELECT id FROM employees WHERE id = %s", (id,))
        if cursor.fetchone() is None:
            raise EmployeeException(404, "Employee Not Found")
        cursor.execute(
            "UPDATE employees SET salary = %s WHERE id = %s",
            (data.salary, id),
        )
        cursor.execute(
            "SELECT id, name, age, salary, desig FROM employees WHERE id = %s",
            (id,),
        )
        employee = employee_from_row(cursor.fetchone())
        connection.commit()

    return {
        "message": "Salary Updated Successfully",
        "employee": employee
    }


# -------------------------------
# 9. DELETE - Delete Employee By ID
# -------------------------------

@app.delete("/deleteEmployee/{id}")
def delete_employee(id: int):
    with database_cursor() as (connection, cursor):
        cursor.execute("DELETE FROM employees WHERE id = %s", (id,))
        if cursor.rowcount == 0:
            raise EmployeeException(404, "Employee Not Found")
        connection.commit()

    return {
        "message": "Employee Deleted Successfully"
    }


# -------------------------------
# 10. DELETE - Delete All Employees
# -------------------------------

@app.delete("/deleteAllEmployees")
def delete_all_employees():
    with database_cursor() as (connection, cursor):
        cursor.execute("DELETE FROM employees")
        if cursor.rowcount == 0:
            raise EmployeeException(404, "No Employees Available")
        connection.commit()

    return {
        "message": "All Employees Deleted Successfully"
    }
