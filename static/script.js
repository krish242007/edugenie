/**
 * EduGenie – AI-Powered Learning Assistant
 * Frontend Controller & Interactive Engine
 */

// Application State
const state = {
    currentMode: 'ask',
    quizSubMode: 'topic', // 'topic' or 'text'
    learnLevel: 'beginner',
    isSubmitting: false,  // Duplicate request prevention guard
    lastSubmittedInput: '',
    lastPayload: null,
    lastResponseData: null,
    // Quiz Session State
    quiz: {
        questions: [],
        currentIndex: 0,
        score: 0,
        userAnswers: [],
        source: ''
    }
};

// Mode Configurations
const modeConfigs = {
    ask: {
        title: "Ask EduGenie Anything",
        subtitle: "Enter any academic concept, homework question, or topic you're studying.",
        placeholder: "Ask anything you're learning (e.g., What is photosynthesis? How does gravity work?)...",
        buttonText: "Ask EduGenie",
        badge: "💬 Q&A Answer",
        maxLen: 1000,
        chips: [
            "What is photosynthesis?",
            "What is the largest ocean?",
            "Explain Newton's third law of motion",
            "Why is the sky blue?"
        ]
    },
    explain: {
        title: "Understand Difficult Concepts Simply",
        subtitle: "Enter a challenging or abstract topic to receive a 6-part beginner-friendly breakdown.",
        placeholder: "Enter a topic to simplify (e.g., Quantum Computing, Pythagorean theorem, Black Holes)...",
        buttonText: "Explain Simply",
        badge: "💡 Conceptual Explanation",
        maxLen: 300,
        chips: [
            "Pythagorean theorem",
            "Quantum Computing",
            "How Blockchain Works",
            "CRISPR Gene Editing"
        ]
    },
    quiz: {
        title: "Generate Interactive Quiz",
        subtitle: "Test your comprehension with 3 targeted multiple-choice questions.",
        placeholder: "Enter a topic to generate a quiz from (e.g., Solar System, Photosynthesis)...",
        buttonText: "Generate Quiz",
        badge: "🎯 Interactive Quiz",
        maxLen: 20000,
        chips: [
            "Solar System",
            "Photosynthesis",
            "Pythagorean Theorem",
            "Python Programming Basics"
        ]
    },
    summarize: {
        title: "Summarize Educational Content",
        subtitle: "Paste textbook passages, study notes, or research text to extract core takeaways and key terms.",
        placeholder: "Paste educational text here (minimum 20 characters)...",
        buttonText: "Summarize Text",
        badge: "📑 Synthesized Summary",
        maxLen: 20000,
        chips: [
            "Load Sample: Photosynthesis & Solar Energy",
            "Load Sample: The Roman Republic & Senate",
            "Load Sample: Fundamentals of Machine Learning"
        ]
    },
    learn: {
        title: "Personalized Learning Roadmaps",
        subtitle: "Generate an end-to-end curriculum from Beginner to Advanced with practical milestones.",
        placeholder: "Enter a subject or skill (e.g., SQL, Machine Learning, Full-Stack Development)...",
        buttonText: "Generate Roadmap",
        badge: "🗺️ Learning Roadmap",
        maxLen: 300,
        chips: [
            "SQL",
            "Python for Data Science",
            "Machine Learning",
            "Web Development"
        ]
    }
};

// Sample Texts for Summarizer
const sampleTexts = {
    "Load Sample: Photosynthesis & Solar Energy": `Photosynthesis is the fundamental biological process by which green plants, algae, and certain bacteria convert light energy, typically from the sun, into chemical energy stored in glucose molecules. This remarkable biochemical reaction takes place within cellular organelles called chloroplasts, which contain the green pigment chlorophyll. 

During the light-dependent reactions occurring in the thylakoid membranes, photons of light are absorbed by chlorophyll, splitting water molecules into oxygen, protons, and electrons. The released oxygen is expelled into the Earth's atmosphere as a vital byproduct. Subsequently, during the light-independent Calvin cycle in the stroma, carbon dioxide is fixed and converted into energy-rich carbohydrates. Photosynthesis is the primary engine of planetary biomass production and the ultimate source of oxygen and atmospheric balance on Earth.`,

    "Load Sample: The Roman Republic & Senate": `The Roman Republic was established in 509 BCE following the overthrow of the tyrannical Tarquin monarchy. Rather than vesting supreme authority in an individual king, the Romans crafted a complex constitution centered on shared governance, mutual checks, and civic participation. 

The Senate served as the guiding advisory body composed of patrician aristocracy, exercising profound influence over foreign policy, public expenditure, and religious traditions. Executive power was divided between two annually elected Consuls who commanded armies and administered laws. Lower legislative assemblies, notably the Centuriate and Tribal assemblies, allowed citizens to vote on statutes and elect magistrates. While marked by intense class struggles between patricians and plebeians, this republican structure endured for nearly five centuries before transforming into the Roman Empire.`,

    "Load Sample: Fundamentals of Machine Learning": `Machine Learning (ML) is a specialized branch of artificial intelligence focused on building algorithms that enable computational systems to learn patterns and make inferences directly from empirical data without being explicitly programmed for every specific scenario. 

Historically, computational tasks required rigid rules formulated by human programmers. In contrast, machine learning utilizes statistical models trained on vast datasets. The primary paradigms include supervised learning, where algorithms learn from labeled input-output pairs; unsupervised learning, which discovers hidden patterns in unlabeled data; and reinforcement learning, where an agent learns through iterative feedback and trial-and-error rewards. Machine learning now powers modern search engines, natural language processing, diagnostic medicine, and autonomous transport.`
};

