"""Application entry point for the alert explainer API."""

from fastapi import FastAPI

import models
from database import Base, engine
from routers import alerts

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Intelligence Layer -- Alert Explainer API")
app.include_router(alerts.router)


@app.get("/")
def status():
    return {"message": "Alert Explainer API is running"}