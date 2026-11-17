
from langchain_core.prompts import ChatPromptTemplate

from src.llm import get_llm


def rewrite_speech(
    transcript: str,
    style: str
) -> str:

    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty.")

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are an expert English language coach
            and professional speech editor.

            Your task is to improve the user's spoken English.

            Follow these rules carefully:

            1. Correct all grammatical mistakes.
            2. Improve vocabulary where appropriate.
            3. Improve sentence structure and clarity.
            4. Make the speech sound natural when spoken aloud.
            5. Preserve the original meaning and intentions.
            6. Do not invent facts, examples or experiences.
            7. Do not unnecessarily increase the length.
            8. Do not turn a simple speech into an essay.
            9. Preserve the user's personality and main ideas.
            10. Return ONLY the rewritten speech.

            The requested communication style is: {style}

            Style guidelines:

            Professional:
            Clear, polished and suitable for professional situations.

            Friendly:
            Warm, approachable and natural.

            Formal:
            Grammatically precise and respectful.

            Conversational:
            Natural everyday English that sounds comfortable
            when spoken aloud.

            Academic:
            Structured, articulate and suitable for academic
            discussions and formal presentations.
            """
        ),
        (
            "human",
            """
            Rewrite the following spoken transcript.

            Original speech:
            {transcript}
            """
        )
    ])

    chain = prompt | llm

    response = chain.invoke({
        "transcript": transcript,
        "style": style
    })

    result = response.content

    if isinstance(result, list):
        result = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in result
        )

    result = result.strip()

    if not result:
        raise ValueError("The model returned an empty response.")

    return result
