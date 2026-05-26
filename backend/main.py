import sys
import os

# 1. Inject local packages folder into paths
bundle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'local_packages'))
sys.path.insert(0, bundle_path)

# 2. Force Python 3.9 to map 'typing' requests to 'typing_extensions'
try:
    from typing import TypeAlias
except ImportError:
    import typing
    import typing_extensions
    # Copy all missing backward-compatible attributes into standard typing
    for attr in dir(typing_extensions):
        if not hasattr(typing, attr):
            setattr(typing, attr, getattr(typing_extensions, attr))
    sys.modules['typing'] = typing 
from fastapi import FastAPI
from mentor_api import router as mentor_router # This imports your work
from student_api import router as student_router
from booking_api import router as booking_router

app = FastAPI(title="Eduronix Backend")

# This "mounts" all your mentor and student routes into the app
app.include_router(mentor_router)
app.include_router(student_router)
app.include_router(booking_router)

@app.get("/")
async def root():
    return {"message": "Eduronix API is online and healthy!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True) 