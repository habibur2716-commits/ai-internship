# Developer Notes

Notes for anyone maintaining or extending this project.

## Project Structure

resume-enhancement-system/
├── app.py # Streamlit UI + orchestration (scraping, parsing, PDF gen)
├── agents/
│ └── crew_setup.py # All 6 CrewAI agents, tasks, and the crew pipeline
├── requirements.txt # Pinned dependencies
├── .env.example # Template for required environment variables
└── docs (SETUP_NOTES.md, COMPATIBILITY_LIST.md, TEST_CHECKLIST.md)


## Agent Pipeline

The pipeline runs sequentially (`Process.sequential` in `crew_setup.py`):

1. **Skills Analyzer** — extracts skills from the job posting. Runs first; its output
   feeds into the Resume Enhancement Expert and most other agents via `context=[...]`.
2. **Resume Enhancement Expert** — compares resume vs. skills. Uses the *strong* LLM.
3. **HR Questions Agent** — behavioral questions. Uses the *fast* LLM.
4. **Coding Test Agent (DSA)** — practice problems. Uses the *fast* LLM.
5. **Technical Test Agent** — resume-specific technical questions. Uses the *strong* LLM.
6. **Final Interview Agent** — company-fit + salary negotiation. Uses the *fast* LLM.

Two `LLM` instances are created in `build_crew()`: `fast_llm` (whatever model is selected
in the sidebar) and `strong_llm` (hardcoded to a stronger model). This split exists because
Resume Enhancement and Technical Test questions need deeper reasoning over specific resume
content, while the other agents mostly generate templated Q&A.

## Adding a New Agent

1. Define the `Agent` in `crew_setup.py` (role, goal, backstory, llm).
2. Define its `Task` with a strict output format in `description` (the pipeline relies on
   consistent markdown structure — `##`/`###` headings and `- `/`1. ` bullets — for the PDF
   renderer in `app.py` to work correctly).
3. Add `context=[...]` if it needs another agent's output.
4. Add the agent and task to the `agents=[...]` and `tasks=[...]` lists in `Crew(...)`,
   keeping both lists in the same order.

## PDF Generation (`app.py`)

The PDF renderer (`generate_pdf()` and helpers) is a **manual markdown parser**, not a
generic library. It specifically expects:
- `## Heading` and `### Subheading` lines
- `**bold**` inline text
- `- item` or `1. item` bullet lines

If agent prompts stop following this format, PDF formatting will silently degrade (headings
will just print as plain bold-less text). Keep task `description` fields strict about format
if you edit them.

Note: `multi_cell()` from fpdf2 is intentionally avoided due to a known library bug
(see `SETUP_NOTES.md`, Phase 1). Text wrapping is done manually via `print_wrapped()`.

## Known Fragile Points

- **Gemini model names change often.** If you get a `404` on a model name, check the error
  message — it usually tells you the replacement model ID.
- **Free-tier quota is limited**, especially for "Pro"-tier models. Some models return
  `429 RESOURCE_EXHAUSTED` with `limit: 0` on the free tier — this means the model isn't
  available at all on free tier, not a temporary rate limit.
- **Serper scraping fails on some sites** (Indeed, Google Careers, Bayt.com as of testing).
  This is expected — the manual paste fallback in `app.py` handles it.