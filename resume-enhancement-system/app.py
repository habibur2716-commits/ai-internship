import os
import re
import streamlit as st
import requests
from PyPDF2 import PdfReader
from fpdf import FPDF
from dotenv import load_dotenv
from urllib.parse import urlparse

from agents.crew_setup import build_crew

# Load .env file variables
load_dotenv()

st.set_page_config(page_title="Resume Enhancement System", layout="wide")
st.title("📄 Resume Enhancement & Interview Prep System")

# ---------------- SIDEBAR ----------------
st.sidebar.header("Settings")

gemini_key_input = st.sidebar.text_input(
    "Gemini API Key (optional override)", type="password"
)

serper_key_input = st.sidebar.text_input(
    "Serper API Key (optional override)", type="password"
)

model_choice = st.sidebar.selectbox(
    "Select Model",
    ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.1-pro"],
)

# Use sidebar key if given, otherwise fallback to .env
gemini_api_key = gemini_key_input or os.getenv("GEMINI_API_KEY")
serper_api_key = serper_key_input or os.getenv("SERPER_API_KEY")


# ---------------- HELPER FUNCTIONS ----------------

def scrape_job_posting(url, api_key):
    """Uses Serper's scrape endpoint to fetch job posting page content.
    Returns (text, error_message). If successful, error_message is None."""
    endpoint = "https://scrape.serper.dev"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {"url": url}
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        text = data.get("text", "")

        if not text or len(text.strip()) < 100:
            return None, "The scraper couldn't extract enough content from this page."

        return text, None

    except requests.exceptions.Timeout:
        return None, "The job site took too long to respond (timeout)."
    except requests.exceptions.RequestException as e:
        return None, f"Couldn't scrape this job posting (the site may be blocking automated access)."


