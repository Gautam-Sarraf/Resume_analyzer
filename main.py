from typing import Optional, Union

import fitz
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
)
from starlette.datastructures import UploadFile as StarletteUploadFile
from fastapi.middleware.cors import CORSMiddleware

from analyzer import analyze_resume as run_analysis

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {
        "status": "running",
        "service": "resume-analyzer"
    }


@app.post("/analyze")
async def analyze(
    resume_text: Optional[str] = Form(None),
    resume_file: Union[UploadFile, str, None] = File(None),
    job_description_text: Optional[str] = Form(None),
    job_description_file: Union[UploadFile, str, None] = File(None),
):
    # -------------------------
    # Extract Resume Content
    # -------------------------
    resume_content = ""
    # 1. Prioritize a valid UploadFile if one was actually uploaded
    if isinstance(resume_file, StarletteUploadFile) and resume_file.filename and resume_file.filename.strip():
        if not resume_file.content_type.startswith("application/pdf"):
            raise HTTPException(
                status_code=400,
                detail="Resume file must be a PDF"
            )
        pdf_bytes = await resume_file.read()
        doc = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )
        resume_content = "\n".join(
            page.get_text()
            for page in doc
        ).strip()
    # 2. Fall back to resume_text
    elif resume_text and resume_text.strip():
        resume_content = resume_text.strip()
    # 3. Fall back to resume_file if it was sent as a raw text string
    elif isinstance(resume_file, str) and resume_file.strip():
        resume_content = resume_file.strip()

    if not resume_content:
        raise HTTPException(
            status_code=400,
            detail="Provide either resume text or resume file"
        )

    # -------------------------
    # Extract Job Description
    # -------------------------
    job_description = ""
    # 1. Prioritize a valid UploadFile if one was actually uploaded
    if isinstance(job_description_file, StarletteUploadFile) and job_description_file.filename and job_description_file.filename.strip():
        if not job_description_file.content_type.startswith("application/pdf"):
            raise HTTPException(
                status_code=400,
                detail="Job description file must be a PDF"
            )
        pdf_bytes = await job_description_file.read()
        doc = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )
        job_description = "\n".join(
            page.get_text()
            for page in doc
        ).strip()
    # 2. Fall back to job_description_text
    elif job_description_text and job_description_text.strip():
        job_description = job_description_text.strip()
    # 3. Fall back to job_description_file if it was sent as a raw text string
    elif isinstance(job_description_file, str) and job_description_file.strip():
        job_description = job_description_file.strip()

    if not job_description:
        raise HTTPException(
            status_code=400,
            detail="Provide either job description text or job description file"
        )

    # -------------------------
    # Run Analysis
    # -------------------------
    try:
        result = run_analysis(
            resume_content,
            job_description
        )
        return result
    except Exception as e:
        status_code = 500
        # If it's an APIError, it might have a code / status_code attribute
        err_code = getattr(e, "code", None) or getattr(e, "status_code", None)
        if err_code and isinstance(err_code, int):
            status_code = err_code
        
        detail_msg = getattr(e, "message", str(e))
        raise HTTPException(
            status_code=status_code,
            detail=f"Analysis service error: {detail_msg}"
        )