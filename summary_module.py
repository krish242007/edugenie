import logging
import math
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from gemini_service import gemini_service
import config

logger = logging.getLogger("edugenie.summary")

class SummaryRequest(BaseModel):
    text: str = Field(..., description="Educational text passage to summarize.")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < config.MIN_TEXT_LENGTH:
            raise ValueError(f"Please provide at least {config.MIN_TEXT_LENGTH} characters for summarization.")
        if len(cleaned) > config.MAX_TEXT_LENGTH:
            raise ValueError(f"Text is too long (maximum {config.MAX_TEXT_LENGTH} characters).")
        return cleaned


class ImportantTerm(BaseModel):
    term: str
    definition: str


class SummaryResponse(BaseModel):
    main_summary: str
    key_points: List[str]
    important_terms: List[ImportantTerm]
    original_word_count: int
    summary_word_count: int
    reading_time_saved_minutes: float
    status: str = "success"


SUMMARY_SYSTEM_INSTRUCTION = (
    "You are EduGenie's Summarization Specialist. Your goal is to synthesize educational texts into "
    "clear, crystal-focused, and high-retention summaries for students.\n"
    "Rules:\n"
    "1. Preserve core concepts, factual accuracy, and crucial arguments.\n"
    "2. Remove fluff, unnecessary tangents, and rhetorical repetition.\n"
    "3. NEVER introduce outside facts or hallucinations not present or directly implied in the source.\n"
    "4. Use accessible, student-friendly language.\n"
    "5. Return output in structured JSON format with:\n"
    "   - 'main_summary': A coherent, well-structured 2-4 sentence narrative overview.\n"
    "   - 'key_points': A list of 3-6 distinct bullet takeaways.\n"
    "   - 'important_terms': A list of key terms and their context definitions."
)


def summarize_text(text: str) -> SummaryResponse:
    """Summarizes educational text, extracting core summary, key bullet points, and key terms."""
    original_words = len(text.split())

    prompt = (
        f"Please summarize the following educational text:\n"
        f"\"\"\"\n{text}\n\"\"\"\n\n"
        "Return structured JSON:\n"
        "{\n"
        '  "main_summary": "...",\n'
        '  "key_points": ["Point 1", "Point 2", "Point 3"],\n'
        '  "important_terms": [\n'
        '    {"term": "Term 1", "definition": "Brief definition based on text"}\n'
        "  ]\n"
        "}"
    )

    try:
        data = gemini_service.generate_json(
            prompt=prompt,
            system_instruction=SUMMARY_SYSTEM_INSTRUCTION,
            temperature=0.2
        )

        main_summary = data.get("main_summary", "Summary of the provided text.")
        raw_key_points = data.get("key_points", [])
        key_points = [str(p).strip() for p in raw_key_points if str(p).strip()]

        raw_terms = data.get("important_terms", [])
        terms: List[ImportantTerm] = []
        for t in raw_terms:
            if isinstance(t, dict) and "term" in t and "definition" in t:
                terms.append(ImportantTerm(term=str(t["term"]), definition=str(t["definition"])))
            elif isinstance(t, str) and ":" in t:
                parts = t.split(":", 1)
                terms.append(ImportantTerm(term=parts[0].strip(), definition=parts[1].strip()))

        summary_words = len(main_summary.split()) + sum(len(kp.split()) for kp in key_points)
        words_saved = max(0, original_words - summary_words)
        # Average reading speed is 200 words per minute
        reading_time_saved = round(words_saved / 200.0, 1)

        return SummaryResponse(
            main_summary=main_summary,
            key_points=key_points,
            important_terms=terms,
            original_word_count=original_words,
            summary_word_count=summary_words,
            reading_time_saved_minutes=reading_time_saved
        )

    except Exception as e:
        logger.warning("JSON summarization failed, falling back to text generation: %s", e)
        fallback_prompt = f"Summarize this educational text into a main summary and key bullet points:\n\n{text}"
        raw_text = gemini_service.generate_text(
            prompt=fallback_prompt,
            system_instruction=SUMMARY_SYSTEM_INSTRUCTION,
            temperature=0.3
        )
        return SummaryResponse(
            main_summary=raw_text,
            key_points=["Review the complete summary above."],
            important_terms=[],
            original_word_count=original_words,
            summary_word_count=len(raw_text.split()),
            reading_time_saved_minutes=0.0
        )
