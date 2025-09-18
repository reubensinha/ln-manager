from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()


sample_data = {
    "title": "This is a test note.",
    "content": "Programming is fun!",
}

# app.mount("/assets", StaticFiles(directory="../ln-auto-frontend/build/client/assets"), name="assets")

# @app.get("/{full_path:path}")
# async def frontend(full_path: str):
#     return FileResponse("../ln-auto-frontend/build/client/index.html")

@app.get("/")
async def read_root():
    return sample_data
 