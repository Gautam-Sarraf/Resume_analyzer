from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import fitz
from analyzer import analyze_resume as run_analysis

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def health():
    return {"status": "running", "service": "resume-analyzer"}

@app.post("/analyze")
async def analyze(resume: UploadFile = File(...), job_description: str = Form(...)):
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    pdf_bytes = await resume.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    resume_text = "\n".join(page.get_text() for page in doc)

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    return run_analysis(resume_text, job_description)