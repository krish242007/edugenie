import os
import sys
import unittest
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
import config
from main import app
from gemini_service import GeminiService, GeminiServiceError

client = TestClient(app)

class TestEduGenieFixes(unittest.TestCase):

    def test_01_health_and_status_endpoints(self):
        """Test GET /health and GET /api/status without calling Gemini."""
        res_h = client.get("/health")
        self.assertEqual(res_h.status_code, 200)
        data_h = res_h.json()
        self.assertEqual(data_h.get("status"), "ok")
        self.assertEqual(data_h.get("service"), "EduGenie")
        self.assertNotIn("GEMINI_API_KEY", res_h.text)
        self.assertNotIn("AQ.", res_h.text)

        res_s = client.get("/api/status")
        self.assertEqual(res_s.status_code, 200)
        data_s = res_s.json()
        self.assertEqual(data_s.get("status"), "ok")
        self.assertTrue(data_s.get("gemini_configured"))
        self.assertEqual(data_s.get("model"), config.GEMINI_MODEL)
        self.assertNotIn("GEMINI_API_KEY", res_s.text)
        print("[PASS] Test: Health & Safe Diagnostic Endpoints verified")

    def test_02_ask_photosynthesis(self):
        """Test 1: Ask 'What is photosynthesis?' via POST /qa."""
        time.sleep(2.0)
        payload = {"question": "What is photosynthesis?"}
        res = client.post("/qa", json=payload)
        self.assertEqual(res.status_code, 200, f"QA failed: {res.text}")
        data = res.json()
        self.assertIn("answer", data)
        self.assertTrue(len(data["answer"]) > 20)
        print(f"[PASS] Test 1: Ask photosynthesis -> {data['answer'][:70]}...")

    def test_03_explain_pythagorean_theorem(self):
        """Test 2: Explain 'Pythagorean theorem' via POST /explain."""
        time.sleep(2.0)
        payload = {"topic": "Pythagorean theorem"}
        res = client.post("/explain", json=payload)
        self.assertEqual(res.status_code, 200, f"Explain failed: {res.text}")
        data = res.json()
        self.assertIn("explanation", data)
        self.assertEqual(data.get("topic"), "Pythagorean theorem")
        print("[PASS] Test 2: Explain Pythagorean theorem verified")

    def test_04_quiz_solar_system(self):
        """Test 3: Generate a quiz for 'Solar System' via POST /quiz."""
        time.sleep(2.5)
        payload = {"topic": "Solar System"}
        res = client.post("/quiz", json=payload)
        self.assertEqual(res.status_code, 200, f"Quiz failed: {res.text}")
        data = res.json()
        questions = data.get("questions", [])
        self.assertEqual(len(questions), 3, f"Expected 3 questions, got {len(questions)}")
        for idx, q in enumerate(questions):
            self.assertEqual(len(q["options"]), 4, f"Question {idx+1} options count != 4")
            self.assertIn(q["correct_answer"], q["options"])
            self.assertTrue(bool(q["explanation"]))
        print("[PASS] Test 3: Quiz Solar System generated 3 MCQs with 4 options each and explanations")

    def test_05_summarize_long_paragraph(self):
        """Test 4: Summarize a long educational paragraph via POST /summarize."""
        time.sleep(2.5)
        text = (
            "The solar system consists of the Sun and the gravitationally bound celestial bodies "
            "that orbit it, including eight major planets, dwarf planets, moons, asteroids, and comets. "
            "The four inner terrestrial planets—Mercury, Venus, Earth, and Mars—are composed primarily "
            "of rock and metal. In contrast, the outer gas and ice giants—Jupiter, Saturn, Uranus, "
            "and Neptune—are substantially more massive and possess extensive atmospheres.\n\n"
            "Between Mars and Jupiter lies the asteroid belt, containing rocky fragments leftover from the "
            "early accretion period. Beyond Neptune lies the Kuiper belt and the hypothetical Oort cloud, "
            "sources of short- and long-period comets."
        )
        res = client.post("/summarize", json={"text": text})
        self.assertEqual(res.status_code, 200, f"Summarize failed: {res.text}")
        data = res.json()
        self.assertTrue(bool(data.get("main_summary")))
        self.assertTrue(len(data.get("key_points", [])) >= 1)
        print("[PASS] Test 4: Summarize long paragraph verified")

    def test_06_sql_learning_path(self):
        """Test 5: Generate 'SQL learning path' via POST /learn/recommendations."""
        time.sleep(6.0)
        payload = {"topic": "SQL", "level": "beginner"}
        res = client.post("/learn/recommendations", json=payload)
        self.assertEqual(res.status_code, 200, f"Learning path failed: {res.text}")
        data = res.json()
        self.assertEqual(data.get("topic"), "SQL")
        stages = data.get("stages", [])
        self.assertTrue(len(stages) >= 3)
        print("[PASS] Test 5: SQL learning path generated Beginner -> Intermediate -> Advanced")

    def test_07_submit_empty_input(self):
        """Test 6: Submit empty input and verify clean validation error handling."""
        res_qa = client.post("/qa", json={"question": ""})
        self.assertEqual(res_qa.status_code, 422)
        data = res_qa.json()
        self.assertFalse(data.get("success", True))
        self.assertEqual(data.get("error_type"), "validation_error")

        res_quiz = client.post("/quiz", json={"topic": "", "text": ""})
        self.assertEqual(res_quiz.status_code, 422)
        print("[PASS] Test 6: Empty input rejected cleanly with 422 and structured error JSON")

    def test_08_429_quota_discrimination(self):
        """Test 8: Distinguish rate-limit vs quota exhaustion."""
        svc = GeminiService()
        
        # Test quota failure payload from Google Gemini API
        quota_err = {
            "error": {
                "code": 429,
                "message": "You exceeded your current quota. Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests",
                "status": "RESOURCE_EXHAUSTED",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                        "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]
                    }
                ]
            }
        }
        err_type, msg, retry = svc._parse_429_error(quota_err)
        self.assertEqual(err_type, "quota_exceeded")
        self.assertIn("AI usage limit has been reached", msg)

        # Test transient rate limit payload
        rate_err = {
            "error": {
                "code": 429,
                "message": "Too many requests. Please slow down.",
                "status": "RESOURCE_EXHAUSTED",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.RetryInfo",
                        "retryDelay": "3s"
                    }
                ]
            }
        }
        err_type_rate, msg_rate, retry_rate = svc._parse_429_error(rate_err)
        self.assertEqual(err_type_rate, "rate_limit")
        self.assertEqual(retry_rate, 3)
        print("[PASS] Test 8: 429 discrimination between transient rate-limit and quota exhaustion verified")

    def test_09_invalid_gemini_api_key(self):
        """Test 9: Test invalid Gemini API key handling."""
        bad_svc = GeminiService()
        bad_svc.api_key = "AIzaSy_INVALID_KEY_FOR_TESTING_12345"
        
        with self.assertRaises(GeminiServiceError) as cm:
            bad_svc._call_gemini_api(prompt="Test")
        
        err = cm.exception
        self.assertEqual(err.error_type, "authentication")
        self.assertEqual(err.status_code, 401)
        self.assertIn("invalid", err.message.lower())
        print("[PASS] Test 9: Invalid API key properly returns 401 authentication error")

    def test_10_invalid_model_configuration(self):
        """Test 10: Test unavailable/invalid model configuration."""
        bad_svc = GeminiService()
        bad_svc.model = "non-existent-gemini-model-xyz-999"
        
        with self.assertRaises(GeminiServiceError) as cm:
            bad_svc._call_gemini_api(prompt="Test")
        
        err = cm.exception
        self.assertEqual(err.error_type, "model_error")
        self.assertEqual(err.status_code, 404)
        self.assertIn("unavailable or invalid", err.message.lower())
        print("[PASS] Test 10: Unavailable model configuration properly returns 404 model_error")


if __name__ == "__main__":
    unittest.main()
