from fastapi import FastAPI, UploadFile, File, HTTPException, Depends,  APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from pandas import pandas as pd
import httpx
import io
import csv
from app.services.pesalink import fetch_api_key, validate_account, validate_bulk_accounts
from app.models.account import AccountRequest, ApiResponse

# app = FastAPI()

# Create router with prefix
validator = APIRouter(tags=["validation"])

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#Api key end points
@validator.get("/api/key", response_model=dict, summary="Fetch Pesalink API key")
async def get_api_key():
    """
    Retrieve API key from Pesalink service for authentication purposes.
    
    Returns:
        dict: JSON response containing the API key
    """
    try:
        return await fetch_api_key()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch API key: {str(e)}")


# Validate single account
@validator.post("/api/validate", response_model=dict, summary="Validate a single account")
async def validate_single_account(account_details: AccountRequest):
    """
    Validate a single bank account against Pesalink service.
    
    Args:
        account_details (AccountRequest): Account information including account number and bank code
        
    Returns:
        dict: Account validation result
    """
    try:
        return await validate_account(account_details.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

# Bulk validation via CSV
@validator.post("/validate/bulk", response_model=ApiResponse, summary="Validate accounts from CSV")
async def validate_csv(file: UploadFile = File(...)):
    """
    Validate multiple bank accounts from an uploaded CSV file.
    
    The CSV file must contain 'Account Number' and 'Bank Code' columns.
    
    Args:
        file (UploadFile): CSV file containing account details
        
    Returns:
        ApiResponse: Object containing valid accounts, invalid accounts with error codes, and summary
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        return await validate_bulk_accounts(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk validation failed: {str(e)}")

# Optional: Download example CSV
@validator.get("/api/sample", summary="Download a sample CSV template")
async def sample_csv():
    """
    Provides a downloadable sample CSV template with the correct format.
    
    Returns:
        StreamingResponse: CSV file download
    """
    from fastapi.responses import StreamingResponse
    import io
    
    content = "Account Number,Bank Code\n123456789012,01\n987654321098,02"
    return StreamingResponse(
        io.StringIO(content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_accounts.csv"}
    )