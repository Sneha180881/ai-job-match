from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import os
import json
import PyPDF2
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


load_dotenv()

app = Flask(__name__)

# Initialize Gemini Client using the GEMINI_API_KEY environment variable loaded via python-dotenv
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class JobMatchAnalysis(BaseModel):
    match_score: int = Field(ge=0, le=100, description="Match score integer between 0 and 100")
    matching_skills: list[str] = Field(description="Array of matching skills")
    missing_skills: list[str] = Field(description="Array of missing skills")
    experience_match: str = Field(description="Summary of experience match")
    gaps: list[str] = Field(description="Array of gaps identified")
    recommendations: list[str] = Field(description="Array of practical recommendations based on identified gaps")


class ImprovedSection(BaseModel):
    section: str = Field(description="Name or title of the resume section to improve (e.g. Summary, Experience, Skills, Education, Projects)")
    suggestion: str = Field(description="Specific suggestion to improve wording, clarity, presentation of existing experience, or what to learn/add in the future")


class ResumeImprovementResponse(BaseModel):
    improved_sections: list[ImprovedSection] = Field(description="List of suggested improvements for resume sections")


class MatchExplanationResponse(BaseModel):
    explanation: str = Field(description="Beginner-friendly explanation of why the candidate received the given match score based only on the supplied resume, job description, and analysis")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/ai/test", methods=["GET"])
def test_ai():
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents="ping",
        )
        if response and response.text:
            return jsonify({
                "success": True,
                "message": "Gemini API connection working"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Gemini API connection failed"
            }), 500
    except Exception:
        return jsonify({
            "success": False,
            "message": "Gemini API connection failed"
        }), 500


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid JSON or missing body"
        }), 400

    resume = data.get("resume")
    job_description = data.get("job_description")

    # Validation: resume is required and must contain non-whitespace text
    if resume is None or not isinstance(resume, str) or not resume.strip():
        return jsonify({
            "success": False,
            "message": "resume is required and must contain non-whitespace text"
        }), 400

    # Validation: job_description is required and must contain non-whitespace text
    if job_description is None or not isinstance(job_description, str) or not job_description.strip():
        return jsonify({
            "success": False,
            "message": "job_description is required and must contain non-whitespace text"
        }), 400

    prompt = f"""You are an AI job matching assistant.
Compare the candidate's resume against the supplied job description.
Evaluate ONLY information explicitly present in the supplied resume and job description.

Do not invent:
- Skills
- Work experience
- Education
- Certifications
- Projects

Evaluate the match and provide:
- match_score: integer from 0 to 100
- matching_skills: array of strings
- missing_skills: array of strings
- experience_match: string
- gaps: array of strings
- recommendations: array of strings based only on the identified gaps

Candidate's Resume:
{resume.strip()}

Job Description:
{job_description.strip()}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobMatchAnalysis,
            ),
        )

        if response.parsed and isinstance(response.parsed, JobMatchAnalysis):
            analysis = response.parsed
        elif response.text:
            analysis = JobMatchAnalysis.model_validate_json(response.text)
        else:
            raise ValueError("Empty or invalid response from AI")

        # Ensure validation constraints are fully satisfied
        analysis = JobMatchAnalysis.model_validate(analysis)

        return jsonify({
            "success": True,
            "match_score": analysis.match_score,
            "matching_skills": analysis.matching_skills,
            "missing_skills": analysis.missing_skills,
            "experience_match": analysis.experience_match,
            "gaps": analysis.gaps,
            "recommendations": analysis.recommendations
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "AI response validation failed"
        }), 502


@app.route("/api/improve-resume", methods=["POST"])
def improve_resume():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid JSON or missing body"
        }), 400

    resume = data.get("resume")
    # Validation: resume is required and must contain non-whitespace text
    if resume is None or not isinstance(resume, str) or not resume.strip():
        return jsonify({
            "success": False,
            "message": "resume is required and must contain non-whitespace text"
        }), 400

    gaps = data.get("gaps", [])
    if not isinstance(gaps, list):
        gaps = [str(gaps)]

    recommendations = data.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)]

    prompt = f"""You are an expert resume improvement coach.
Suggest improvements to the candidate's resume based ONLY on the provided gaps and recommendations.

