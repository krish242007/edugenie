import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from gemini_service import gemini_service
import config

logger = logging.getLogger("edugenie.learn")

class LearnRequest(BaseModel):
    topic: str = Field(..., description="Topic or subject to generate a learning path for.")
    level: str = Field(default="beginner", description="Current learner level: beginner, intermediate, or advanced.")

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Topic cannot be empty.")
        if len(cleaned) > config.MAX_TOPIC_LENGTH:
            raise ValueError(f"Topic is too long (maximum {config.MAX_TOPIC_LENGTH} characters).")
        return cleaned

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ("beginner", "intermediate", "advanced"):
            return "beginner"
        return cleaned


class ResourceItem(BaseModel):
    name: str
    type: str = "Resource"
    description: Optional[str] = ""
    url: Optional[str] = None


class TopicModule(BaseModel):
    title: str
    what_to_learn: str
    why_it_matters: str
    suggested_timeframe: str
    practice_activity: str
    resources: List[ResourceItem] = []


class StagePath(BaseModel):
    stage_name: str
    description: str
    estimated_duration: str
    modules: List[TopicModule]


class LearningPathResponse(BaseModel):
    topic: str
    user_level: str
    summary: str
    stages: List[StagePath]
    status: str = "success"


LEARNING_PATH_SYSTEM_INSTRUCTION = (
    "You are EduGenie's Curriculum Architect. Your mission is to construct realistic, progressive, "
    "and highly motivating learning roadmaps from Beginner to Advanced levels.\n"
    "Crucial Guidelines:\n"
    "1. Structure the path into exactly 3 stages: 'Beginner', 'Intermediate', and 'Advanced'.\n"
    "2. For each stage, define 2 to 3 essential topic modules.\n"
    "3. For each topic module include:\n"
    "   - 'title': Clear subject module title.\n"
    "   - 'what_to_learn': Concrete list of skills and concepts.\n"
    "   - 'why_it_matters': Real-world motivation and importance.\n"
    "   - 'suggested_timeframe': Realistic time estimate (e.g. '1-2 weeks', '3-5 days').\n"
    "   - 'practice_activity': A hands-on mini-project or exercise.\n"
    "   - 'resources': Recommended resources (name, type such as 'Official Documentation', 'Book', 'Practice Platform', 'Video Course').\n"
    "4. DO NOT FABRICATE URLs. Never create fake links. If linking, only use verified root/canonical domains (e.g. https://docs.python.org, https://developer.mozilla.org, https://leetcode.com), otherwise leave url null.\n"
    "5. Return strictly valid JSON."
)


def generate_learning_path(req: LearnRequest) -> LearningPathResponse:
    """Generates a structured learning path progressing from beginner to advanced with actionable resources."""
    prompt = (
        f"Create a comprehensive learning path for \"{req.topic}\".\n"
        f"The learner's current starting level is: {req.level}.\n\n"
        "Return structured JSON matching this schema:\n"
        "{\n"
        '  "summary": "Inspiring 1-2 sentence overview of the journey.",\n'
        '  "stages": [\n'
        "    {\n"
        '      "stage_name": "Beginner",\n'
        '      "description": "Foundations and core basics.",\n'
        '      "estimated_duration": "4-6 weeks",\n'
        '      "modules": [\n'
        "        {\n"
        '          "title": "Module Title",\n'
        '          "what_to_learn": "Key skills and concepts...",\n'
        '          "why_it_matters": "Why this matters in practice...",\n'
        '          "suggested_timeframe": "1-2 weeks",\n'
        '          "practice_activity": "Hands-on project...",\n'
        '          "resources": [\n'
        '            {"name": "Resource Name", "type": "Documentation", "description": "Short tip", "url": null}\n'
        "          ]\n"
        "        }\n"
        "      ]\n"
        "    },\n"
        '    {"stage_name": "Intermediate", ...},\n'
        '    {"stage_name": "Advanced", ...}\n'
        "  ]\n"
        "}"
    )

    try:
        data = gemini_service.generate_json(
            prompt=prompt,
            system_instruction=LEARNING_PATH_SYSTEM_INSTRUCTION,
            temperature=0.3
        )

        summary = data.get("summary", f"Structured roadmap to master {req.topic}.")
        raw_stages = data.get("stages", [])

        stages: List[StagePath] = []
        for stage_data in raw_stages:
            stage_name = stage_data.get("stage_name", "Stage")
            desc = stage_data.get("description", "")
            duration = stage_data.get("estimated_duration", "Varies")
            
            raw_modules = stage_data.get("modules", [])
            modules: List[TopicModule] = []
            for m_data in raw_modules:
                # Parse resources
                raw_res = m_data.get("resources", [])
                res_list: List[ResourceItem] = []
                for r in raw_res:
                    if isinstance(r, dict):
                        # Ensure no fake URLs
                        url = r.get("url")
                        if url and not any(trusted in url for trusted in ("docs.", "mozilla.org", "khanacademy.org", "github.com", "leetcode.com", "w3schools.com")):
                            url = None
                        res_list.append(ResourceItem(
                            name=str(r.get("name", "Recommended Guide")),
                            type=str(r.get("type", "Reference")),
                            description=str(r.get("description", "")),
                            url=url
                        ))
                    elif isinstance(r, str):
                        res_list.append(ResourceItem(name=r, type="Guide"))

                modules.append(TopicModule(
                    title=str(m_data.get("title", "Topic Module")),
                    what_to_learn=str(m_data.get("what_to_learn", "Core skills")),
                    why_it_matters=str(m_data.get("why_it_matters", "Foundational knowledge")),
                    suggested_timeframe=str(m_data.get("suggested_timeframe", "1 week")),
                    practice_activity=str(m_data.get("practice_activity", "Build a small demo project")),
                    resources=res_list
                ))

            stages.append(StagePath(
                stage_name=stage_name,
                description=desc,
                estimated_duration=duration,
                modules=modules
            ))

        # Fallback if AI didn't return 3 stages
        if len(stages) < 3:
            required = ["Beginner", "Intermediate", "Advanced"]
            existing = [s.stage_name.capitalize() for s in stages]
            for req_stage in required:
                if req_stage not in existing:
                    stages.append(StagePath(
                        stage_name=req_stage,
                        description=f"{req_stage} mastery for {req.topic}",
                        estimated_duration="3-4 weeks",
                        modules=[TopicModule(
                            title=f"Core {req_stage} Concepts",
                            what_to_learn=f"Key {req_stage.lower()} techniques and best practices.",
                            why_it_matters="Crucial for developing proficiency.",
                            suggested_timeframe="2 weeks",
                            practice_activity=f"Implement practical {req.topic} projects.",
                            resources=[ResourceItem(name=f"Official {req.topic} Documentation", type="Documentation")]
                        )]
                    ))

        return LearningPathResponse(
            topic=req.topic,
            user_level=req.level,
            summary=summary,
            stages=stages
        )

    except Exception as e:
        logger.error("Learning path generation error: %s", e)
        raise e
