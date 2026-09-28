# EduGenie – AI-Powered Learning Assistant

EduGenie is a modern, full-stack educational web application designed for students and self-directed learners. Powered by Google Gemini AI and built on FastAPI, EduGenie simplifies complex academic concepts, delivers concise answers, generates interactive comprehension quizzes, synthesizes long reading material, and charts actionable learning roadmaps from beginner to advanced mastery.

---

## 🌟 Key Features

1. **Academic Q&A (`POST /qa`)**
   - Direct, accurate, and student-friendly answers to homework and conceptual questions.
   - Clarifies terminology and uses relatable examples without hallucinations.

2. **Concept Simplification (`POST /explain`)**
   - Breaks difficult or abstract concepts into a structured 6-part framework:
     1. Simple Definition (intuitive 1-2 sentence overview)
     2. How It Works (step-by-step mechanics)
     3. Key Concepts (core principles)
     4. Simple Everyday Analogy (mental model)
     5. Real-World Example (practical application)
     6. Short Recap (memorable takeaway)

3. **Interactive Knowledge Quizzes (`POST /quiz`)**
   - Generates exactly 3 conceptual multiple-choice questions (4 options each) from any topic or passage.
   - Features an interactive browser quiz runner:
     - Real-time score counter and question tracking
     - Instant visual feedback (Emerald green for correct, Rose red for incorrect)
     - Reveals the correct answer and in-depth educational explanations
     - Final score summary card with celebration status and a "Try Again" retake option.

4. **Educational Text Summarizer (`POST /summarize`)**
   - Distills long textbook chapters, lecture notes, or research papers.
   - Extracts:
     - Core narrative summary
     - High-retention bullet takeaways
     - Key terminology dictionary with definitions
     - Real-time reading metrics (words saved, estimated time saved).

5. **Personalized Learning Paths (`POST /learn/recommendations`)**
   - Creates a progressive 3-stage roadmap: **Beginner → Intermediate → Advanced**.
   - Includes what to learn, why it matters, suggested timeframes, hands-on practice milestones, and verified recommended resources.

---

## 🏗️ Architecture & Project Structure

The project maintains a strict separation of concerns between API routing, business logic, AI orchestration, and user interface:

```text
EduGenie/
├── main.py                 # FastAPI application, route mounting, & error handlers
├── config.py               # Environment configuration and input validation boundaries
├── gemini_service.py       # Google Gemini SDK & fallback REST communication engine
├── qna.py                  # Q&A module with student-focused system prompting
├── explanation_module.py   # Concept breakdown module (structured JSON & markdown)
├── quiz_module.py          # 3-question MCQ generator with Pydantic validation
├── summary_module.py       # Educational text summarizer & metric calculator
├── learning_path.py        # Beginner-to-Advanced curriculum and roadmap generator
├── requirements.txt        # Pinned dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Protects secrets, cache, and virtual environments
├── templates/
│   └── index.html          # Semantic HTML5 dashboard template
├── static/
│   ├── style.css           # Modern SaaS design system with dark aesthetics
│   └── script.js           # Client-side state manager and interactive quiz engine
└── README.md               # Complete documentation
```

---

## 💻 Tech Stack

- **Backend**: Python 3.10+ (tested with Python 3.12), FastAPI, Uvicorn, Pydantic v2, Jinja2, HTTPX.
- **AI Engine**: Google Gemini API (`google-genai` SDK with resilient REST API fallback).
- **Frontend**: Semantic HTML5, Vanilla Modern CSS (glassmorphism, CSS Grid, Flexbox, accessible contrast), Vanilla JavaScript (ES6+), and Marked.js for fast markdown parsing.

---

## 🚀 Quickstart & Installation

### 1. Clone or Navigate to the Repository
```bash
cd EduGenie
```

### 2. Set Up a Virtual Environment
```bash
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and provide your Google Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
HOST=127.0.0.1
PORT=8000
DEBUG=false
```

