from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class AccountRequest(BaseModel):
    """
    Model representing a bank account validation request
    """
    accountNumber: str = Field(..., description="Account number to validate")
    bankCode: str = Field(..., description="Bank code identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "accountNumber": "123456789012",
                "bankCode": "01"
            }
        }

class AccountResponse(BaseModel):
    """
    Model representing a successful account validation response
    """
    accountNumber: str
    bankCode: str
    status: str
    accountHolderName: str
    bankName: str
    currency: str

class AccountError(BaseModel):
    """
    Model representing an account validation error
    """
    accountNumber: str
    bankCode: str
    errorCode: str
    errorMessage: str

class ValidationSummary(BaseModel):
    """
    Summary of bulk validation process
    """
    total: int
    valid: int
    invalid: int
    processingTime: float

class ApiResponse(BaseModel):
    """
    Complete API response for bulk validation
    """
    valid: List[AccountResponse] = []
    invalid: List[AccountError] = []
    summary: ValidationSummary