from crewai import Agent, Task, Crew, Process
from crewai import LLM


def build_crew(job_text, resume_text, model_name="gpt-3.5-turbo", api_key=None):
    """
    job_text: scraped job posting text
    resume_text: text extracted from user's resume PDF
    model_name: model selected in Streamlit sidebar
    api_key: OpenAI key (from .env or sidebar override)
    """

    llm = LLM(model=f"gemini/{model_name}", api_key=api_key, temperature=0.3)

    # --- Agent 1: Skills Analyzer ---
    skills_analyzer = Agent(
        role="Skills Analyzer",
        goal="Extract required technical and soft skills from a job posting",
        backstory="You are an expert recruiter who reads job postings and extracts exactly what skills, tools, and qualifications are required.",
        llm=llm,
        verbose=True,
    )

    task_skills = Task(
        description=f"Read this job posting and extract a structured list of required technical skills, tools, and soft skills:\n\n{job_text}",
        expected_output="A clear bullet list separated into 'Technical Skills' and 'Soft Skills'.",
        agent=skills_analyzer,
    )

    # --- Agent 2: Resume Enhancement Expert ---
    resume_expert = Agent(
        role="Resume Enhancement Expert",
        goal="Compare the candidate's resume against required job skills and suggest concrete improvements",
        backstory="You are a professional resume writer who improves resumes to match job descriptions using the right keywords and structure.",
        llm=llm,
        verbose=True,
    )

    task_resume = Task(
        description=f"Compare this resume against the extracted skills list. Identify missing or underrepresented skills, and give concrete suggestions to improve wording, keywords, and structure.\n\nResume:\n{resume_text}",
        expected_output="A list of missing skills, plus specific rewrite suggestions for resume bullet points.",
        agent=resume_expert,
        context=[task_skills],
    )

    # --- Agent 3: HR Questions Agent ---
    hr_agent = Agent(
        role="HR Interview Coach",
        goal="Generate likely behavioral/HR interview questions with sample answers",
        backstory="You are an HR interviewer who prepares candidates for soft-skill and culture-fit interview rounds.",
        llm=llm,
        verbose=True,
    )

    task_hr = Task(
        description="Generate 5 likely behavioral/HR interview questions (teamwork, conflict resolution, motivation) relevant to this role, each with a sample answer.",
        expected_output="5 HR questions, each followed by a sample answer.",
        agent=hr_agent,
        context=[task_skills],
    )

    # --- Agent 4: Coding Test Agent (DSA) ---
    dsa_agent = Agent(
        role="DSA Practice Coach",
        goal="Generate data structures & algorithms practice problems matching the role's seniority",
        backstory="You are a technical interviewer who prepares candidates with DSA problems matched to the job level.",
        llm=llm,
        verbose=True,
    )

    task_dsa = Task(
        description="Generate 5 DSA practice problems appropriate to this job's seniority level, with a note on which practice platform (LeetCode/HackerRank) to find similar problems.",
        expected_output="5 DSA problems with difficulty level and platform suggestion.",
        agent=dsa_agent,
        context=[task_skills],
    )

    # --- Agent 5: Technical Test Agent ---
    tech_agent = Agent(
        role="Technical Interviewer",
        goal="Generate technical questions personalized to the candidate's own resume skills",
        backstory="You are a technical interviewer who asks questions based specifically on what the candidate claims to know on their resume.",
        llm=llm,
        verbose=True,
    )

    task_tech = Task(
        description=f"Based on the skills mentioned in this resume, generate 5 technical interview questions specific to those skills:\n\n{resume_text}",
        expected_output="5 technical questions tailored to the candidate's resume skills.",
        agent=tech_agent,
    )

    # --- Agent 6: Final Interview Agent ---
    final_agent = Agent(
        role="Final Round Coach",
        goal="Prepare the candidate for company-fit questions and salary negotiation",
        backstory="You prepare candidates for the final interview round, covering company-fit and negotiation strategy.",
        llm=llm,
        verbose=True,
    )

    task_final = Task(
        description="Generate 3 company-fit questions and brief salary negotiation guidance relevant to this role's seniority.",
        expected_output="3 company-fit questions plus a short salary negotiation tip section.",
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