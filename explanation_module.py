import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from gemini_service import gemini_service
import config

logger = logging.getLogger("edugenie.explain")

class ExplainRequest(BaseModel):
    topic: str = Field(..., description="The concept or topic to explain.")

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Topic cannot be empty.")
        if len(cleaned) > config.MAX_TOPIC_LENGTH:
            raise ValueError(f"Topic is too long (maximum {config.MAX_TOPIC_LENGTH} characters).")
        return cleaned


class ExplainStructured(BaseModel):
    simple_definition: str
    how_it_works: str
    key_concepts: List[str]
    simple_analogy: str
    real_world_example: str
    short_recap: str


class ExplainResponse(BaseModel):
    topic: str
    explanation: str
    structured: Optional[ExplainStructured] = None
    status: str = "success"


EXPLAIN_SYSTEM_INSTRUCTION = (
    "You are EduGenie, an expert educational teacher specialized in simplifying complex, difficult, "
    "or abstract concepts for complete beginners.\n"
    "When explaining a topic, you MUST structure your answer into exactly these 6 parts:\n"
    "1. Simple Definition: An intuitive, jargon-free 1-2 sentence definition.\n"
    "2. How It Works: A step-by-step breakdown of the core mechanics.\n"
    "3. Key Concepts: 3 to 5 fundamental terms or principles every student must know.\n"
    "4. Simple Analogy: A vivid, everyday analogy that makes the concept click instantly.\n"
    "5. Real-World Example: A tangible application showing why this matters in everyday life or technology.\n"
    "6. Short Recap: A memorable 1-sentence takeaway.\n"
    "Keep tone encouraging, insightful, and accessible to a student or beginner."
)


def explain_topic(topic: str) -> ExplainResponse:
    """Generates a structured, beginner-friendly explanation of a difficult concept."""
    json_prompt = (
        f"Topic to explain for a beginner: \"{topic}\"\n\n"
        "Return a JSON object with exactly these keys:\n"
        "{\n"
        '  "simple_definition": "...",\n'
        '  "how_it_works": "...",\n'
        '  "key_concepts": ["...", "...", "..."],\n'
        '  "simple_analogy": "...",\n'
        '  "real_world_example": "...",\n'
        '  "short_recap": "..."\n'
        "}"
    )

    try:
        data = gemini_service.generate_json(
            prompt=json_prompt,
            system_instruction=EXPLAIN_SYSTEM_INSTRUCTION,
            temperature=0.3
        )
        
        # Ensure all expected keys are present or provide fallback
        structured = ExplainStructured(
            simple_definition=data.get("simple_definition") or f"A beginner overview of {topic}.",
            how_it_works=data.get("how_it_works") or "Explanation of how it functions.",
            key_concepts=data.get("key_concepts") or ["Core principle 1", "Core principle 2"],
            simple_analogy=data.get("simple_analogy") or "An everyday mental model to visualize the concept.",
            real_world_example=data.get("real_world_example") or data.get("example") or "Practical usage in the real world.",
            short_recap=data.get("short_recap") or "Key summary."
        )

        # Build readable formatted markdown
        concepts_md = "\n".join([f"- **{c}**" if not c.startswith("-") else c for c in structured.key_concepts])
        explanation_md = (
            f"### 💡 Simple Definition\n{structured.simple_definition}\n\n"
            f"### ⚙️ How It Works\n{structured.how_it_works}\n\n"
            f"### 🔑 Key Concepts\n{concepts_md}\n\n"
            f"### 🌟 Everyday Analogy\n{structured.simple_analogy}\n\n"
            f"### 🌍 Real-World Example\n{structured.real_world_example}\n\n"
            f"### 📌 Short Recap\n{structured.short_recap}"
        )

        return ExplainResponse(
            topic=topic,
            explanation=explanation_md,
            structured=structured
        )

    except Exception as e:
        logger.warning("Structured JSON generation failed for explain, falling back to text: %s", e)
        # Fallback to direct text generation if JSON fails
        text_prompt = f"Please explain the topic \"{topic}\" simply for a beginner using the 6 core sections."
        explanation_text = gemini_service.generate_text(
            prompt=text_prompt,
            system_instruction=EXPLAIN_SYSTEM_INSTRUCTION,
            temperature=0.5
        )
        return ExplainResponse(
            topic=topic,
            explanation=explanation_text,
            structured=None
        )
