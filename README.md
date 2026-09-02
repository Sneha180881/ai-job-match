# AI Job Match Assistant

An intelligent, web-based career tool designed to analyze resumes against job descriptions, evaluate compatibility, provide actionable resume improvements, and explain match scores using Google Gemini AI with structured outputs.

---

## Features

- **PDF Resume Text Extraction**: Upload a resume in PDF format to extract and populate text directly into an editable editor.
- **Comprehensive Match Analysis**: Evaluates resume text against job descriptions to produce:
  - Overall Match Score (0–100%)
  - Matching Skills & Missing Skills
  - Experience Match summary
  - Identified Gaps & Actionable Recommendations
- **Targeted Resume Improvements**: Generates section-by-section suggestions (Summary, Experience, Skills, Projects, etc.) based strictly on identified gaps without fabricating qualifications.
- **Match Explanation**: Provides a beginner-friendly explanation detailing why a particular match score was awarded.
- **Structured AI Validation**: Enforces strict Pydantic schemas on Gemini AI responses for reliable JSON output.

---

## Tech Stack

- **Backend**: Python 3.10+, Flask
- **AI & LLM**: Google GenAI SDK (`google-genai`), Gemini 3.6 Flash (`gemini-3.6-flash`), Pydantic v2
- **PDF Processing**: PyPDF2
- **Frontend**: HTML5, CSS3, Modern JavaScript (Vanilla Fetch API)
- **Configuration**: `python-dotenv`

---

## Project Structure

```text
ai-job-match/
├── app.py              # Flask server, routes, and Gemini API integration
├── requirements.txt    # Project dependencies
├── sample_resume.pdf   # Sample resume for testing
├── templates/
│   └── index.html      # Frontend user interface
└── README.md           # Documentation
```

---

## Setup and Configuration

### 1. Prerequisites
- Python 3.10 or higher
- A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone / Open Project
Navigate to the project root directory:
```bash
cd ai-job-match
```

### 3. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Variables (`.env`)
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## How to Run

Start the Flask development server:
```bash
python app.py
```

Once running, access the web interface at:
```text
http://127.0.0.1:5000
```

---

## How to Use

1. **Provide Resume**:
   - Click **Choose File** to select a `.pdf` resume and click **Upload PDF**, or
   - Paste resume plain text directly into the **Resume** textarea.
2. **Provide Job Description**:
   - Paste the job posting or description into the **Job Description** textarea.
3. **Analyze Match**:
   - Click **Analyze Match** to generate the Match Report.
4. **Improve Resume**:
   - Click **Improve My Resume** below the Match Report to view suggested improvements tailored to missing skills and gaps.
5. **Explain Match**:
   - Click **Explain My Match** below the Match Report to view a plain-language summary explaining the score and breakdown.

---

## API Endpoints

| Method | Endpoint | Description | Request Payload / Format |
|---|---|---|---|
| `GET` | `/` | Web application interface | None |
| `GET` | `/api/ai/test` | Verifies Gemini API connectivity | None |
| `POST` | `/api/extract-resume` | Extracts text from uploaded PDF | `multipart/form-data` (`resume_pdf` file) |
| `POST` | `/api/analyze` | Generates job match analysis | `application/json`: `{"resume": "...", "job_description": "..."}` |
| `POST` | `/api/improve-resume` | Generates section improvement advice | `application/json`: `{"resume": "...", "gaps": [...], "recommendations": [...]}` |
| `POST` | `/api/explain-match` | Generates narrative explanation | `application/json`: `{"resume": "...", "job_description": "...", "analysis": {...}}` |

---

## Security Note

- **API Key Protection**: Never commit `.env` files or expose your `GEMINI_API_KEY` in version control repositories.
- **Git Ignore**: Ensure `.env` and virtual environment folders (`venv/`, `__pycache__/`) are listed in `.gitignore`.
- **Key Restrictions**: For production deployments, apply API key restrictions within Google Cloud Console / Google AI Studio.

---

## Future Improvements

- Support for additional resume formats (`.docx`, `.txt`, `.rtf`).
- Export and download options for updated resumes (Markdown and PDF).
- Match history tracking with SQLite / PostgreSQL persistence.
- Configurable matching criteria weights (e.g., prioritize experience vs. education/skills).
- ATS (Applicant Tracking System) keyword optimization score and suggestions.
