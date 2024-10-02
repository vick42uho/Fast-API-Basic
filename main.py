from  fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def home_root():
    return {"message": "Success"}


@app.get("/deploy")
async def home_root(): 
    return {"message": "Vercel Deployment"}