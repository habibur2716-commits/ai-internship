from crewai import Agent, Task, Crew, Process, LLM


def build_crew(job_text, resume_text, model_name="gemini-3.5-flash-lite", api_key=None):
    """
    model_name: the "fast/cheap" model selected in the sidebar — used for simpler tasks.
    A stronger model is always used for tasks that need deeper reasoning
    (Resume Enhancement Expert, Technical Test Agent), regardless of sidebar choice.
    """

    fast_llm = LLM(model=f"gemini/{model_name}", api_key=api_key, temperature=0.3)
    strong_llm = LLM(model="gemini/gemini-3.1-pro", api_key=api_key, temperature=0.3)

    # --- Agent 1: Skills Analyzer (fast model — straightforward extraction) ---
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

    # --- Agent 2: Resume Enhancement Expert (strong model — needs real comparison/reasoning) ---
    resume_expert = Agent(
        role="Resume Enhancement Expert",
        goal="Compare the candidate's resume against required job skills and suggest concrete improvements",
        backstory="You are a professional resume writer who improves resumes to match job descriptions using the right keywords and structure.",
        llm=strong_llm,
        verbose=True,
    )

    task_resume = Task(
        description=(
            f"Compare this resume against the extracted skills list. Resume:\n{resume_text}\n\n"
            "Format your response EXACTLY like this:\n"
            "## Missing Skills\n"
            "- skill: why it matters for this role\n\n"
            "## Suggested Improvements\n"
            "1. Original line -> Improved line (with a one-sentence reason)\n"
            "...\n\n"
            "Give at least 3 concrete before/after suggestions. Be specific, not generic."
        ),
        expected_output="A markdown response with 'Missing Skills' and 'Suggested Improvements' sections, with concrete before/after examples.",
        agent=resume_expert,
        context=[task_skills],
    )

    # --- Agent 3: HR Questions Agent (fast model — templated Q&A) ---
    hr_agent = Agent(
        role="HR Interview Coach",
        goal="Generate likely behavioral/HR interview questions with sample answers",
        backstory="You are an HR interviewer who prepares candidates for soft-skill and culture-fit interview rounds.",
        llm=fast_llm,
        verbose=True,
    )

    task_hr = Task(
        description=(
            "Generate exactly 5 behavioral/HR interview questions (teamwork, conflict resolution, motivation) "
            "relevant to this role. Format EXACTLY like this, repeated 5 times:\n\n"
            "### Q1: [question]\n**Sample Answer:** [answer]\n\n"
        ),
        expected_output="Exactly 5 numbered questions, each with a '### Q#:' heading and a bolded 'Sample Answer:' line.",
        agent=hr_agent,
        context=[task_skills],
    )

    # --- Agent 4: Coding Test Agent (fast model) ---
    dsa_agent = Agent(
        role="DSA Practice Coach",
        goal="Generate data structures & algorithms practice problems matching the role's seniority",
        backstory="You are a technical interviewer who prepares candidates with DSA problems matched to the job level.",
        llm=fast_llm,
        verbose=True,
    )

    task_dsa = Task(
        description=(
            "Generate exactly 5 DSA practice problems appropriate to this job's seniority level. "
            "Format EXACTLY like this, repeated 5 times:\n\n"
            "### Problem 1: [name]\n**Difficulty:** [Easy/Medium/Hard]\n**Practice on:** [LeetCode/HackerRank + suggested search term]\n\n"
        ),
        expected_output="Exactly 5 problems, each with name, difficulty, and a practice platform suggestion.",
        agent=dsa_agent,
        context=[task_skills],
    )

    # --- Agent 5: Technical Test Agent (strong model — needs to reason over resume specifics) ---
    tech_agent = Agent(
        role="Technical Interviewer",
        goal="Generate technical questions personalized to the candidate's own resume skills",
        backstory="You are a technical interviewer who asks questions based specifically on what the candidate claims to know on their resume.",
        llm=strong_llm,
        verbose=True,
    )

    task_tech = Task(
        description=(
            f"Based on the skills mentioned in this resume, generate exactly 5 technical interview questions "
            f"specific to those skills:\n\n{resume_text}\n\n"
            "Format EXACTLY like this, repeated 5 times:\n\n"
            "### Q1: [question]\n**Tests:** [which specific resume skill this checks]\n\n"
        ),
        expected_output="Exactly 5 technical questions, each tied to a specific skill from the resume.",
        agent=tech_agent,
    )

    # --- Agent 6: Final Interview Agent (fast model) ---
    final_agent = Agent(
        role="Final Round Coach",
        goal="Prepare the candidate for company-fit questions and salary negotiation",
        backstory="You prepare candidates for the final interview round, covering company-fit and negotiation strategy.",
        llm=fast_llm,
        verbose=True,
    )

    task_final = Task(
        description=(
            "Generate exactly 3 company-fit questions, then a short salary negotiation section. "
            "Format EXACTLY like this:\n\n"
            "## Company-Fit Questions\n"
            "### Q1: [question]\n**Why they ask:** [reason]\n\n(repeat for Q2, Q3)\n\n"
            "## Salary Negotiation Tips\n"
            "- tip 1\n- tip 2\n- tip 3\n"
        ),
        expected_output="A markdown response with 'Company-Fit Questions' (3 Q&A pairs) and 'Salary Negotiation Tips' (bullet list) sections.",
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