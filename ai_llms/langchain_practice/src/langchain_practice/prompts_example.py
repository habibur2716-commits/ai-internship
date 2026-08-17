from langchain_core.prompts import ChatPromptTemplate

# Template banana - {} mein jo bhi hoga, wo variable hai
prompt = ChatPromptTemplate.from_template(
    "Tum ek {role} ho. {topic} ke baare mein 2 lines mein batao."
)

# Template mein values bharna
final_prompt = prompt.invoke({"role": "history teacher", "topic": "Pakistan ki azaadi"})
print(final_prompt)