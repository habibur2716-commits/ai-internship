from crewai import Agent, Task, Crew, Process, LLM


def build_crew(job_text, resume_text, model_name="gemini-3.5-flash-lite", api_key=None):
    fast_llm = LLM(model=f"gemini/{model_name}", api_key=api_key, temperature=0.4)
    strong_llm = LLM(model="gemini/gemini-3.5-flash", api_key=api_key, temperature=0.4)

    TONE_INSTRUCTION = (
        "Write in a warm, encouraging, easy-to-understand tone — like a helpful mentor "
        "talking directly to the candidate. Avoid stiff corporate language and jargon. "
        "Keep sentences clear and direct. Use 'you' to address the candidate directly."
    )

    # --- Agent 1: Skills Analyzer ---
    skills_analyzer = Agent(
        role="Skills Analyzer",
        goal="Extract required technical and soft skills from a job posting",
        backstory="You are an expert recruiter who reads job postings and extracts exactly what skills, tools, and qualifications are required.",
        llm=fast_llm,
        verbose=True,
    )

    task_skills = Task(
        description=(
            f"Read this job posting and extract required skills:\n\n{job_text}\n\n"
            "Format your response EXACTLY like this:\n"
            "## Technical Skills\n"
            "- skill 1\n- skill 2\n...\n\n"
            "## Soft Skills\n"
            "- skill 1\n- skill 2\n...\n\n"
            "Do not add any other sections. Do not add commentary before or after the lists."
        ),
        expected_output="A markdown response with exactly two headed sections: 'Technical Skills' and 'Soft Skills', each a bullet list.",
        agent=skills_analyzer,
    )

    # --- Agent 2: Resume Enhancement Expert (THE MOST IMPORTANT AGENT) ---
    resume_expert = Agent(
        role="Resume Enhancement Expert",
        goal="Compare the candidate's resume against required job skills and suggest concrete improvements",
        backstory="You are a friendly, encouraging resume coach who helps candidates see exactly what to improve, in a way that feels supportive, not critical. This is the core service you provide, so you are always thorough and specific.",
        llm=strong_llm,
        verbose=True,
    )

    task_resume = Task(
        description=(
            f"Compare this resume against the extracted skills list. Resume:\n{resume_text}\n\n"
            f"{TONE_INSTRUCTION}\n\n"
            "This is the MOST IMPORTANT section of the whole report — the candidate is here mainly "
            "to find out what's missing from their resume. Be thorough and detailed, not brief.\n\n"
            "Format your response EXACTLY like this:\n\n"
            "## Skills You're Missing\n"
            "For EVERY skill from the job posting that is not clearly shown in the resume, write one entry:\n"
            "- **[skill name]** — [2-3 sentences: what this skill means for this specific role, why the "
            "employer cares about it, and a concrete way the candidate could gain it or better demonstrate "
            "it — e.g. a project idea, a certification, or reframing existing experience]\n\n"
            "List every gap you find (aim for at least 5 if the job posting has that many requirements). "
            "If very few gaps exist, say so clearly and highlight what's already well covered instead.\n\n"
            "## How to Improve Your Resume\n"
            "Give at least 5 concrete before/after rewrites:\n"
            "1. **Before:** \"[exact or close-to-exact original resume line]\"\n"
            "   **After:** \"[improved line]\"\n"
            "   **Why:** [1-2 sentences on why this is stronger and what it signals to a recruiter]\n"
            "(repeat this pattern for each suggestion)\n\n"
            "Be specific and reference actual content from the resume — avoid generic advice like "
            "'add more keywords' or 'be more specific'."
        ),
        expected_output="A detailed markdown response: 'Skills You're Missing' (at least 5 detailed entries with explanations) and 'How to Improve Your Resume' (at least 5 detailed before/after suggestions with reasons).",
        agent=resume_expert,
        context=[task_skills],
    )

    # --- Agent 3: HR Questions Agent ---
    hr_agent = Agent(
        role="HR Interview Coach",
        goal="Generate likely behavioral/HR interview questions with sample answers",
        backstory="You are a friendly HR interview coach who helps candidates feel confident and prepared, not nervous.",
        llm=fast_llm,
        verbose=True,
    )

    task_hr = Task(
        description=(
            f"Generate exactly 5 behavioral/HR interview questions (teamwork, conflict resolution, motivation) "
            f"relevant to this role. {TONE_INSTRUCTION}\n\n"
            "For each question, write a sample answer that is at least 3-4 sentences long using the "
            "STAR method (Situation, Task, Action, Result), so the candidate has a real template to build on, "
            "not just a one-liner.\n\n"
            "Format EXACTLY like this, repeated 5 times:\n\n"
            "### Q1: [question]\n"
            "**Why they ask this:** [1 sentence]\n"
            "**Sample Answer:** [3-4 sentences using the STAR method]\n\n"
        ),
        expected_output="Exactly 5 questions, each with a 1-sentence reason and a detailed 3-4 sentence STAR-method sample answer.",
        agent=hr_agent,
        context=[task_skills],
    )

    # --- Agent 4: Coding Test Agent (DSA) ---
    dsa_agent = Agent(
        role="DSA Practice Coach",
        goal="Generate data structures & algorithms practice problems matching the role's seniority",
        backstory="You are an encouraging technical coach who makes DSA practice feel approachable, not intimidating.",
        llm=fast_llm,
        verbose=True,
    )

    task_dsa = Task(
        description=(
            f"Generate exactly 5 DSA practice problems appropriate to this job's seniority level. "
            f"{TONE_INSTRUCTION}\n\n"
            "For each problem, briefly explain (1-2 sentences) what concept it tests and why it's relevant "
            "to this role, not just the problem name.\n\n"
            "Format EXACTLY like this, repeated 5 times:\n\n"
            "### Problem 1: [name]\n"
            "**Difficulty:** [Easy/Medium/Hard]\n"
            "**What it tests:** [1-2 sentences on the underlying concept and why it matters for this role]\n"
            "**Practice on:** [LeetCode/HackerRank + a suggested search term]\n\n"
        ),
        expected_output="Exactly 5 problems, each with name, difficulty, a short explanation of what it tests, and a practice platform suggestion.",
        agent=dsa_agent,
        context=[task_skills],
    )

    # --- Agent 5: Technical Test Agent ---
    tech_agent = Agent(
        role="Technical Interviewer",
        goal="Generate technical questions personalized to the candidate's own resume skills",
        backstory="You are a supportive technical interviewer who wants to help the candidate showcase what they know.",
        llm=strong_llm,
        verbose=True,
    )

    task_tech = Task(
        description=(
            f"Based on the skills mentioned in this resume, generate exactly 5 technical interview questions "
            f"specific to those skills:\n\n{resume_text}\n\n"
            f"{TONE_INSTRUCTION}\n\n"
            "For each question, also give a short pointer (2-3 sentences) on what a strong answer should "
            "cover, so the candidate can prepare, not just guess.\n\n"
            "Format EXACTLY like this, repeated 5 times:\n\n"
            "### Q1: [question]\n"
            "**Tests:** [which specific resume skill this checks]\n"
            "**What a strong answer covers:** [2-3 sentences]\n\n"
        ),
        expected_output="Exactly 5 technical questions, each tied to a specific resume skill, with a short guide on what a strong answer covers.",
        agent=tech_agent,
    )

    # --- Agent 6: Final Interview Agent ---
    final_agent = Agent(
        role="Final Round Coach",
        goal="Prepare the candidate for company-fit questions and salary negotiation",
        backstory="You are a warm, confidence-building coach helping the candidate walk into their final round feeling ready.",
        llm=fast_llm,
        verbose=True,
    )

    task_final = Task(
        description=(
            f"Generate exactly 3 company-fit questions, then a salary negotiation section. "
            f"{TONE_INSTRUCTION}\n\n"
            "For each company-fit question, explain why it's asked AND give a 2-3 sentence tip on how "
            "to approach answering it.\n\n"
            "Format EXACTLY like this:\n\n"
            "## Company-Fit Questions\n"
            "### Q1: [question]\n"
            "**Why they ask:** [1 sentence]\n"
            "**How to approach it:** [2-3 sentences]\n"
            "(repeat for Q2, Q3)\n\n"
            "## Salary Negotiation Tips\n"
            "Give at least 5 practical tips, each 1-2 sentences with a concrete example or script where useful:\n"
            "- tip 1\n- tip 2\n- tip 3\n- tip 4\n- tip 5\n"
        ),
        expected_output="A detailed markdown response with 3 company-fit Q&A pairs (each with reasoning and approach tips) and at least 5 detailed salary negotiation tips.",
        agent=final_agent,
        context=[task_skills],
    )

    crew = Crew(
        agents=[skills_analyzer, resume_expert, hr_agent, dsa_agent, tech_agent, final_agent],
        tasks=[task_skills, task_resume, task_hr, task_dsa, task_tech, task_final],
        process=Process.sequential,
        verbose=True,
    )

    return crew