// DOM Elements
const elements = {
    tabs: document.querySelectorAll('.mode-tab'),
    learningForm: document.getElementById('learning-form'),
    inputModeTitle: document.getElementById('input-mode-title'),
    inputModeSubtitle: document.getElementById('input-mode-subtitle'),
    auxControls: document.getElementById('aux-controls'),
    userInput: document.getElementById('user-input'),
    charCounter: document.getElementById('char-counter'),
    btnClearInput: document.getElementById('btn-clear-input'),
    chipsList: document.getElementById('chips-list'),
    btnSubmit: document.getElementById('btn-submit'),
    btnSubmitText: document.getElementById('btn-submit-text'),
    loadingState: document.getElementById('loading-state'),
    loadingTitle: document.getElementById('loading-title'),
    loadingDesc: document.getElementById('loading-desc'),
    errorState: document.getElementById('error-state'),
    errorTitle: document.getElementById('error-title'),
    errorMessage: document.getElementById('error-message'),
    btnRetry: document.getElementById('btn-retry'),
    btnDismissError: document.getElementById('btn-dismiss-error'),
    resultsSection: document.getElementById('results-section'),
    resultsBadgeIcon: document.getElementById('results-badge-icon'),
    resultsBadgeText: document.getElementById('results-badge-text'),
    resultsBody: document.getElementById('results-body'),
    btnCopyResult: document.getElementById('btn-copy-result'),
    btnNewQuery: document.getElementById('btn-new-query'),
    appStatusIndicator: document.getElementById('app-status-indicator'),
    appStatusDot: document.getElementById('app-status-dot'),
    appStatusLabel: document.getElementById('app-status-label')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    setMode('ask');
    checkInitialStatus();
});

/**
 * Checks system status without consuming Gemini generation quota
 */
async function checkInitialStatus() {
    try {
        const resp = await fetch('/api/status');
        if (resp.ok) {
            const data = await resp.json();
            if (data.gemini_configured) {
                setAIStatus('ready', 'AI Ready', `Configured Model: ${data.model}`);
            } else {
                setAIStatus('error', 'Config Error', 'GEMINI_API_KEY is not configured in .env');
            }
        }
    } catch (e) {
        console.warn('Could not check /api/status:', e);
    }
}

/**
 * Updates the Header Status Indicator
 * @param {'ready'|'busy'|'error'} status - 'ready', 'busy', or 'error'
 */
function setAIStatus(status, label, titleText) {
    if (!elements.appStatusIndicator) return;
    elements.appStatusIndicator.className = 'status-indicator';

    if (status === 'ready') {
        elements.appStatusIndicator.classList.add('online');
    } else if (status === 'busy') {
        elements.appStatusIndicator.classList.add('busy');
    } else {
        elements.appStatusIndicator.classList.add('error');
    }

    if (elements.appStatusLabel) elements.appStatusLabel.textContent = label;
    if (titleText) elements.appStatusIndicator.title = titleText;
}

