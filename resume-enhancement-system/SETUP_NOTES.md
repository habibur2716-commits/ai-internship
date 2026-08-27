# Setup Notes — Resume Enhancement System (Phase 1)

## Environment
- OS: Windows
- Python virtual environment: `venv` (standard `venv` module, not Poetry)
- IDE: VS Code

## Steps Taken

1. Created project folder `resume-enhancement-system`, initialized with `git init`.
2. Created virtual environment: `python -m venv venv`, activated with `venv\Scripts\activate`.
3. Created `requirements.txt` with core dependencies (streamlit, crewai, langchain-openai,
   PyPDF2, fpdf2, requests, python-dotenv) and installed with `pip install -r requirements.txt`.
4. Built the app from scratch based on the requirements document (no existing repo was provided).
   Structure: `app.py` (Streamlit UI + pipeline orchestration) and `agents/crew_setup.py`
   (all 6 CrewAI agents + tasks + crew definition).
5. Obtained a Serper API key (reused from a previous project) and a Gemini API key.

## Manual Fixes Required

### 1. LLM Provider Changed: OpenAI → Gemini
- Original requirements specified `langchain-openai` / OpenAI models.
- Got approval from senior to use Gemini instead (OpenAI's free trial credits are no longer
  reliably available for new accounts as of 2026).
- Fix: Used `crewai.LLM` (CrewAI's native LLM class, which wraps LiteLLM) instead of
  `langchain_openai.ChatOpenAI`. Model string format: `f"gemini/{model_name}"`.
- Sidebar model list changed from GPT-3.5/GPT-4/GPT-4-turbo to Gemini equivalents.

### 2. CrewAI + LangChain ChatOpenAI Incompatibility
- Installed CrewAI version (1.15.17) does not accept a LangChain `ChatOpenAI` object directly
  as `llm=` — raised a Pydantic validation error (`llm.str` / `llm.BaseLLM` type errors).
- Fix: switched to `crewai.LLM(model=..., api_key=..., temperature=...)`.

### 3. Missing Gemini Provider Package
- Error: `Google Gen AI native provider not available`.
- Fix: `pip install "crewai[google-genai]"`.

### 4. Gemini Model Deprecation
- `gemini-2.5-flash-lite` returned a 404 — no longer available to new users.
- Fix: switched sidebar models to `gemini-3.5-flash-lite`, `gemini-3.6-flash`, `gemini-3.1-pro`
  (current models as of Aug 2026). Note: model availability changes frequently — check
  Google's model list if this breaks again.

### 5. fpdf2 "Not enough horizontal space to render a single character"
- This is a known fpdf2 bug (GitHub issue #1250) where `multi_cell()`'s internal auto-wrap
  fails on text with many small fragments (e.g. markdown symbols like `**bold**`, smart quotes,
  em-dashes from AI-generated text).
- Fix: (a) sanitize AI output — strip markdown symbols (`*`, `#`) and replace smart
  quotes/dashes with plain ASCII equivalents, (b) replaced `multi_cell()` with a manual
  word-wrapping function using `pdf.get_string_width()` to measure and wrap lines ourselves,
  avoiding fpdf2's buggy auto-wrap entirely.
- Trade-off: PDF output is currently plain text with no bold/headings, since markdown symbols
  are stripped rather than rendered. Proper formatting (bold headings, sections) is a Phase 5
  task.

### 6. VS Code Auto-Creating Duplicate `.venv-1`
- VS Code occasionally auto-triggered creation of a second virtual environment (`.venv-1`)
  with a malformed path, causing `CommandNotFoundException` in PowerShell.
- Fix: deleted `.venv-1` manually (`Remove-Item -Recurse -Force .venv-1`) and continued using
  the original `venv`.

## Result
Successfully completed one full run: job URL + resume PDF → all 6 agents ran → PDF report
generated and downloaded via the Streamlit UI.

## Time Taken
_(add roughly how long Phase 1 took you, e.g. "~1 day including debugging")_

## Known Limitations (to address in later phases)
- API keys pinned in `requirements.txt` are not yet version-pinned (Phase 2).
- No input validation yet for bad URLs / non-PDF uploads (Phase 2).
- PDF has no formatting (headings, bold) — plain text only (Phase 5).
- Only tested against one job posting and one resume so \sfar — broader testing is Phase 3.\s