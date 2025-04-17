from fastapi import FastAPI

app = FastAPI()

@app.get("/welcome")
async def welcome_fun():
    return{"messege" : "Hello Wello !"}

