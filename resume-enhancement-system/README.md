# Resume Enhancement System & Interview Preparation

A Streamlit app that uses a CrewAI multi-agent pipeline to compare a resume against a job
posting, then generates personalized interview prep material and a downloadable PDF report.

## What It Does

Given a job posting URL and a resume PDF, the app:
1. Extracts required skills from the job posting
2. Compares them against the resume and suggests improvements
3. Generates HR/behavioral interview questions
4. Generates DSA practice problems matched to the role's seniority
5. Generates technical questions based on the candidate's own resume
6. Generates final-round company-fit questions and salary negotiation guidance
7. Compiles everything into a downloadable PDF

## Tech Stack

- **UI:** Streamlit
- **Agents:** CrewAI (6 agents, sequential pipeline)
- **LLM:** Gemini (via `crewai.LLM`) — free-tier models
- **Job scraping:** Serper API (`scrape.serper.dev`)
- **Resume parsing:** PyPDF2
- **PDF generation:** fpdf2 (with manual markdown-to-PDF rendering)

## Setup

### 1. Clone and enter the project folder
```bash
git clone https://github.com/habibur2716-commits/ai-internship.git
cd ai-internship/resume-enhancement-system
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up API keys
Copy `.env.example` to `.env` and fill in your keys:

- Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- Get a Serper API key from [serper.dev](https://serper.dev/)

Alternatively, keys can be entered directly in the app's sidebar (overrides `.env`).

### 5. Run the app
```bash
streamlit run app.py
```

## Model Notes

- The sidebar model dropdown selects the "fast" model used for simpler agents
  (HR Questions, DSA, Final Interview).
- The Resume Enhancement Expert and Technical Test agents always use a stronger model
  (`gemini-3.5-flash`) for better reasoning quality, regardless of sidebar selection.
- **Note:** Gemini model availability and naming changes frequently. If you get a `404`
  error, check the error message — Google's API typically tells you the replacement model
  name to use. See `SETUP_NOTES.md` for a history of model changes encountered during
  development.

## Job Site Compatibility

Tested against 10 real job postings. See `COMPATIBILITY_LIST.md` for full details.

Quick summary: LinkedIn, Microsoft Careers, Rozee.pk, Mustakbil.com, Wellfound, and Glassdoor
work with direct scraping. Indeed, Google Careers, and Bayt.com currently block scraping —
in these cases, the app shows a warning and lets you paste the job description manually.

## Known Limitations

- Scanned/image-based PDF resumes are not supported (no extractable text) — the app shows
  a clear error in this case rather than crashing.
- Job/resume text longer than 12,000 characters is automatically trimmed before processing.
- Free-tier Gemini API rate limits apply; heavy usage may hit `429` errors.

## Project Documentation

- `SETUP_NOTES.md` — setup steps and issues encountered during development
- `COMPATIBILITY_LIST.md` — job site scraping compatibility results
- `TEST_CHECKLIST.md` — manual test cases and results
- `CONTRIBUTING.md` — codebase structure notes for future maintainers