from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def healthcheck():
    return "Health check check"