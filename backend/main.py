from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mentor_api import router as mentor_router # This imports your work
from student_api import router as student_router
from booking_api import router as booking_router 
from collegematch_api import router as collegematch_router 
from admin_api import router as admin_router

app = FastAPI(title="Eduronix Backend")

# Enable CORS for local development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This "mounts" all your mentor, student, and admin routes into the app
app.include_router(mentor_router)
app.include_router(student_router)
app.include_router(booking_router)
app.include_router(collegematch_router) 
app.include_router(admin_router)

@app.get("/")
async def root():
    return {"message": "Eduronix API is online and healthy!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True) 