from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load env
load_dotenv()

app = FastAPI()

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "practice_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


class ParseRequest(BaseModel):
    text: str
    llm: str


class ParseResponse(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    found_in_database: bool
    company: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    database: str


def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")


def extract_contact_with_llm(text: str, llm: str) -> dict:
    
    system_prompt = """ Extract contact information from the given text.
                        Return a JSON object with these fields:
                        - name: The person's full name (string or null)
                        - email: The email address (string or null)
                        - phone: The phone number (string or null)

                        Return ONLY the JSON object, no other text. If a field is not present, use null.
                        Example: {"name": "John Doe", "email": "john@example.com", "phone": "555-1234"}
                    """

    try:
        if llm in ["gemini-2.5-flash", "gemini-2.5-flash-preview"]:
            model = genai.GenerativeModel(
                model_name=llm,
                generation_config={
                    "temperature": 0,
                    "response_mime_type": "application/json",
                }
            )
            
            prompt = f"{system_prompt}\n\nText: {text}"
            response = model.generate_content(prompt)
            
            result = json.loads(response.text)
            
            return {
                "name": result.get("name"),
                "email": result.get("email"),
                "phone": result.get("phone"),
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported LLM: {llm}")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse LLM response as JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {str(e)}")


def check_contact_in_database(name: Optional[str]) -> tuple[bool, Optional[str]]:
    if not name:
        return False, None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # split the name into parts
        name_parts = name.strip().split(None, 1)
        if len(name_parts) == 2:
            first_name, last_name = name_parts
        elif len(name_parts) == 1:
            first_name = name_parts[0]
            last_name = ""
        else:
            return False, None
        
        # query for the contact
        query = """
            SELECT c.*, co.name as company_name
            FROM contacts c
            LEFT JOIN companies co ON c.company_id = co.company_id
            WHERE LOWER(c.first_name) = LOWER(%s)
            AND LOWER(c.last_name) = LOWER(%s)
        """
        cursor.execute(query, (first_name, last_name))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return True, result.get("company_name")
        else:
            return False, None
            
    except Exception as e:
        print(f"Database query error: {e}")
        return False, None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return HealthResponse(status="ok", database="connected")
    except Exception as e:
        return HealthResponse(status="ok", database=f"error: {str(e)}")


@app.post("/parse", response_model=ParseResponse)
async def parse_contact(request: ParseRequest):
    extracted = extract_contact_with_llm(request.text, request.llm)
    
    # Database check
    found_in_db, company = check_contact_in_database(extracted["name"])
    
    return ParseResponse(
        name=extracted["name"],
        email=extracted["email"],
        phone=extracted["phone"],
        found_in_database=found_in_db,
        company=company
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
