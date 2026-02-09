import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def main_page():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)