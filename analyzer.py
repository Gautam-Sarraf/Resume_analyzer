from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)