function initEventListeners() {
    // Mode tabs switching
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            setMode(mode);
        });
    });

    // Form submission handler (Prevents duplicate events)
    if (elements.learningForm) {
        elements.learningForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleFormSubmit();
        });
    }

    // Textarea input changes & char count
    elements.userInput.addEventListener('input', updateCharCount);

    // Clear button
    elements.btnClearInput.addEventListener('click', () => {
        elements.userInput.value = '';
        updateCharCount();
        elements.userInput.focus();
    });

    // Keyboard shortcut (Ctrl+Enter or Cmd+Enter)
    elements.userInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleFormSubmit();
        }
    });

    // Retry Button - Properly retries the same request preserving mode and input
    if (elements.btnRetry) {
        elements.btnRetry.addEventListener('click', () => {
            if (state.lastSubmittedInput && !elements.userInput.value.trim()) {
                elements.userInput.value = state.lastSubmittedInput;
                updateCharCount();
            }
            hideError();
            handleFormSubmit();
        });
    }

    // Dismiss Error Button
    if (elements.btnDismissError) {
        elements.btnDismissError.addEventListener('click', hideError);
    }

    // Copy result button
    elements.btnCopyResult.addEventListener('click', copyResultsToClipboard);

    // New Query button
    elements.btnNewQuery.addEventListener('click', () => {
        elements.userInput.value = '';
        updateCharCount();
        elements.resultsSection.classList.add('hidden');
        elements.userInput.focus();
        window.scrollTo({ top: elements.userInput.offsetTop - 120, behavior: 'smooth' });
    });
}

/**
 * Switch Active Learning Mode
 */
function setMode(mode) {
    if (!modeConfigs[mode]) return;
    state.currentMode = mode;

    elements.tabs.forEach(tab => {
        const isActive = tab.dataset.mode === mode;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    const cfg = modeConfigs[mode];
    elements.inputModeTitle.textContent = cfg.title;
    elements.inputModeSubtitle.textContent = cfg.subtitle;
    elements.userInput.placeholder = cfg.placeholder;
    elements.btnSubmitText.textContent = cfg.buttonText;
    elements.resultsBadgeText.textContent = cfg.badge;

    // Adjust textarea sizing
    elements.userInput.rows = (mode === 'summarize' || (mode === 'quiz' && state.quizSubMode === 'text')) ? 6 : 3;

    renderAuxControls(mode);
    renderChips(cfg.chips);

    updateCharCount();
    hideError();
    elements.userInput.focus();
}

/**
 * Render Secondary Controls (for Quiz sub-mode & Learn level)
 */
function renderAuxControls(mode) {
    elements.auxControls.innerHTML = '';

    if (mode === 'quiz') {
        const segmented = document.createElement('div');
        segmented.className = 'segmented-control';
        segmented.innerHTML = `
            <button type="button" class="seg-btn ${state.quizSubMode === 'topic' ? 'active' : ''}" data-sub="topic">From Topic</button>
            <button type="button" class="seg-btn ${state.quizSubMode === 'text' ? 'active' : ''}" data-sub="text">From Passage</button>
        `;
        segmented.querySelectorAll('.seg-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                state.quizSubMode = btn.dataset.sub;
                segmented.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                if (state.quizSubMode === 'text') {
                    elements.userInput.placeholder = "Paste an educational passage or chapter excerpt to test comprehension...";
                    elements.userInput.rows = 6;
                } else {
                    elements.userInput.placeholder = modeConfigs.quiz.placeholder;
                    elements.userInput.rows = 3;
                }
            });
        });
        elements.auxControls.appendChild(segmented);
    } else if (mode === 'learn') {
        const segmented = document.createElement('div');
        segmented.className = 'segmented-control';
        segmented.innerHTML = `
            <button type="button" class="seg-btn ${state.learnLevel === 'beginner' ? 'active' : ''}" data-level="beginner">Beginner</button>
            <button type="button" class="seg-btn ${state.learnLevel === 'intermediate' ? 'active' : ''}" data-level="intermediate">Intermediate</button>
            <button type="button" class="seg-btn ${state.learnLevel === 'advanced' ? 'active' : ''}" data-level="advanced">Advanced</button>
        `;
        segmented.querySelectorAll('.seg-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                state.learnLevel = btn.dataset.level;
                segmented.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
        elements.auxControls.appendChild(segmented);
    }
}

/**
 * Render Quick Inspiration Chips
 */
function renderChips(chips) {
    elements.chipsList.innerHTML = '';
    chips.forEach(chipText => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'chip-btn';
        btn.textContent = chipText;
        btn.addEventListener('click', () => {
            if (sampleTexts[chipText]) {
                elements.userInput.value = sampleTexts[chipText];
            } else {
                elements.userInput.value = chipText;
            }
            updateCharCount();
            elements.userInput.focus();
        });
        elements.chipsList.appendChild(btn);
    });
}

function updateCharCount() {
    const len = elements.userInput.value.length;
    const max = modeConfigs[state.currentMode].maxLen;
    elements.charCounter.textContent = `${len.toLocaleString()} / ${max.toLocaleString()}`;
    if (len > max) {
        elements.charCounter.style.color = '#f43f5e';
    } else {
        elements.charCounter.style.color = '';
    }
}

/**
 * Form Submission & API Controller with Duplicate Request Prevention and Timeouts
 */
