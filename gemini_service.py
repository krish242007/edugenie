import json
import logging
import re
import time
from typing import Any, Dict, Optional, Tuple
import httpx

import config

logger = logging.getLogger("edugenie.gemini")

class GeminiServiceError(Exception):
    """Structured exception for Gemini API related issues, categorized by error type."""
    def __init__(self, message: str, error_type: str, status_code: int = 502, retry_after: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.retry_after = retry_after

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "success": False,
            "error_type": self.error_type,
            "message": self.message,
            "detail": self.message
        }
        if self.retry_after is not None:
            data["retry_after"] = self.retry_after
        return data


class GeminiService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else config.GEMINI_API_KEY
        self.model = model if model is not None else config.GEMINI_MODEL
        self._genai_client = None
        self._init_client()

    def _init_client(self):
        """Initialize Google GenAI SDK client if available and configured."""
        if not self.api_key:
            config.refresh_config()
            self.api_key = config.GEMINI_API_KEY
        if not self.model:
            config.refresh_config()
            self.model = config.GEMINI_MODEL

        if not self.api_key or self.api_key.startswith("your_"):
            logger.warning("[Gemini] API key is not configured.")
            return

        try:
            from google import genai
            self._genai_client = genai.Client(api_key=self.api_key)
            logger.info("[Gemini] Client initialized with model: %s", self.model)
        except Exception as e:
            logger.info("[Gemini] Falling back to direct HTTPS REST client: %s", e)
            self._genai_client = None

    def _ensure_api_key(self):
        """Ensure non-empty API key before making any call."""
        if not self.api_key:
            config.refresh_config()
            self.api_key = config.GEMINI_API_KEY
        if not self.model:
            config.refresh_config()
            self.model = config.GEMINI_MODEL

        if not self.api_key or self.api_key.startswith("your_"):
            raise GeminiServiceError(
                message="The Gemini API configuration is invalid. Please set GEMINI_API_KEY in your .env file.",
                error_type="authentication",
                status_code=401
            )

    def _parse_429_error(self, err_json: Dict[str, Any]) -> Tuple[str, str, Optional[int]]:
        """
        Distinguishes between:
        1. Exhausted API Quota (daily/project quota limit reached - do NOT retry repeatedly)
        2. Temporary Rate Limiting (RPM limit or short traffic spike - retry with backoff)
        """
        err_obj = err_json.get("error", {})
        msg = err_obj.get("message", "")
        status = err_obj.get("status", "")
        details = err_obj.get("details", [])

        retry_seconds = None
        has_quota_failure = False
        is_per_day = False

        # Extract retryDelay from details if provided by Google
        for item in details:
            if isinstance(item, dict):
                if item.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                    raw_delay = item.get("retryDelay", "")
                    delay_match = re.search(r"(\d+)", str(raw_delay))
                    if delay_match:
                        retry_seconds = int(delay_match.group(1))

                if item.get("@type") == "type.googleapis.com/google.rpc.QuotaFailure":
                    has_quota_failure = True
                    violations = item.get("violations", [])
                    for v in violations:
                        quota_id = v.get("quotaId", "")
                        if "perday" in quota_id.lower() or "daily" in quota_id.lower():
                            is_per_day = True

        msg_lower = msg.lower()
        if "perday" in msg_lower or "daily" in msg_lower:
            is_per_day = True

        # Check if quota exhaustion (daily/project limit without a short retry delay):
        is_quota_exhausted = False
        if is_per_day and (retry_seconds is None or retry_seconds > 15):
            is_quota_exhausted = True
        elif has_quota_failure and (retry_seconds is None or retry_seconds > 15):
            is_quota_exhausted = True
        elif ("exceeded your current quota" in msg_lower or "quota exceeded" in msg_lower) and (retry_seconds is None or retry_seconds > 15):
            is_quota_exhausted = True

        if is_quota_exhausted:
            error_message = (
                f"AI usage limit has been reached for the configured Gemini API model ('{self.model}'). "
                "Please try again later or check your API quota in Google AI Studio."
            )
            return "quota_exceeded", error_message, retry_seconds

        # Otherwise, temporary RPM or transient spike
        error_message = "EduGenie is receiving too many requests. Please wait a moment and try again."
        return "rate_limit", error_message, retry_seconds or 2

    def _strip_markdown_json_fences(self, text: str) -> str:
        """Safely extract raw JSON from AI output that may contain markdown code fences."""
        cleaned = text.strip()
        pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

        # Find first '{' or '[' and matching last '}' or ']'
        first_brace = cleaned.find("{")
        first_bracket = cleaned.find("[")
        
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            end_idx = cleaned.rfind("}")
            if end_idx != -1 and end_idx >= first_brace:
                return cleaned[first_brace : end_idx + 1]
        elif first_bracket != -1:
            end_idx = cleaned.rfind("]")
            if end_idx != -1 and end_idx >= first_bracket:
                return cleaned[first_bracket : end_idx + 1]

        return cleaned

    def _call_gemini_api(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
        json_mode: bool = False
    ) -> str:
        """
        Executes request to Gemini API with:
        - Logging ([Gemini] Request started, Model, etc.)
        - Request timeout
        - Controlled exponential backoff retries for transient rate limits and 503s
        - Immediate return without infinite retries for exhausted quota or invalid auth
        """
        self._ensure_api_key()

        logger.info("[Gemini] Request started")
        logger.info("[Gemini] Model: %s", self.model)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        headers = {"Content-Type": "application/json"}
        max_retries = config.MAX_RETRIES

        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=config.REQUEST_TIMEOUT) as client:
                    response = client.post(url, json=payload, headers=headers)
                    status_code = response.status_code

                    # 1. Successful response
                    if status_code == 200:
                        logger.info("[Gemini] Response received (200 OK)")
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            prompt_feedback = data.get("promptFeedback", {})
                            block_reason = prompt_feedback.get("blockReason", "Blocked by safety filters")
                            raise GeminiServiceError(
                                message=f"Content generation was blocked: {block_reason}",
                                error_type="safety_blocked",
                                status_code=400
                            )

                        parts = candidates[0].get("content", {}).get("parts", [])
                        if not parts:
                            raise GeminiServiceError(
                                message="No response content returned from Gemini model.",
                                error_type="empty_response",
                                status_code=502
                            )

                        # Filter out thought signatures from modern models
                        text_parts = [p.get("text", "") for p in parts if not p.get("thought", False)]
                        result_text = "".join(text_parts).strip() if text_parts else "".join(p.get("text", "") for p in parts).strip()
                        return result_text

                    # 2. Rate Limit or Quota Exceeded (429)
                    if status_code == 429:
                        logger.warning("[Gemini] Rate limit / quota encountered (HTTP 429)")
                        try:
                            err_data = response.json()
                        except Exception:
                            err_data = {}

                        error_type, err_msg, retry_after = self._parse_429_error(err_data)

                        # If it is an account/project quota exhaustion, DO NOT keep retrying repeatedly
                        if error_type == "quota_exceeded":
                            logger.error("[Gemini] API Quota exhausted for model: %s", self.model)
                            raise GeminiServiceError(
                                message=err_msg,
                                error_type="quota_exceeded",
                                status_code=429,
                                retry_after=retry_after
                            )

                        # Transient rate-limit: apply backoff if retries remain
                        if attempt < max_retries:
                            backoff = max(float(retry_after or 0), 2.0 * (attempt + 1))
                            logger.info("[Gemini] Retry %d/%d (waiting %.1fs)", attempt + 1, max_retries, backoff)
                            time.sleep(backoff)
                            continue

                        raise GeminiServiceError(
                            message=err_msg,
                            error_type="rate_limit",
                            status_code=429,
                            retry_after=retry_after
                        )

                    # 3. Authentication or Bad Request (400 / 401 / 403)
                    if status_code in (400, 401, 403):
                        try:
                            err_data = response.json().get("error", {})
                            msg = err_data.get("message", "API request rejected")
                        except Exception:
                            msg = "API request rejected"

                        if "api key" in msg.lower() or "unregistered" in msg.lower() or status_code in (401, 403):
                            logger.error("[Gemini] Authentication failed: %s", msg)
                            raise GeminiServiceError(
                                message="The Gemini API configuration is invalid. Please verify your GEMINI_API_KEY.",
                                error_type="authentication",
                                status_code=401
                            )

                        logger.error("[Gemini] Client Error (%d): %s", status_code, msg)
                        raise GeminiServiceError(
                            message=f"Gemini API request error: {msg}",
                            error_type="bad_request",
                            status_code=400
                        )

                    # 4. Model Not Found or Unsupported (404)
                    if status_code == 404:
                        logger.error("[Gemini] Model not found: %s", self.model)
                        raise GeminiServiceError(
                            message=f"The configured AI model '{self.model}' is unavailable or invalid. Please check GEMINI_MODEL in .env.",
                            error_type="model_error",
                            status_code=404
                        )

                    # 5. Server Errors (500, 502, 503)
                    if status_code in (500, 502, 503):
                        logger.warning("[Gemini] Server error encountered: HTTP %d", status_code)
                        if attempt < max_retries:
                            backoff = 2.0 * (attempt + 1)
                            logger.info("[Gemini] Retry %d/%d (waiting %.1fs)", attempt + 1, max_retries, backoff)
                            time.sleep(backoff)
                            continue

                        raise GeminiServiceError(
                            message="Google Gemini servers are temporarily experiencing high demand. Please try again shortly.",
                            error_type="service_unavailable",
                            status_code=503
                        )

                    # Generic fallback for any other status code
                    raise GeminiServiceError(
                        message=f"Unexpected status code {status_code} received from Gemini API.",
                        error_type="api_error",
                        status_code=502
                    )

            except httpx.TimeoutException:
                logger.warning("[Gemini] Request timed out after %.1fs (attempt %d/%d)", config.REQUEST_TIMEOUT, attempt + 1, max_retries + 1)
                if attempt < max_retries:
                    time.sleep(2.0)
                    continue
                raise GeminiServiceError(
                    message="The AI service took too long to respond. Please try again.",
                    error_type="timeout",
                    status_code=504
                )
            except httpx.RequestError as re_err:
                logger.error("[Gemini] Network error connecting to Gemini API: %s", re_err)
                if attempt < max_retries:
                    time.sleep(2.0)
                    continue
                raise GeminiServiceError(
                    message="Unable to connect to Google Gemini API servers. Please check your internet connection.",
                    error_type="network_error",
                    status_code=503
                )

        raise GeminiServiceError(
            message="Request failed after maximum retry attempts.",
            error_type="rate_limit",
            status_code=429
        )

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.5
    ) -> str:
        """Centralized text generation method called by all AI modules."""
        return self._call_gemini_api(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            json_mode=False
        )

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> Any:
        """Centralized structured JSON generation method with safe extraction and parsing."""
        raw_text = self._call_gemini_api(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            json_mode=True
        )

        cleaned_json = self._strip_markdown_json_fences(raw_text)
        try:
            return json.loads(cleaned_json)
        except json.JSONDecodeError as jde:
            logger.error("[Gemini] Failed to decode JSON from AI output: %s\nRaw output: %s", jde, raw_text[:200])
            raise GeminiServiceError(
                message="EduGenie received an invalid structured response from the AI engine. Please retry.",
                error_type="json_parse_error",
                status_code=502
            )


# Global service singleton
gemini_service = GeminiService()
