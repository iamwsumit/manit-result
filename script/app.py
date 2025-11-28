from fastapi import FastAPI, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
import httpx
import base64
import json
from datetime import datetime

app = FastAPI(title="Student Result API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def decode_jwt_payload(jwt_token: str) -> dict:
    try:
        parts = jwt_token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT token format")
        
        payload = parts[1]
        padding = len(payload) % 4
        if padding:
            payload += "=" * (4 - padding)
        
        decoded = base64.b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode JWT token: {str(e)}"
        )

async def fetch_student_result(jwt_token: str, student_uid: str) -> dict:
    
    url = "https://erpapi.manit.ac.in/api/student_result"
    headers = {
        "Authorization": jwt_token,
        "Content-Type": "application/json",
    }
    payload = {
        "studentuid": student_uid,
        "programID": 80,
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch student result: {str(e)}"
            )

@app.get("/")
async def fetch_result(token: str = Header(...)):
    
    if token is None or token.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JWT token is required in the Authorization header"
        )
    
    payload = decode_jwt_payload(token)
    student_uid = payload.get("studentuid")
    
    if not student_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="studentuid not found in JWT token"
        )
    
    result_data = await fetch_student_result(token, student_uid)
    
    if result_data.get("status") != "success":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch student result from college API"
        )
    
    return result_data

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
