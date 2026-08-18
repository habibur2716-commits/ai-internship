import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai.llm import LLM

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# LLM Setup - konsa AI model use karna hai
llm = LLM(
    model="gemini/gemini-3.6-flash",
    api_key=api_key
)

# AGENT 1: Researcher
researcher = Agent(
    role="Senior Researcher",
    goal="AI ke fayde ke baare mein accurate aur detailed information dhoondna",
    backstory="Tum ek experienced researcher ho jo technology topics mein 10 saal ka tajarba rakhte ho. Tum hamesha factual aur clear information dete ho.",
    llm=llm
)

# AGENT 2: Writer
writer = Agent(
    role="Content Writer",
    goal="Research se ek acha, aasan samajh aane wala article likhna",
    backstory="Tum ek skilled content writer ho jo complex information ko simple aur interesting tareeqe se likh sakte ho.",
    llm=llm
)

# TASK 1: Research Karna
research_task = Task(
    description="AI (Artificial Intelligence) ke top 3 fayde dhoondo, students ke liye",
    expected_output="AI ke 3 fayde, har ek 1-2 lines mein",
    agent=researcher
)

# TASK 2: Article Likhna
writing_task = Task(
    description="Researcher ki di hui information se ek 100-word article likho, students ke liye",
    expected_output="Ek 100-word ka acha article",
    agent=writer,
    context=[research_task]  # Ye pehle task ka result use karega
)

# CREW: Sab ko jodna
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task]
)

# Crew ko chalana
result = crew.kickoff()
print("\n\nFINAL RESULT:\n")
print(result)