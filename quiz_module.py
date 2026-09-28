import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
from gemini_service import gemini_service
import config

logger = logging.getLogger("edugenie.quiz")

class QuizRequest(BaseModel):
    topic: Optional[str] = Field(None, description="Topic name to generate quiz from.")
    text: Optional[str] = Field(None, description="Educational passage or text to generate quiz from.")

    @model_validator(mode="after")
    def check_inputs(self):
        topic_clean = self.topic.strip() if self.topic else ""
        text_clean = self.text.strip() if self.text else ""
        
        if not topic_clean and not text_clean:
            raise ValueError("Please provide either a 'topic' or an educational 'text' passage to generate a quiz.")
        
        if topic_clean and len(topic_clean) > config.MAX_TOPIC_LENGTH:
            raise ValueError(f"Topic is too long (maximum {config.MAX_TOPIC_LENGTH} characters).")
            
        if text_clean and len(text_clean) > config.MAX_TEXT_LENGTH:
            raise ValueError(f"Text passage is too long (maximum {config.MAX_TEXT_LENGTH} characters).")
            
        self.topic = topic_clean if topic_clean else None
        self.text = text_clean if text_clean else None
        return self


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    questions: List[QuizQuestion]
    source: str
    status: str = "success"


QUIZ_SYSTEM_INSTRUCTION = (
    "You are EduGenie's Quiz Generator. Your goal is to test a student's conceptual comprehension "
    "with high-quality, unambiguous multiple-choice questions.\n"
    "Requirements:\n"
    "1. Generate EXACTLY 3 multiple-choice questions.\n"
    "2. Each question MUST have EXACTLY 4 options.\n"
    "3. Options should be plausible, distinct, and without leading letters like 'A)', 'B)'.\n"
    "4. 'correct_answer' MUST EXACTLY match one of the 4 items in 'options'.\n"
    "5. 'explanation' MUST clearly justify why the correct answer is right and why others are wrong.\n"
    "6. Output MUST be valid JSON adhering strictly to the requested schema."
)


def _clean_option_text(opt: str) -> str:
    """Removes leading 'A) ', '1. ', etc. if the model inadvertently added them."""
    opt = opt.strip()
    return re.sub(r"^[A-Da-d1-4][\.\)\:\-]\s*", "", opt)


def _normalize_questions(raw_questions: list) -> List[QuizQuestion]:
    """Validates and normalizes raw questions into valid Pydantic QuizQuestion models."""
    normalized: List[QuizQuestion] = []
    
    for idx, q_data in enumerate(raw_questions[:3]):
        try:
            q_text = str(q_data.get("question", f"Question {idx + 1}")).strip()
            raw_options = q_data.get("options", [])
            options = [_clean_option_text(str(opt)) for opt in raw_options if str(opt).strip()]
            
            # Ensure exactly 4 options
            while len(options) < 4:
                options.append(f"Alternative Option {len(options) + 1}")
            options = options[:4]
            
            raw_correct = _clean_option_text(str(q_data.get("correct_answer", options[0])))
            
            # Find the best match in options for correct_answer
            correct_match = None
            for opt in options:
                if opt.lower() == raw_correct.lower():
                    correct_match = opt
                    break
            if not correct_match:
                # If model returned an option number/index or partial string
                for opt in options:
                    if raw_correct.lower() in opt.lower() or opt.lower() in raw_correct.lower():
                        correct_match = opt
                        break
            if not correct_match:
                correct_match = options[0]

            explanation = str(q_data.get("explanation", f"The correct answer is: {correct_match}.")).strip()
            
            normalized.append(QuizQuestion(
                question=q_text,
                options=options,
                correct_answer=correct_match,
                explanation=explanation
            ))
        except Exception as err:
            logger.warning("Error normalizing question %d: %s", idx, err)

    if not normalized:
        raise ValueError("Could not parse valid quiz questions from the AI output.")

    # If fewer than 3 were returned, fill with fallback
    while len(normalized) < 3:
        n = len(normalized) + 1
        normalized.append(QuizQuestion(
            question=f"Review question {n} on the material.",
            options=["Option A", "Option B", "Option C", "Option D"],
            correct_answer="Option A",
            explanation="Review the provided topic or text for in-depth insights."
        ))

    return normalized[:3]


def generate_quiz(req: QuizRequest) -> QuizResponse:
    """Generates an interactive 3-question quiz from a topic or educational passage."""
    source_desc = f"Topic: {req.topic}" if req.topic else "Educational Passage"
    input_content = req.topic if req.topic else req.text

    prompt = (
        f"Generate exactly 3 educational multiple choice questions based on:\n"
        f"\"{input_content}\"\n\n"
        "Return JSON format:\n"
        "{\n"
        '  "questions": [\n'
        "    {\n"
        '      "question": "What is...?",\n'
        '      "options": ["Choice 1", "Choice 2", "Choice 3", "Choice 4"],\n'
        '      "correct_answer": "Choice 1",\n'
        '      "explanation": "Why Choice 1 is correct..."\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    data = gemini_service.generate_json(
        prompt=prompt,
        system_instruction=QUIZ_SYSTEM_INSTRUCTION,
        temperature=0.2
    )

    raw_list = []
    if isinstance(data, dict):
        raw_list = data.get("questions") or data.get("quiz") or []
    elif isinstance(data, list):
        raw_list = data

    questions = _normalize_questions(raw_list)

    return QuizResponse(
        questions=questions,
        source=source_desc
    )
