from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def home():
    return {"message": "Hello World"}
    
@app.get("/greet")
def greet():
    return{"Good morning"}