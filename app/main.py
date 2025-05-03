from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.validator import validator

# Create FastAPI app instance
app = FastAPI(
    title="Bulk Account Validator API",
    description="A service to validate single and bulk bank accounts using Pesalink APIs",
    version="1.0.0"
)

# Configure CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

# Include API routes
app.include_router(validator)

# Root endpoint for API health check
@app.get("/")
async def root():
    return {"status": "online", "message": "Bulk Account Validator API is running"}