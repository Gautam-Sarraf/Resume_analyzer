# from openai import OpenAI
# from dotenv import load_dotenv
# import os
# import json

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from google import genai
from dotenv import load_dotenv
import os
import json
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
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    return json.loads(response.text)