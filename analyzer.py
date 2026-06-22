from google import genai
from google.genai import errors
from dotenv import load_dotenv
import os
import json
import time
import logging

# Configure logging
logger = logging.getLogger("resume_analyzer")
logging.basicConfig(level=logging.INFO)

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_resume(resume_text: str, job_description: str) -> dict:
    prompt = f"""
You are an expert recruiter. Analyze this resume against the job description.

Resume:
{resume_text}

Job Description:
{job_description}

Respond with ONLY a valid JSON object with exactly these keys:
- match_score: integer from 0 to 100
- strengths: list of strings (what the candidate does well)
- missing_skills: list of strings (skills in the JD but not in the resume)
- suggestions: list of strings (specific ways to improve the resume for this role)
"""
    # List of models to try in sequence if we hit temporary server errors or limits
    models_to_try = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemma-4-31b-it"
    ]
    
    last_exception = None
    
    for model_name in models_to_try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting analysis with model {model_name} (attempt {attempt + 1}/{max_retries})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                
                # Try to parse response
                try:
                    return json.loads(response.text)
                except (json.JSONDecodeError, TypeError, AttributeError) as parse_err:
                    logger.error(f"Failed to parse JSON response from model {model_name}: {parse_err}")
                    if attempt < max_retries - 1:
                        sleep_time = 2 ** attempt
                        time.sleep(sleep_time)
                        continue
                    else:
                        break
                        
            except errors.APIError as e:
                last_exception = e
                status_code = getattr(e, "code", None) or getattr(e, "status_code", None)
                message = getattr(e, "message", str(e))
                
                logger.warning(
                    f"Google GenAI APIError with model {model_name} on attempt {attempt + 1}: "
                    f"Status {status_code}, Message: {message}"
                )
                
                # If it's a client error (e.g., 400 Bad Request, 403 Forbidden, 401 Unauthorized), 
                # do not retry or switch models as this is non-transient.
                if status_code and 400 <= status_code < 500 and status_code not in (408, 429):
                    raise e
                
                # For transient/server errors (5xx, 429 rate limit, 408 timeout), we retry
                if attempt < max_retries - 1:
                    sleep_time = 2 ** attempt
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error with model {model_name}: {str(e)}")
                if attempt < max_retries - 1:
                    sleep_time = 2 ** attempt
                    time.sleep(sleep_time)
                else:
                    break
        else:
            logger.warning(f"Model {model_name} failed all {max_retries} attempts. Trying fallback model...")
            
    # If we exited the loop and haven't returned, raise the last exception
    if last_exception:
        raise last_exception
    raise RuntimeError("Analysis failed: all models and retries exhausted.")