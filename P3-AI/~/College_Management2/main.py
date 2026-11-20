"""Application entry point for the college management API."""

from fastapi import FastAPI

import models
from database import Base, engine
from routers import departments, students

Base.metadata.create_all(bind=engine)

app = FastAPI(title="College Management API")
app.include_router(departments.router)
app.include_router(students.router)


@app.get("/")
def status():
	return {"message": "College Management API is running"}
