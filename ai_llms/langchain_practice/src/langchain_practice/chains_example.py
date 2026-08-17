import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=api_key)
prompt = ChatPromptTemplate.from_template("Translate this English text to Urdu: {text}")
output_parser = StrOutputParser()

# Chain banana
chain = prompt | llm | output_parser

result = chain.invoke({"text": "Hello, how are you?"})
print(result)