async function handleFormSubmit() {
    // 1. Prevent duplicate submissions while a request is active
    if (state.isSubmitting) {
        console.warn("EduGenie: Duplicate submission ignored while request is in flight.");
        return;
    }

    const rawVal = elements.userInput.value.trim() || state.lastSubmittedInput;
    if (!rawVal) {
        showErrorUI("Missing Input", "Please enter a question, topic, or educational text before submitting.", false);
        elements.userInput.focus();
        return;
    }

    const maxLen = modeConfigs[state.currentMode].maxLen;
    if (rawVal.length > maxLen) {
        showErrorUI("Input Too Long", `Your input is ${rawVal.length} characters, which exceeds the limit of ${maxLen}. Please shorten it.`, false);
        return;
    }

    state.lastSubmittedInput = rawVal;
    state.isSubmitting = true;

    hideError();
    setLoading(true);

    // Setup client-side timeout controller (35 seconds)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 35000);

    try {
        let endpoint = '';
        let payload = {};

        switch (state.currentMode) {
            case 'ask':
                endpoint = '/qa';
                payload = { question: rawVal };
                break;

            case 'explain':
                endpoint = '/explain';
                payload = { topic: rawVal };
                break;

            case 'quiz':
                endpoint = '/quiz';
                if (state.quizSubMode === 'text') {
                    payload = { text: rawVal };
                } else {
                    payload = { topic: rawVal };
                }
                break;

            case 'summarize':
                endpoint = '/summarize';
                payload = { text: rawVal };
                break;

            case 'learn':
                endpoint = '/learn/recommendations';
                payload = { topic: rawVal, level: state.learnLevel };
                break;
        }

        state.lastPayload = payload;

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        const data = await response.json();

        if (!response.ok) {
            handleAPIErrorResponse(response.status, data);
            return;
        }

        // Success: update status to ready and render result
        setAIStatus('ready', 'AI Ready', 'Gemini AI Engine Active');
        state.lastResponseData = data;
        renderResult(state.currentMode, data);

    } catch (err) {
        clearTimeout(timeoutId);
        console.error("API Request Error:", err);

        if (err.name === 'AbortError') {
            showErrorUI("Request Timed Out", "The AI service took too long to respond. Please try again.", true);
            setAIStatus('busy', 'AI Busy', 'Request Timed Out');
        } else {
            showErrorUI("Connection Error", "Unable to connect to the EduGenie server. Please check your network connection.", true);
            setAIStatus('busy', 'AI Busy', 'Network Connection Error');
        }
    } finally {
        state.isSubmitting = false;
        setLoading(false);
    }
}

/**
 * Categorized Backend Error Handler
 */
function handleAPIErrorResponse(statusCode, data) {
    const errorType = data.error_type || '';
    const message = data.message || data.detail || '';

    if (errorType === 'quota_exceeded' || (statusCode === 429 && message.toLowerCase().includes('quota'))) {
        setAIStatus('busy', 'AI Busy', 'API Quota Exceeded');
        showErrorUI(
            "AI Usage Limit Reached",
            "AI usage limit has been reached for the configured Gemini API. Please try again later or check your API quota in Google AI Studio.",
            true
        );
    } else if (errorType === 'rate_limit' || statusCode === 429) {
        setAIStatus('busy', 'AI Busy', 'Rate Limited');
        showErrorUI(
            "EduGenie is Busy",
            "EduGenie is temporarily busy receiving too many requests. Please wait a few seconds and try again.",
            true
        );
    } else if (errorType === 'authentication' || statusCode === 401) {
        setAIStatus('error', 'Config Error', 'Invalid API Key');
        showErrorUI(
            "API Configuration Error",
            "Gemini API configuration needs attention. Please verify your GEMINI_API_KEY in the .env file.",
            false
        );
    } else if (errorType === 'model_error' || statusCode === 404) {
        setAIStatus('error', 'Config Error', 'Invalid Model');
        showErrorUI(
            "Model Unavailable",
            "The configured AI model is unavailable. Please check GEMINI_MODEL in .env.",
            false
        );
    } else if (errorType === 'timeout' || statusCode === 504) {
        showErrorUI(
            "Request Timed Out",
            "The AI service took too long to respond. Please try again.",
            true
        );
    } else if (statusCode === 422 || errorType === 'validation_error') {
        showErrorUI(
            "Invalid Input",
            message || "Please check your input formatting.",
            false
        );
    } else {
        showErrorUI(
            "Service Notice",
            message || "An unexpected error occurred while communicating with the AI service. Please try again.",
            true
        );
    }
}

/**
 * Loading & Error State Handlers
 */
