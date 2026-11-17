
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


# Load environment variables
load_dotenv(override=True)


def get_llm():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. "
            "Please configure it inside your .env file."
        )

    model_name = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b"
    )

    llm = ChatGroq(
        model=model_name,
        temperature=0.8,
        max_tokens=500,
        api_key=api_key
    )

    return llm
