from main import app

@app.get("/auth/login")
def login():
    return