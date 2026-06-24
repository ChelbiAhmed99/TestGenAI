import os
from dotenv import load_dotenv
load_dotenv('backend/.env')

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def test_model(model_name):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("NO API KEY!")
        return
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.1)
        resp = llm.invoke([HumanMessage(content="Hello")])
        print(f"{model_name}: Success")
    except Exception as e:
        print(f"{model_name}: Error - {e}")

test_model("gemini-1.5-flash")
test_model("gemini-1.5-flash-latest")
test_model("gemini-2.0-flash")
