import pandas as pd
import io
from fastapi import UploadFile, HTTPException
from typing import List, Dict, Any


async def parse_csv(file: UploadFile) -> List[Dict[str, Any]]:
    """
    Parse a CSV file containing bank account information.
    
    Handles various CSV formats and column names, normalizing them
    to the expected format for the validation API.
    
    Args:
        file (UploadFile): The uploaded CSV file
        
    Returns:
        List[Dict[str, Any]]: List of account records with standardized field names
        
    Raises:
        ValueError: If CSV is missing required columns or is empty
        HTTPException: If file cannot be read or parsed
    """
    try:
        # Read the file contents
        contents = await file.read()
        
        # Check if file is empty
        if not contents:
            raise ValueError("Uploaded CSV file is empty")
        
        # Parse CSV using pandas
        df = pd.read_csv(io.BytesIO(contents))
        
        # Check if DataFrame is empty
        if df.empty:
            raise ValueError("CSV file contains no data")
        
        # Clean column names (strip whitespace, handle case variations)
        df.columns = [col.strip() for col in df.columns]
        
        # Map common column name variations to standard names
        column_mapping = {
            # Account number variations
            'account number': 'accountNumber',
            'account_number': 'accountNumber',
            'accountnumber': 'accountNumber',
            'account': 'accountNumber',
            'acc number': 'accountNumber',
            'acc no': 'accountNumber',
            'accno': 'accountNumber',
            
            # Bank code variations
            'bank code': 'bankCode',
            'bank_code': 'bankCode',
            'bankcode': 'bankCode',
            'bank': 'bankCode',
            'bank id': 'bankCode',
            'bank_id': 'bankCode',
        }
        
        # Replace column names using case-insensitive matching
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in column_mapping:
                df = df.rename(columns={col: column_mapping[col_lower]})
        
        # Check for required columns after mapping
        if 'accountNumber' not in df.columns:
            # Check if "Account Number" exists (with capital letters)
            if 'Account Number' in df.columns:
                df = df.rename(columns={'Account Number': 'accountNumber'})
            else:
                raise ValueError("CSV file must contain an 'Account Number' column")
                
        if 'bankCode' not in df.columns:
            # Check if "Bank Code" exists (with capital letters)
            if 'Bank Code' in df.columns:
                df = df.rename(columns={'Bank Code': 'bankCode'})
            else:
                raise ValueError("CSV file must contain a 'Bank Code' column")
        
        # Convert all values to strings to ensure consistency for the API
        df['accountNumber'] = df['accountNumber'].astype(str)
        df['bankCode'] = df['bankCode'].astype(str)
        
        # Remove rows with missing values in required fields
        df = df.dropna(subset=['accountNumber', 'bankCode'])
        
        # Convert DataFrame to list of dictionaries
        records = df.to_dict(orient='records')
        
        return records
        
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty or contains no data")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Unable to parse CSV file. Please check the format.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")