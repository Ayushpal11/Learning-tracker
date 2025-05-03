from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from routes import topics, plans, resources, analytics, quizzes
from db import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Learning Tracker API",
    description="API for tracking learning progress across various topics",
    version="1.0.0"
)

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://learning-tracker-eight.vercel.app/"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Include routers with proper prefix
app.include_router(topics.router, prefix="/topics", tags=["Topics"])
app.include_router(plans.router, prefix="/plan", tags=["Study Plans"])
app.include_router(resources.router, prefix="/resources", tags=["Resources"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])

# Connect to MongoDB on startup and disconnect on shutdown
@app.on_event("startup")
async def startup():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Welcome to the Learning Tracker API",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)