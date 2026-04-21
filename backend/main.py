from fastapi import FastAPI
from mentor_api import router as mentor_router # This imports your work
from student_api import router as student_router

app = FastAPI(title="Eduronix Backend")

# This "mounts" all your mentor and student routes into the app
app.include_router(mentor_router)
app.include_router(student_router)

@app.get("/")
async def root():
    return {"message": "Eduronix API is online and healthy!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True) 