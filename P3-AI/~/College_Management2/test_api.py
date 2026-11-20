"""End-to-end API checks using an isolated in-memory database."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


def test_college_management_api():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine)

    def override_get_db():
        with test_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            assert client.get("/").status_code == 200
            assert client.get("/docs").status_code == 200
            for name in ("Computer Science", "Mechanical Engineering"):
                response = client.post("/api/departments/", json={"department_name": name})
                assert response.status_code == 201
                assert response.json()["department_name"] == name
            departments = client.get("/api/departments/").json()
            assert departments == [
                {"department_id": 1, "department_name": "Computer Science"},
                {"department_id": 2, "department_name": "Mechanical Engineering"},
            ]
            for name, department in (("Asha Rao", departments[0]), ("Rahul Mehta", departments[1])):
                response = client.post("/api/students/", json={"student_name": name, "department_id": department["department_id"]})
                assert response.status_code == 201
                assert response.json()["department_name"] == department["department_name"]
            assert client.get("/api/students/").json() == [
                {"student_id": 1, "student_name": "Asha Rao", "department_id": 1, "department_name": "Computer Science"},
                {"student_id": 2, "student_name": "Rahul Mehta", "department_id": 2, "department_name": "Mechanical Engineering"},
            ]
            response = client.post("/api/students/", json={"student_name": "Ram", "department_id": 10})
            assert response.status_code == 404
            assert response.json() == {"detail": "Department not found"}
    finally:
        app.dependency_overrides.clear()
        engine.dispose()