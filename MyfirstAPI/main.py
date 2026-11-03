from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

@app.get("/hello")
def home():
    return {"message": "Hello World"}

@app.get("/greet")
def greet():
    return{"Good morning"}

class Employee(BaseModel):
    id:int
    name:str
    age:int
    salary:float
    designation:str
employees=[]
@app.post("/addEmployees")
def add_employees(emps:Employee):
    employees.append(emps)
    return {"message:successfully added"}

@app.get("/getEmployees")
def get_employees():
    return employees

@app.get("/EmployeeById/{id}")
def get_employees_byId(id:int):
    for emp in employees:
        if emp.id==id:
            return emp
    return {"message:not found"}

@app.delete("/deleteById/{id}")
def del_employees_byId(id:int):
    for emp in employees:
        if emp.id==id:
            employees.remove(emp)
            return {"message:deleted successfully"}
    return {"message:deletion failed"}

@app.delete("/deleteAllEmployees")
def del_all_employees():
    employees.clear()
    return {"message:deleted successfully"}

@app.put("/updateEmployee/{id}")
def update_employee(id:int,updatedEmp:Employee):
    for emp in employees:
        if emp.id == id:
            emp.name=updatedEmp.name
            emp.age=updatedEmp.age
            emp.salary=updatedEmp.salary
            emp.designation=updatedEmp.designation
            return emp
    return {"message:employee not found"}

