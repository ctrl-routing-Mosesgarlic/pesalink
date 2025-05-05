import httpx
import time
from fastapi import UploadFile, HTTPException
from app.utils.csv_parser import parse_csv
# from app.models.account import AccountRequest, AccountResponse
from app.models.account import AccountResponse, AccountError, ValidationSummary, ApiResponse
from typing import Dict, List, Any
import re
import os
from dotenv import load_dotenv

load_dotenv()

# Base URL for Pesalink API
PESALINK_BASE = os.getenv("PESALINK_BASE_URL")
api_key = os.getenv("PESALINK_API_KEY")

if not PESALINK_BASE:
    print("WARNING: PESALINK_BASE_URL not set in environment variables")


def get_pesalink_base_url() -> str:
    """
    Get and validate the Pesalink base URL, ensuring it has a protocol.
    """
    base_url = os.getenv("PESALINK_BASE_URL", "")
    
    # If URL doesn't start with http:// or https://, add https://
    if not re.match(r'^https?://', base_url):
        base_url = f"https://{base_url}"
        
    return base_url

PESALINK_BASE = get_pesalink_base_url()

async def fetch_api_key() -> Dict[str, Any]:
    """
    Fetches API key from Pesalink service
    
    Returns:
        Dict: JSON response containing the API key
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(f"{api_key}/api/key")
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Pesalink API error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )

async def validate_account(payload: Dict[str, str]) -> Dict[str, Any]:
    """
    Validates a single account using Pesalink API
    
    Args:
        payload (Dict): Account details with accountNumber and bankCode
        
    Returns:
        Dict: Validation result from Pesalink
    """
    try:
        # Get API key
        api_key_response = await fetch_api_key()
        api_key = api_key_response["api_key"]
        
        # Get base URL with protocol
        base_url = get_pesalink_base_url()
        
        # Log for debugging
        print(f"Using base URL: {base_url}")
        
        # Set headers with API key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Make sure the URL has the protocol
        endpoint = f"{base_url}/api/validate"
        if not endpoint.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid endpoint URL: {endpoint}. URL must include http:// or https:// protocol.")
            
        print(f"Making request to: {endpoint}")

        
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(endpoint, json=payload)
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            # Handle validation errors from the API
            try:
                error_data = e.response.json()
                return {
                    "accountNumber": payload["accountNumber"],
                    "bankCode": payload["bankCode"],
                    "status": "Invalid",
                    "errorCode": error_data.get("code", "UNKNOWN"),
                    "errorMessage": error_data.get("message", str(e))
                }
            except Exception:
                # If can't parse JSON response
                return {
                    "accountNumber": payload["accountNumber"],
                    "bankCode": payload["bankCode"],
                    "status": "Invalid",
                    "errorCode": "ERROR",
                    "errorMessage": e.response.text
                }
        else:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Pesalink API error: {e.response.text}"
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )

async def validate_bulk_accounts(file: UploadFile) -> ApiResponse:
    """
    Validates multiple accounts from a CSV file
    
    Args:
        file (UploadFile): CSV file with account details
        
    Returns:
        ApiResponse: Object containing valid accounts, invalid accounts, and summary
    """
    start_time = time.time()
    
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
        # Parse CSV file
        data = await parse_csv(file)
        
        if not data:
            raise ValueError("CSV file is empty or contains no valid rows")
        
        valid_accounts = []
        invalid_accounts = []
        
        # Process each account
        async with httpx.AsyncClient(timeout=30.0) as client:
            for row in data:
                try:
                    # Ensure required fields are present
                    if "accountNumber" not in row or "bankCode" not in row:
                        invalid_accounts.append(AccountError(
                            accountNumber=row.get("accountNumber", "Unknown"),
                            bankCode=row.get("bankCode", "Unknown"),
                            errorCode="MISSING_FIELDS",
                            errorMessage="Account number or bank code missing"
                        ))
                        continue
                    
                    # Call validation API
                    res = await client.post(f"{PESALINK_BASE}/api/validate", json=row)
                    res.raise_for_status()
                    result = res.json()
                    
                    # Add to valid accounts
                    valid_accounts.append(AccountResponse(**result))
                    
                except httpx.HTTPStatusError as e:
                    # Handle API validation errors
                    try:
                        error_data = e.response.json()
                        invalid_accounts.append(AccountError(
                            accountNumber=row.get("accountNumber", "Unknown"),
                            bankCode=row.get("bankCode", "Unknown"),
                            errorCode=error_data.get("code", "API_ERROR"),
                            errorMessage=error_data.get("message", str(e))
                        ))
                    except Exception:
                        # If can't parse JSON response
                        invalid_accounts.append(AccountError(
                            accountNumber=row.get("accountNumber", "Unknown"),
                            bankCode=row.get("bankCode", "Unknown"),
                            errorCode="API_ERROR",
                            errorMessage=e.response.text
                        ))
                except Exception as e:
                    # Handle other exceptions during processing
                    invalid_accounts.append(AccountError(
                        accountNumber=row.get("accountNumber", "Unknown"),
                        bankCode=row.get("bankCode", "Unknown"),
                        errorCode="PROCESSING_ERROR",
                        errorMessage=str(e)
                    ))
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create summary
        total = len(data)
        valid_count = len(valid_accounts)
        invalid_count = len(invalid_accounts)
        
        summary = ValidationSummary(
            total=total,
            valid=valid_count,
            invalid=invalid_count,
            processingTime=round(processing_time, 2)
        )
        
        # Return complete response
        return ApiResponse(
            valid=valid_accounts,
            invalid=invalid_accounts,
            summary=summary
        )
        
    except Exception as e:
        # Handle exceptions from CSV parsing or other errors
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")