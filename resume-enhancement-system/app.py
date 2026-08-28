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
    """Uses Serper's scrape endpoint to fetch job posting page content."""
    endpoint = "https://scrape.serper.dev"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {"url": url}
    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("text", "")


def extract_resume_text(uploaded_file):
    """Extracts raw text from an uploaded PDF resume using PyPDF2."""
    temp_path = "uploaded_resume.pdf"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    reader = PdfReader(temp_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

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

import re

def sanitize_text(text):
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "→": "->", "•": "-", "…": "...",
        "*": "", "#": "",  # remove markdown symbols the AI adds
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = text.encode("latin-1", "ignore").decode("latin-1")
    return text


def wrap_line(pdf, line, max_width):
    """Manually builds wrapped lines using actual character widths,
    avoiding fpdf2's buggy internal multi_cell wrap algorithm."""
    words = line.split(" ")
    lines = []
    current = ""

    for word in words:
        # break any single word that's wider than the page itself
        while pdf.get_string_width(word) > max_width:
            for i in range(len(word), 0, -1):
                if pdf.get_string_width(word[:i]) <= max_width:
                    lines.append(word[:i])
                    word = word[i:]
                    break

        test = (current + " " + word).strip()
        if pdf.get_string_width(test) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)
    return lines if lines else [""]


def generate_pdf(result_text, output_path="resume_improvement_plan.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    max_width = pdf.w - pdf.l_margin - pdf.r_margin

    clean_text = sanitize_text(result_text)

    for raw_line in clean_text.split("\n"):
        if raw_line.strip() == "":
            pdf.ln(4)
            continue
        for wrapped in wrap_line(pdf, raw_line, max_width):
            pdf.cell(0, 8, wrapped, ln=1)

    pdf.output(output_path)
    return output_path
# ---------------- MAIN UI ----------------

job_url = st.text_input("Job Posting URL")
resume_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

run_button = st.button("Generate Resume Improvement Plan")

if run_button:
    if not job_url or not resume_file:
        st.error("Please provide both a job URL and a resume PDF.")
    elif not is_valid_job_url(job_url):
        st.error("That doesn't look like a valid URL. Please enter a full link starting with http:// or https://")
    elif not is_valid_pdf(resume_file):
        st.error("This file doesn't look like a valid PDF. Please upload a proper, non-corrupted PDF resume.")
    elif not gemini_api_key or not serper_api_key:
        st.error("Missing API key(s). Please add them in the sidebar or your .env file.")
    else:
        try:
            with st.spinner("Scraping job posting..."):
                job_text = scrape_job_posting(job_url, serper_api_key)

            with st.spinner("Extracting resume text..."):
                resume_text, temp_pdf_path = extract_resume_text(resume_file)

            with st.spinner("Running AI agents... this may take a minute"):
                crew = build_crew(
                    job_text=job_text,
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

        except Exception as e:
            st.error(f"Something went wrong: {e}")

        finally:
            cleanup_temp_files()