> **How to get a Gemini API Key:**
> 1. Visit Google AI Studio at [https://aistudio.google.com/](https://aistudio.google.com/).
> 2. Click **Get API key** and create a new key.
> 3. Paste it into your `.env` file as `GEMINI_API_KEY`.

### 5. Run the Application
```bash
uvicorn main:app --reload
```

Then open your browser and navigate to:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📡 REST API Reference

### Health Check
- **Endpoint**: `GET /health`
- **Response**:
```json
{
  "status": "ok",
  "app": "EduGenie",
  "gemini_configured": true,
  "model": "gemini-2.5-flash"
}
```

---

### 1. Q&A Module
- **Endpoint**: `POST /qa`
- **Request Body**:
```json
{
  "question": "What is photosynthesis?"
}
```
- **Response Body**:
```json
{
  "question": "What is photosynthesis?",
  "answer": "Photosynthesis is the biological process used by plants, algae, and cyanobacteria to convert light energy into chemical energy stored in glucose...",
  "status": "success"
}
```

---

### 2. Explanation Module
- **Endpoint**: `POST /explain`
- **Request Body**:
```json
{
  "topic": "Quantum Computing"
}
```
- **Response Body**:
```json
{
  "topic": "Quantum Computing",
  "explanation": "### 💡 Simple Definition\n...\n### ⚙️ How It Works\n...",
  "structured": {
    "simple_definition": "Quantum computing uses quantum mechanics to process complex data exponentially faster than regular computers.",
    "how_it_works": "Instead of classical bits (0 or 1), it uses qubits which can exist as both 0 and 1 simultaneously.",
    "key_concepts": ["Qubits", "Superposition", "Entanglement"],
    "simple_analogy": "A regular computer tries one maze path at a time; a quantum computer explores every path at once.",
    "real_world_example": "Discovering new life-saving pharmaceutical drugs by simulating molecular reactions.",
    "short_recap": "Quantum computers leverage superposition to calculate vast possibilities simultaneously."
  },
  "status": "success"
}
```

---

### 3. Quiz Module
- **Endpoint**: `POST /quiz`
- **Request Body** (from topic):
```json
{
  "topic": "Pythagoras Theorem"
}
```
*or from passage:*
```json
{
  "text": "The Pythagorean theorem states that in a right-angled triangle, the square of the hypotenuse is equal to the sum of the squares of the other two sides..."
}
```
- **Response Body**:
```json
{
  "questions": [
    {
      "question": "In a right-angled triangle with legs of length 3 and 4, what is the length of the hypotenuse?",
      "options": ["5", "6", "7", "12"],
      "correct_answer": "5",
      "explanation": "According to the theorem, 3² + 4² = 9 + 16 = 25. The square root of 25 is 5."
    }
  ],
  "source": "Topic: Pythagoras Theorem",
  "status": "success"
}
```

---

### 4. Summarization Module
- **Endpoint**: `POST /summarize`
- **Request Body**:
```json
{
  "text": "Photosynthesis is the fundamental biological process by which green plants, algae, and certain bacteria convert light energy into chemical energy..."
}
```
- **Response Body**:
```json
{
  "main_summary": "Photosynthesis enables plants to convert sunlight into glucose while producing oxygen as a vital atmospheric byproduct.",
  "key_points": [
    "Takes place in cellular organelles called chloroplasts.",
    "Light-dependent reactions split water molecules and release oxygen.",
    "The Calvin cycle fixes carbon dioxide into energy-rich carbohydrates."
  ],
  "important_terms": [
    { "term": "Chloroplast", "definition": "Cellular organelle where photosynthesis occurs" }
  ],
  "original_word_count": 120,
  "summary_word_count": 48,
  "reading_time_saved_minutes": 0.4,
  "status": "success"
}
```

---

### 5. Learning Path Module
- **Endpoint**: `POST /learn/recommendations`
- **Request Body**:
```json
{
  "topic": "SQL",
  "level": "beginner"
}
```
- **Response Body**:
```json
{
  "topic": "SQL",
  "user_level": "beginner",
  "summary": "Master relational databases from basic querying to database administration.",
  "stages": [
    {
      "stage_name": "Beginner",
      "description": "Core querying syntax and database schemas.",
      "estimated_duration": "2-3 weeks",
      "modules": [
        {
          "title": "SELECT, WHERE, and Filtering",
          "what_to_learn": "Basic data extraction, operators, filtering conditions",
          "why_it_matters": "Fundamental building block of all database operations",
          "suggested_timeframe": "1 week",
          "practice_activity": "Query a sample e-commerce database for customer orders",
          "resources": [
            { "name": "W3Schools SQL Tutorial", "type": "Interactive Guide", "url": "https://www.w3schools.com" }
          ]
        }
      ]
    },
    {
      "stage_name": "Intermediate",
      "description": "Joins, aggregations, and subqueries...",
      "estimated_duration": "3-4 weeks",
      "modules": [...]
    },
    {
      "stage_name": "Advanced",
      "description": "Window functions, indexing, and query optimization...",
      "estimated_duration": "4-6 weeks",
      "modules": [...]
    }
  ],
  "status": "success"
}
```

---

## 🔒 Security Best Practices

1. **Secret Isolation**: `GEMINI_API_KEY` is loaded exclusively server-side via `config.py`. It is never transmitted to client JavaScript.
2. **Input Validation**: Strict character length and content checks on all inputs through Pydantic v2 validators.
3. **Markdown Sanitization**: Dynamic client rendering uses safe HTML escaping and structured DOM construction.
4. **Execution Safety**: EduGenie never executes AI-generated code.
5. **Clean Error Messages**: Internal exception stack traces are logged locally on the server; the client receives safe, friendly messages.

---

## 🛠️ Troubleshooting

- **"Gemini API key is not configured"**:
  Ensure `.env` exists in the project root and `GEMINI_API_KEY` contains your actual Google AI Studio API key. Restart the server after editing `.env`.
- **"Model not found or unsupported"**:
  Change `GEMINI_MODEL=gemini-2.5-flash` or `GEMINI_MODEL=gemini-1.5-flash` in your `.env`.
- **Port Conflict (8000 already in use)**:
  Run `uvicorn main:app --port 8080 --reload`.

---

## 🔮 Future-Ready Architecture

The codebase is intentionally modular to support the following upcoming features without architectural refactoring:
- 🎙️ Voice interaction & audio narration (Web Speech API integration ready)
- 🌐 Multilingual learning support
- 📱 Progressive Web App (PWA) offline cache
- 📊 Learning streak & gamification badges
- 👩‍🏫 Teacher & Classroom sync (Moodle/Google Classroom)
- 📄 Document upload (PDF & Image OCR doubt solving)
