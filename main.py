import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

import config
from gemini_service import GeminiServiceError
from qna import QnARequest, QnAResponse, answer_question
from explanation_module import ExplainRequest, ExplainResponse, explain_topic
from quiz_module import QuizRequest, QuizResponse, generate_quiz
from summary_module import SummaryRequest, SummaryResponse, summarize_text
from learning_path import LearnRequest, LearningPathResponse, generate_learning_path

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("edugenie.app")

BASE_DIR = Path(__file__).resolve().parent

# Create FastAPI app
app = FastAPI(
    title="EduGenie – AI-Powered Learning Assistant",
    description="Your AI-powered learning companion for students and self-learners.",
    version="1.0.0"
)

# Enable CORS for cross-origin flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files & Templates
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"
static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


# --- Centralized Exception Handlers ---

@app.exception_handler(GeminiServiceError)
async def gemini_service_exception_handler(request: Request, exc: GeminiServiceError):
    """Categorized handler for Gemini API errors (rate-limits, quota, auth, model, timeouts)."""
    logger.error("GeminiServiceError on %s: [%s] %s", request.url.path, exc.error_type, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Clean user-friendly error formatting for validation failures."""
    errors = []
    for err in exc.errors():
        msg = err.get("msg", "Invalid input")
        loc = " -> ".join(str(l) for l in err.get("loc", []) if l != "body")
        errors.append(f"{loc}: {msg}" if loc else msg)
    combined = " | ".join(errors)
    logger.warning("Validation error on %s: %s", request.url.path, combined)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "validation_error",
            "message": combined,
            "detail": combined
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle custom value validation errors from modules."""
    logger.warning("Value error on %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error_type": "bad_request",
            "message": str(exc),
            "detail": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Protect internal details and stack traces while returning safe messages."""
    logger.exception("Unhandled server exception on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "server_error",
            "message": "An unexpected error occurred while processing your request. Please try again shortly.",
            "detail": "An unexpected error occurred."
        }
    )


# --- Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    """Serves the EduGenie interactive dashboard."""
    config.refresh_config()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "gemini_configured": config.is_gemini_configured(),
            "model_name": config.GEMINI_MODEL
        }
    )


@app.get("/health")
async def health_check():
    """System health check endpoint without calling Gemini."""
    return {
        "status": "ok",
        "service": "EduGenie",
        "app": "EduGenie",
        "gemini_configured": config.is_gemini_configured()
    }


@app.get("/api/status")
async def api_status():
    """Safe diagnostic endpoint returning non-sensitive configuration state."""
    config.refresh_config()
    return {
        "status": "ok",
        "service": "EduGenie",
        "gemini_configured": config.is_gemini_configured(),
        "model": config.GEMINI_MODEL
    }


@app.post("/qa", response_model=QnAResponse)
async def api_qa(payload: QnARequest):
    """Q&A Module: Answer academic and general educational questions concisely."""
    logger.info("Handling Q&A query: %s", payload.question[:60])
    return answer_question(payload.question)


@app.post("/explain", response_model=ExplainResponse)
async def api_explain(payload: ExplainRequest):
    """Explanation Module: Simplify difficult topics into 6 structured beginner-friendly parts."""
    logger.info("Handling Explain query for topic: %s", payload.topic[:60])
    return explain_topic(payload.topic)


@app.post("/quiz", response_model=QuizResponse)
async def api_quiz(payload: QuizRequest):
    """Quiz Module: Generate an interactive 3-question MCQ quiz from topic or text."""
    src = payload.topic if payload.topic else payload.text[:40]
    logger.info("Generating quiz for: %s", src)
    return generate_quiz(payload)


@app.post("/summarize", response_model=SummaryResponse)
async def api_summarize(payload: SummaryRequest):
    """Summary Module: Condense educational text into core summary, key takeaways, and terms."""
    logger.info("Summarizing text of length: %d chars", len(payload.text))
    return summarize_text(payload.text)


@app.post("/learn/recommendations", response_model=LearningPathResponse)
async def api_learn(payload: LearnRequest):
    """Learning Path Module: Create a roadmap from beginner to advanced with actionable resources."""
    logger.info("Generating learning path for '%s' (level: %s)", payload.topic, payload.level)
    return generate_learning_path(payload)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )
