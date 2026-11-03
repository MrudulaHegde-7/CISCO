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