def extract_resume_text(uploaded_file):
    """Extracts raw text from an uploaded PDF resume using PyPDF2."""
    temp_path = "uploaded_resume.pdf"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    reader = PdfReader(temp_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
        if len(text.strip()) < 50:
            os.remove(temp_path)
            raise ValueError("Couldn't extract text from this PDF. It may be a scanned image — please upload a text-based PDF instead.")

    # Save extracted text too (per requirements doc)
    with open("candidate_resume.txt", "w", encoding="utf-8") as f:
        f.write(text)

    return text, temp_path

def is_valid_job_url(url):
    """Checks if the given string is a well-formed http/https URL."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False

def is_valid_pdf(uploaded_file):
    """Checks if the uploaded file is a real, parseable PDF (not corrupt)."""
    try:
        uploaded_file.seek(0)
        reader = PdfReader(uploaded_file)
        _ = len(reader.pages)  # forces PyPDF2 to actually parse the structure
        uploaded_file.seek(0)  # reset pointer so later code can read it again
        return True
    except Exception:
        return False    


def cleanup_temp_files():
    for fname in ["uploaded_resume.pdf", "candidate_resume.txt"]:
        if os.path.exists(fname):
            os.remove(fname)


def sanitize_text(text):
    """Cleans text but KEEPS markdown symbols (#, *, -) since we now parse them."""
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "→": "->", "…": "...",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = text.encode("latin-1", "ignore").decode("latin-1")
    return text


def split_bold_segments(line):
    """Splits a line into (text, is_bold) chunks based on **bold** markers."""
    parts = re.split(r"(\*\*.*?\*\*)", line)
    segments = []
    for part in parts:
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            segments.append((part[2:-2], True))
        elif part:
            segments.append((part, False))
    return segments


def print_wrapped(pdf, segments, base_size, max_width, line_height=7):
    """Prints a list of (text, is_bold) segments, word-wrapping manually,
    switching font style per word so bold text renders as real bold."""
    x_start = pdf.l_margin
    x = pdf.get_x()

    for text, is_bold in segments:
        words = text.split(" ")
        for i, word in enumerate(words):
            if word == "" and i != len(words) - 1:
                word = " "
            style = "B" if is_bold else ""
            pdf.set_font("Helvetica", style=style, size=base_size)
            piece = word + (" " if i != len(words) - 1 else "")
            piece_width = pdf.get_string_width(piece)

            if x + piece_width > pdf.w - pdf.r_margin:
                pdf.ln(line_height)
                x = x_start
                pdf.set_x(x_start)

            pdf.cell(piece_width, line_height, piece)
            x += piece_width

    pdf.ln(line_height)


def generate_pdf(result_text, output_path="resume_improvement_plan.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_font("Helvetica", size=11)

    max_width = pdf.w - pdf.l_margin - pdf.r_margin
    clean_text = sanitize_text(result_text)

    for raw_line in clean_text.split("\n"):
        line = raw_line.strip()

        if line == "":
            pdf.ln(3)
            continue

        # Heading level 2: "## Heading"
        if line.startswith("## "):
            pdf.ln(2)
            text = line[3:].strip()
            print_wrapped(pdf, [(text, True)], base_size=15, max_width=max_width, line_height=9)
            pdf.ln(1)
            continue

        # Heading level 3: "### Heading"
        if line.startswith("### "):
            pdf.ln(1)
            text = line[4:].strip()
            print_wrapped(pdf, [(text, True)], base_size=13, max_width=max_width, line_height=8)
            continue

        # Bullet point: "- text" or "1. text"
        bullet_match = re.match(r"^(-|\d+\.)\s+(.*)", line)
        if bullet_match:
            bullet_text = bullet_match.group(2)
            pdf.set_x(pdf.l_margin + 5)
            pdf.set_font("Helvetica", size=11)
            pdf.cell(5, 7, "-")
            segments = split_bold_segments(bullet_text)
            print_wrapped(pdf, segments, base_size=11, max_width=max_width - 10, line_height=7)
            continue

        # Normal paragraph line (may contain **bold** inline)
        pdf.set_x(pdf.l_margin)
        segments = split_bold_segments(line)
        print_wrapped(pdf, segments, base_size=11, max_width=max_width, line_height=7)

    pdf.output(output_path)
    return output_path

def truncate_text(text, max_chars=12000, label="text"):
    """Truncates very long text before sending to the AI, with a visible warning."""
    if len(text) > max_chars:
        st.warning(f"⚠️ The {label} was quite long, so it was trimmed to the first {max_chars} characters before processing.")
        return text[:max_chars]
    return text


# ---------------- MAIN UI ----------------

job_url = st.text_input("Job Posting URL")
resume_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

run_button = st.button("Generate Resume Improvement Plan")

# Initialize session state (persists across reruns)
if "job_text" not in st.session_state:
    st.session_state.job_text = None
if "awaiting_manual_job_text" not in st.session_state:
    st.session_state.awaiting_manual_job_text = False

if run_button:
    # Reset state for a fresh run
    st.session_state.job_text = None
    st.session_state.awaiting_manual_job_text = False

    if not job_url or not resume_file:
        st.error("Please provide both a job URL and a resume PDF.")
    elif not is_valid_job_url(job_url):
        st.error("That doesn't look like a valid URL. Please enter a full link starting with http:// or https://")
    elif not is_valid_pdf(resume_file):
        st.error("This file doesn't look like a valid PDF. Please upload a proper, non-corrupted PDF resume.")
    elif not gemini_api_key or not serper_api_key:
        st.error("Missing API key(s). Please add them in the sidebar or your .env file.")
    else:
        with st.spinner("Scraping job posting..."):
            job_text, scrape_error = scrape_job_posting(job_url, serper_api_key)

        if scrape_error:
            st.warning(f"⚠️ {scrape_error}")
            st.session_state.awaiting_manual_job_text = True
        else:
            st.session_state.job_text = job_text

# If scraping failed, show manual paste box (this stays visible across reruns)
if st.session_state.awaiting_manual_job_text:
    st.info("You can paste the job description manually below instead.")
    manual_text = st.text_area("Paste job description here:", key="manual_job_input")
    if st.button("Use this description"):
        if manual_text.strip():
            st.session_state.job_text = manual_text
            st.session_state.awaiting_manual_job_text = False
            st.rerun()
        else:
            st.error("Please paste some text first.")

# Once we have job_text (either scraped or manually pasted), run the pipeline
if st.session_state.job_text and resume_file:
    try:
        with st.spinner("Extracting resume text..."):
            resume_text, temp_pdf_path = extract_resume_text(resume_file)

        job_text = truncate_text(job_text, max_chars=12000, label="job description")
        resume_text = truncate_text(resume_text, max_chars=12000, label="resume")

        with st.spinner("Running AI agents... this may take a minute"):
            crew = build_crew(
                job_text=st.session_state.job_text,
                resume_text=resume_text,
                model_name=model_choice,
                api_key=gemini_api_key,
            )
            result = crew.kickoff()

        st.success("Done! Here's your result:")
        st.write(str(result))

        pdf_path = generate_pdf(str(result))
        with open(pdf_path, "rb") as f:
            st.download_button(
                "Download PDF Report",
                f,
                file_name="resume_improvement_plan.pdf",
            )

        st.session_state.job_text = None  # reset so it doesn't re-run automatically

    except Exception as e:
        st.error(f"Something went wrong: {e}")

    finally:
        cleanup_temp_files()