CRITICAL RULES:
Never invent:
- work experience
- projects
- skills
- certifications
- education
- achievements

The AI may:
- improve wording
- improve clarity
- suggest where existing experience could be presented better
- suggest what the student should learn or add in the future

Candidate's Resume:
{resume.strip()}

Identified Gaps:
{json.dumps(gaps)}

Recommendations:
{json.dumps(recommendations)}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResumeImprovementResponse,
            ),
        )

        if response.parsed and isinstance(response.parsed, ResumeImprovementResponse):
            improvement = response.parsed
        elif response.text:
            improvement = ResumeImprovementResponse.model_validate_json(response.text)
        else:
            raise ValueError("Empty or invalid response from AI")

        improvement = ResumeImprovementResponse.model_validate(improvement)

        return jsonify({
            "success": True,
            "improved_sections": [
                {
                    "section": item.section,
                    "suggestion": item.suggestion
                }
                for item in improvement.improved_sections
            ]
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Resume improvement failed"
        }), 502


@app.route("/api/explain-match", methods=["POST"])
def explain_match():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid JSON or missing body"
        }), 400

    resume = data.get("resume")
    if resume is None or not isinstance(resume, str) or not resume.strip():
        return jsonify({
            "success": False,
            "message": "resume is required and must contain non-whitespace text"
        }), 400

    job_description = data.get("job_description")
    if job_description is None or not isinstance(job_description, str) or not job_description.strip():
        return jsonify({
            "success": False,
            "message": "job_description is required and must contain non-whitespace text"
        }), 400

    analysis = data.get("analysis")
    if analysis is None or not isinstance(analysis, dict):
        return jsonify({
            "success": False,
            "message": "analysis object is required"
        }), 400

    prompt = f"""You are an AI career coach explaining a job match assessment to a candidate.
Explain clearly and in beginner-friendly language why the candidate received the given match score.

CRITICAL RULES:
- Base your explanation ONLY on the supplied resume, job description, and analysis.
- Do NOT recalculate or change the score.
- Do NOT invent any skills, experience, qualifications, or information.
- Mention the candidate's strongest matches.
- Explain the most important gaps identified.
- Explain what the candidate could improve based on the recommendations.

Candidate's Resume:
{resume.strip()}

Job Description:
{job_description.strip()}

Match Analysis:
Match Score: {analysis.get('match_score', 'N/A')}
Matching Skills: {json.dumps(analysis.get('matching_skills', []))}
Missing Skills: {json.dumps(analysis.get('missing_skills', []))}
Experience Match: {analysis.get('experience_match', '')}
Gaps: {json.dumps(analysis.get('gaps', []))}
Recommendations: {json.dumps(analysis.get('recommendations', []))}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MatchExplanationResponse,
            ),
        )

        if response.parsed and isinstance(response.parsed, MatchExplanationResponse):
            result = response.parsed
        elif response.text:
            result = MatchExplanationResponse.model_validate_json(response.text)
        else:
            raise ValueError("Empty or invalid response from AI")

        result = MatchExplanationResponse.model_validate(result)

        return jsonify({
            "success": True,
            "explanation": result.explanation
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Match explanation failed"
        }), 502


@app.route("/api/extract-resume", methods=["POST"])
def extract_resume():
    # 1. Verify that a file was provided
    if "resume_pdf" in request.files:
        file = request.files["resume_pdf"]
    elif "resume" in request.files:
        file = request.files["resume"]
    elif "file" in request.files:
        file = request.files["file"]
    elif len(request.files) > 0:
        file = next(iter(request.files.values()))
    else:
        file = None

    if not file or file.filename == "":
        return jsonify({
            "success": False,
            "message": "Resume PDF is required"
        }), 400

    # 2. Verify that the file has a .pdf extension
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({
            "success": False,
            "message": "Only PDF files are allowed"
        }), 400

    # 3. Extract readable text from the PDF
    try:
        reader = PyPDF2.PdfReader(file.stream)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        extracted_text = "\n".join(text_parts).strip()

        if not extracted_text:
            return jsonify({
                "success": False,
                "message": "could not extract text from PDF"
            }), 400

        return jsonify({
            "success": True,
            "resume_text": extracted_text
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "could not extract text from PDF"
        }), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)