function setLoading(isLoading) {
    elements.btnSubmit.disabled = isLoading;
    if (elements.btnRetry) elements.btnRetry.disabled = isLoading;

    if (isLoading) {
        elements.loadingState.classList.remove('hidden');
        elements.resultsSection.classList.add('hidden');
        
        const tips = [
            "Synthesizing academic knowledge base...",
            "Consulting educational pedagogy models...",
            "Formulating beginner-friendly analogies...",
            "Structuring comprehension questions...",
            "Distilling core concepts and removing redundancy..."
        ];
        elements.loadingDesc.textContent = tips[Math.floor(Math.random() * tips.length)];
        elements.loadingState.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        elements.loadingState.classList.add('hidden');
    }
}

function showErrorUI(title, msg, showRetry = true) {
    elements.errorTitle.textContent = title;
    elements.errorMessage.textContent = msg;
    if (elements.btnRetry) {
        elements.btnRetry.style.display = showRetry ? 'inline-flex' : 'none';
        elements.btnRetry.disabled = false;
    }
    elements.errorState.classList.remove('hidden');
    elements.errorState.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError() {
    elements.errorState.classList.add('hidden');
}

/**
 * Result Rendering Dispatcher
 */
function renderResult(mode, data) {
    elements.resultsSection.classList.remove('hidden');
    elements.resultsBody.innerHTML = '';

    switch (mode) {
        case 'ask':
            renderQnAResult(data);
            break;
        case 'explain':
            renderExplainResult(data);
            break;
        case 'quiz':
            renderQuizResult(data);
            break;
        case 'summarize':
            renderSummaryResult(data);
            break;
        case 'learn':
            renderLearningPathResult(data);
            break;
    }

    elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Q&A Renderer
 */
function renderQnAResult(data) {
    const container = document.createElement('div');
    container.className = 'markdown-output';
    const htmlContent = window.marked ? marked.parse(data.answer) : escapeHtml(data.answer).replace(/\n/g, '<br>');
    container.innerHTML = htmlContent;
    elements.resultsBody.appendChild(container);
}

/**
 * Explanation Renderer (6-part structured view)
 */
function renderExplainResult(data) {
    const s = data.structured;
    if (!s) {
        const container = document.createElement('div');
        container.className = 'markdown-output';
        container.innerHTML = window.marked ? marked.parse(data.explanation) : escapeHtml(data.explanation).replace(/\n/g, '<br>');
        elements.resultsBody.appendChild(container);
        return;
    }

    const container = document.createElement('div');
    container.className = 'explain-container';

    // Header Card (Simple Definition)
    const headerCard = document.createElement('div');
    headerCard.className = 'explain-header-card';
    headerCard.innerHTML = `
        <div class="explain-title-tag">Simplified Concept</div>
        <h3 class="explain-topic-title">${escapeHtml(data.topic)}</h3>
        <p class="explain-def-text"><strong>Definition:</strong> ${escapeHtml(s.simple_definition)}</p>
    `;
    container.appendChild(headerCard);

    // 4-Card Grid (How it works, Key concepts, Analogy, Example)
    const grid = document.createElement('div');
    grid.className = 'explain-grid';

    // How It Works
    const howCard = document.createElement('div');
    howCard.className = 'explain-card';
    howCard.innerHTML = `
        <div class="card-icon-title">
            <span class="explain-icon">⚙️</span>
            <h4 class="card-heading">How It Works</h4>
        </div>
        <p class="explain-text">${escapeHtml(s.how_it_works)}</p>
    `;
    grid.appendChild(howCard);

    // Key Concepts
    const conceptsCard = document.createElement('div');
    conceptsCard.className = 'explain-card';
    const conceptsListHtml = (s.key_concepts || []).map(c => `<li class="concept-item">${escapeHtml(c)}</li>`).join('');
    conceptsCard.innerHTML = `
        <div class="card-icon-title">
            <span class="explain-icon">🔑</span>
            <h4 class="card-heading">Key Concepts</h4>
        </div>
        <ul class="concepts-list">${conceptsListHtml}</ul>
    `;
    grid.appendChild(conceptsCard);

    // Simple Analogy
    const analogyCard = document.createElement('div');
    analogyCard.className = 'explain-card';
    analogyCard.innerHTML = `
        <div class="card-icon-title">
            <span class="explain-icon">🌟</span>
            <h4 class="card-heading">Everyday Analogy</h4>
        </div>
        <p class="explain-text">${escapeHtml(s.simple_analogy)}</p>
    `;
    grid.appendChild(analogyCard);

    // Real-World Example
    const exampleCard = document.createElement('div');
    exampleCard.className = 'explain-card';
    exampleCard.innerHTML = `
        <div class="card-icon-title">
            <span class="explain-icon">🌍</span>
            <h4 class="card-heading">Real-World Example</h4>
        </div>
        <p class="explain-text">${escapeHtml(s.real_world_example)}</p>
    `;
    grid.appendChild(exampleCard);

    container.appendChild(grid);

    // Recap Box
    const recapBox = document.createElement('div');
    recapBox.className = 'recap-box';
    recapBox.innerHTML = `
        <span class="explain-icon">📌</span>
        <div>
            <h4 class="card-heading" style="color: #6ee7b7; margin-bottom: 0.2rem;">Quick Recap</h4>
            <p class="explain-text" style="color: #e2e8f0;">${escapeHtml(s.short_recap)}</p>
        </div>
    `;
    container.appendChild(recapBox);

    elements.resultsBody.appendChild(container);
}

/**
 * Interactive Quiz Renderer
 */
function renderQuizResult(data) {
    if (!data.questions || !data.questions.length) {
        showErrorUI("Quiz Generation Error", "No questions were returned. Please try again.", true);
        return;
    }

    state.quiz = {
        questions: data.questions,
        currentIndex: 0,
        score: 0,
        userAnswers: [],
        source: data.source || 'Topic'
    };

    renderActiveQuizQuestion();
}

function renderActiveQuizQuestion() {
    const qState = state.quiz;
    elements.resultsBody.innerHTML = '';

    if (qState.currentIndex >= qState.questions.length) {
        renderQuizSummaryCard();
        return;
    }

    const currentQ = qState.questions[qState.currentIndex];
    const totalQ = qState.questions.length;

    const runner = document.createElement('div');
    runner.className = 'quiz-runner';

    runner.innerHTML = `
        <div class="quiz-top-bar">
            <span class="quiz-progress-text">Question ${qState.currentIndex + 1} of ${totalQ}</span>
            <span class="quiz-score-badge">Score: ${qState.score} / ${qState.currentIndex}</span>
        </div>
    `;

    const qCard = document.createElement('div');
    qCard.className = 'quiz-question-card';
    qCard.innerHTML = `<h3 class="quiz-question-prompt">${escapeHtml(currentQ.question)}</h3>`;

    const optionsList = document.createElement('div');
    optionsList.className = 'quiz-options-list';

    const letters = ['A', 'B', 'C', 'D'];
    currentQ.options.forEach((optText, optIdx) => {
        const optBtn = document.createElement('button');
        optBtn.type = 'button';
        optBtn.className = 'quiz-option-btn';
        optBtn.innerHTML = `
            <span class="quiz-option-letter">${letters[optIdx] || optIdx + 1}</span>
            <span class="quiz-option-text">${escapeHtml(optText)}</span>
        `;
        optBtn.addEventListener('click', () => handleQuizAnswer(optText, optBtn, optionsList, currentQ));
        optionsList.appendChild(optBtn);
    });

    qCard.appendChild(optionsList);
    runner.appendChild(qCard);
    elements.resultsBody.appendChild(runner);
}

function handleQuizAnswer(selectedOption, chosenBtn, optionsList, currentQ) {
    const allBtns = optionsList.querySelectorAll('.quiz-option-btn');
    allBtns.forEach(btn => btn.disabled = true);

    const isCorrect = selectedOption.trim().toLowerCase() === currentQ.correct_answer.trim().toLowerCase();

    if (isCorrect) {
        state.quiz.score += 1;
        chosenBtn.classList.add('correct');
    } else {
        chosenBtn.classList.add('wrong');
        allBtns.forEach(btn => {
            const txt = btn.querySelector('.quiz-option-text').textContent.trim();
            if (txt.toLowerCase() === currentQ.correct_answer.trim().toLowerCase()) {
                btn.classList.add('correct');
            }
        });
    }

    state.quiz.userAnswers.push({
        question: currentQ.question,
        chosen: selectedOption,
        correct: currentQ.correct_answer,
        isCorrect: isCorrect,
        explanation: currentQ.explanation
    });

    const runner = elements.resultsBody.querySelector('.quiz-runner');
    const feedbackBox = document.createElement('div');
    feedbackBox.className = `quiz-feedback-box ${isCorrect ? 'is-correct' : 'is-wrong'}`;
    feedbackBox.innerHTML = `
        <div class="feedback-status-title ${isCorrect ? 'correct' : 'wrong'}">
            ${isCorrect ? '✅ Correct Answer!' : '❌ Incorrect'}
        </div>
        <p class="feedback-explanation">
            ${!isCorrect ? `<strong>Correct Answer:</strong> ${escapeHtml(currentQ.correct_answer)}<br>` : ''}
            <strong>Explanation:</strong> ${escapeHtml(currentQ.explanation)}
        </p>
    `;
    runner.appendChild(feedbackBox);

    const isLast = state.quiz.currentIndex === state.quiz.questions.length - 1;
    const navBar = document.createElement('div');
    navBar.className = 'quiz-navigation-bar';
    navBar.innerHTML = `
        <button type="button" class="btn-quiz-next">
            ${isLast ? 'View Final Results 🏆' : 'Next Question &rarr;'}
        </button>
    `;
    navBar.querySelector('.btn-quiz-next').addEventListener('click', () => {
        state.quiz.currentIndex += 1;
        renderActiveQuizQuestion();
    });
    runner.appendChild(navBar);
    navBar.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function renderQuizSummaryCard() {
    const qState = state.quiz;
    const total = qState.questions.length;
    const pct = Math.round((qState.score / total) * 100);

    let emoji = '🌟';
    let title = 'Mastery Achieved!';
    let desc = 'Exceptional job! You demonstrated complete conceptual comprehension.';

    if (pct < 50) {
        emoji = '📚';
        title = 'Keep Practicing!';
        desc = 'Good attempt! Review the explanations below and try again to reinforce key concepts.';
    } else if (pct < 100) {
        emoji = '👏';
        title = 'Great Progress!';
        desc = 'Strong understanding! With a quick review of missed points, you will have total mastery.';
    }

    const card = document.createElement('div');
    card.className = 'quiz-summary-card';
    card.innerHTML = `
        <div class="summary-score-circle">
            <span class="score-num">${qState.score}</span>
            <span class="score-total">out of ${total}</span>
        </div>
        <h3 class="summary-title">${emoji} ${title}</h3>
        <p class="summary-desc">${desc}</p>
        <button type="button" class="btn-retake-quiz" id="btn-retake">Try Again 🔄</button>
    `;

    card.querySelector('#btn-retake').addEventListener('click', () => {
        state.quiz.currentIndex = 0;
        state.quiz.score = 0;
        state.quiz.userAnswers = [];
        renderActiveQuizQuestion();
    });

    elements.resultsBody.appendChild(card);
}

/**
 * Summary Renderer
 */
function renderSummaryResult(data) {
    const container = document.createElement('div');
    container.className = 'summary-container';

    const metricsBar = document.createElement('div');
    metricsBar.className = 'summary-metrics-bar';
    metricsBar.innerHTML = `
        <div class="metric-card">
            <div class="metric-value">${data.original_word_count.toLocaleString()}</div>
            <div class="metric-label">Original Words</div>
        </div>
        <div class="metric-card">
            <div class="metric-value highlight">${data.summary_word_count.toLocaleString()}</div>
            <div class="metric-label">Summarized Words</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #34d399;">~${data.reading_time_saved_minutes} min</div>
            <div class="metric-label">Reading Time Saved</div>
        </div>
    `;
    container.appendChild(metricsBar);

    const summaryBlock = document.createElement('div');
    summaryBlock.className = 'summary-block';
    summaryBlock.innerHTML = `
        <h3 class="summary-block-title">📖 Core Synthesis</h3>
        <p class="summary-narrative">${escapeHtml(data.main_summary)}</p>
    `;
    container.appendChild(summaryBlock);

    if (data.key_points && data.key_points.length) {
        const pointsBlock = document.createElement('div');
        pointsBlock.className = 'summary-block';
        const pointsHtml = data.key_points.map(pt => `
            <li class="key-point-item">
                <span class="point-bullet"></span>
                <span>${escapeHtml(pt)}</span>
            </li>
        `).join('');
        pointsBlock.innerHTML = `
            <h3 class="summary-block-title">💡 Key Takeaways</h3>
            <ul class="key-points-list">${pointsHtml}</ul>
        `;
        container.appendChild(pointsBlock);
    }

    if (data.important_terms && data.important_terms.length) {
        const termsBlock = document.createElement('div');
        termsBlock.className = 'summary-block';
        const termsHtml = data.important_terms.map(t => `
            <div class="term-pill-card">
                <div class="term-name">${escapeHtml(t.term)}</div>
                <div class="term-def">${escapeHtml(t.definition)}</div>
            </div>
        `).join('');
        termsBlock.innerHTML = `
            <h3 class="summary-block-title">🏷️ Important Terminology</h3>
            <div class="terms-grid">${termsHtml}</div>
        `;
        container.appendChild(termsBlock);
    }

    elements.resultsBody.appendChild(container);
}

/**
 * Learning Path Renderer
 */
function renderLearningPathResult(data) {
    const container = document.createElement('div');
    container.className = 'roadmap-container';

    const headerCard = document.createElement('div');
    headerCard.className = 'roadmap-header-card';
    headerCard.innerHTML = `
        <div class="explain-title-tag">Mastery Blueprint &bull; Starting Level: ${escapeHtml(data.user_level.toUpperCase())}</div>
        <h3 class="explain-topic-title" style="margin-bottom: 0.5rem;">${escapeHtml(data.topic)}</h3>
        <p class="roadmap-summary-text">${escapeHtml(data.summary)}</p>
    `;
    container.appendChild(headerCard);

    const timeline = document.createElement('div');
    timeline.className = 'stages-timeline';

    data.stages.forEach(stage => {
        const stagePillClass = stage.stage_name.toLowerCase().includes('begin') 
            ? 'beginner' 
            : stage.stage_name.toLowerCase().includes('inter') 
                ? 'intermediate' 
                : 'advanced';

        const stageCard = document.createElement('div');
        stageCard.className = 'stage-card';

        stageCard.innerHTML = `
            <div class="stage-header">
                <div class="stage-title-group">
                    <span class="stage-pill ${stagePillClass}">${escapeHtml(stage.stage_name)}</span>
                    <span class="explain-text" style="font-weight: 600;">${escapeHtml(stage.description)}</span>
                </div>
                <span class="stage-duration">⏱️ ${escapeHtml(stage.estimated_duration)}</span>
            </div>
        `;

        const modulesList = document.createElement('div');
        modulesList.className = 'modules-list';

        stage.modules.forEach(mod => {
            const modCard = document.createElement('div');
            modCard.className = 'module-card';

            const resourcesHtml = (mod.resources || []).map(res => {
                if (res.url) {
                    return `<a href="${escapeHtml(res.url)}" target="_blank" rel="noopener noreferrer" class="resource-pill">
                        <span class="resource-type-badge">${escapeHtml(res.type)}</span>
                        <span>${escapeHtml(res.name)} &nearr;</span>
                    </a>`;
                }
                return `<div class="resource-pill">
                    <span class="resource-type-badge">${escapeHtml(res.type)}</span>
                    <span>${escapeHtml(res.name)}</span>
                </div>`;
            }).join('');

            modCard.innerHTML = `
                <div class="module-title-row">
                    <h4 class="module-title">${escapeHtml(mod.title)}</h4>
                    <span class="module-timeframe">${escapeHtml(mod.suggested_timeframe)}</span>
                </div>
                <div class="module-details-grid">
                    <div>
                        <div class="detail-label">What to Learn</div>
                        <div class="detail-value">${escapeHtml(mod.what_to_learn)}</div>
                    </div>
                    <div>
                        <div class="detail-label">Why It Matters</div>
                        <div class="detail-value">${escapeHtml(mod.why_it_matters)}</div>
                    </div>
                </div>
                <div class="practice-box">
                    <div class="practice-label">Hands-On Practice Milestone:</div>
                    <div class="detail-value">${escapeHtml(mod.practice_activity)}</div>
                </div>
                ${resourcesHtml ? `
                    <div class="detail-label" style="margin-top: 0.6rem;">Recommended Curated Resources</div>
                    <div class="resources-list">${resourcesHtml}</div>
                ` : ''}
            `;
            modulesList.appendChild(modCard);
        });

        stageCard.appendChild(modulesList);
        timeline.appendChild(stageCard);
    });

    container.appendChild(timeline);
    elements.resultsBody.appendChild(container);
}

/**
 * Clipboard Copy Utility
 */
function copyResultsToClipboard() {
    let textToCopy = '';

    if (state.currentMode === 'ask') {
        textToCopy = state.lastResponseData ? state.lastResponseData.answer : '';
    } else if (state.currentMode === 'explain') {
        textToCopy = state.lastResponseData ? state.lastResponseData.explanation : '';
    } else if (state.currentMode === 'quiz') {
        textToCopy = JSON.stringify(state.lastResponseData ? state.lastResponseData.questions : [], null, 2);
    } else if (state.currentMode === 'summarize') {
        textToCopy = state.lastResponseData ? `${state.lastResponseData.main_summary}\n\nKey Takeaways:\n${(state.lastResponseData.key_points || []).map(p => `- ${p}`).join('\n')}` : '';
    } else if (state.currentMode === 'learn') {
        textToCopy = JSON.stringify(state.lastResponseData, null, 2);
    }

    if (!textToCopy) return;

    navigator.clipboard.writeText(textToCopy).then(() => {
        const copyBtn = elements.btnCopyResult;
        const origHtml = copyBtn.innerHTML;
        copyBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <span style="color: #34d399; font-weight: 700;">Copied!</span>
        `;
        setTimeout(() => {
            copyBtn.innerHTML = origHtml;
        }, 2000);
    }).catch(err => {
        console.error("Clipboard copy failed:", err);
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
