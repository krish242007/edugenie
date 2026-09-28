import logging
from pydantic import BaseModel, Field, field_validator
from gemini_service import gemini_service
import config

logger = logging.getLogger("edugenie.qna")

class QnARequest(BaseModel):
    question: str = Field(..., description="The academic or educational question to answer.")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty or only whitespace.")
        if len(cleaned) > config.MAX_QUESTION_LENGTH:
            raise ValueError(f"Question is too long (maximum {config.MAX_QUESTION_LENGTH} characters).")
        return cleaned


class QnAResponse(BaseModel):
    question: str
    answer: str
    status: str = "success"


QNA_SYSTEM_INSTRUCTION = (
    "You are EduGenie, an expert AI educational assistant for students and self-learners.\n"
    "Guidelines:\n"
    "1. Answer accurately and directly.\n"
    "2. Use student-friendly, clear, and engaging language.\n"
    "3. Keep your answers concise yet comprehensive.\n"
    "4. Explain important terminology simply when it appears.\n"
    "5. Use concrete real-world examples or analogies when helpful.\n"
    "6. Never invent or hallucinate facts.\n"
    "7. If the question is ambiguous or lacks necessary context, briefly state your assumption or ask a clarifying question while providing the most helpful educational answer.\n"
    "8. Format key concepts cleanly with bullet points or bold text where appropriate for easy reading."
)


def answer_question(question: str) -> QnAResponse:
    """Processes an educational question and returns a concise, student-friendly answer."""
    prompt = f"Student Question: {question}\n\nPlease provide a clear, accurate, and concise educational explanation."
    answer = gemini_service.generate_text(
        prompt=prompt,
        system_instruction=QNA_SYSTEM_INSTRUCTION,
        temperature=0.4
    )
    return QnAResponse(question=question, answer=answer)
