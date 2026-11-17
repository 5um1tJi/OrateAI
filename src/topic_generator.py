
from langchain_core.prompts import ChatPromptTemplate

from src.llm import get_llm


def generate_topic(category: str, difficulty: str):

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are an expert English speaking coach.

            Your job is to generate interesting speaking
            topics that help people improve their English.

            Generate exactly ONE speaking topic.

            Rules:
            - The topic must match the requested category.
            - The topic must match the requested difficulty.
            - Make it interesting and engaging.
            - Avoid overly common or boring topics.
            - Keep the topic suitable for spontaneous speaking.
            - Do not provide an answer to the topic.
            - Do not generate multiple topics.

            Return only the topic and nothing else.
            """
        ),
        (
            "human",
            """
            Category: {category}
            Difficulty: {difficulty}

            Generate one speaking topic.
            """
        )
    ])

    chain = prompt | llm

    response = chain.invoke({
        "category": category,
        "difficulty": difficulty
    })

    return response.content.strip()
