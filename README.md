# Resume Analyzer API

Upload a resume PDF and job description → get AI-powered match analysis.

## Endpoints
POST /analyze — returns match_score, strengths, missing_skills, suggestions

## Setup
pip install fastapi uvicorn pymupdf openai python-dotenv
Add OPENAI_API_KEY to .env
uvicorn main:app --reload
