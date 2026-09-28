import sys
import time
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestEduGenie(unittest.TestCase):

    def test_01_health_check(self):
        """Test GET /health returns status ok."""
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("app"), "EduGenie")
        print("[PASS] Health check endpoint verified")

    def test_02_homepage_loads(self):
        """Test GET / renders HTML successfully."""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("EduGenie", response.text)
        self.assertIn("interactive-textarea", response.text)
        print("[PASS] Homepage HTML successfully rendered")

    def test_03_qa_endpoint(self):
        """Test POST /qa with academic question: 'What is the largest ocean?'."""
        time.sleep(2.0)
        payload = {"question": "What is the largest ocean?"}
        response = client.post("/qa", json=payload)
        self.assertEqual(response.status_code, 200, f"QA failed: {response.text}")
        data = response.json()
        self.assertIn("answer", data)
        self.assertIn("pacific", data["answer"].lower())
        print(f"[PASS] Q&A module answered: {data['answer'][:80]}...")

    def test_04_explain_endpoint(self):
        """Test POST /explain with topic: 'Pythagorean theorem'."""
        time.sleep(2.0)
        payload = {"topic": "Pythagorean theorem"}
        response = client.post("/explain", json=payload)
        self.assertEqual(response.status_code, 200, f"Explain failed: {response.text}")
        data = response.json()
        self.assertIn("explanation", data)
        self.assertEqual(data.get("topic"), "Pythagorean theorem")
        if data.get("structured"):
            s = data["structured"]
            self.assertTrue(bool(s.get("simple_definition")))
            self.assertTrue(bool(s.get("how_it_works")))
            self.assertTrue(len(s.get("key_concepts", [])) > 0)
            self.assertTrue(bool(s.get("simple_analogy")))
            self.assertTrue(bool(s.get("real_world_example")))
            self.assertTrue(bool(s.get("short_recap")))
        print(f"[PASS] Explanation module verified with 6-part framework for '{data['topic']}'")

    def test_05_quiz_endpoint(self):
        """Test POST /quiz with topic: 'Photosynthesis'."""
        time.sleep(2.0)
        payload = {"topic": "Photosynthesis"}
        response = client.post("/quiz", json=payload)
        self.assertEqual(response.status_code, 200, f"Quiz failed: {response.text}")
        data = response.json()
        questions = data.get("questions", [])
        self.assertEqual(len(questions), 3, f"Expected 3 questions, got {len(questions)}")
        
        for idx, q in enumerate(questions):
            self.assertTrue(bool(q.get("question")), f"Question {idx+1} is missing text")
            options = q.get("options", [])
            self.assertEqual(len(options), 4, f"Question {idx+1} must have 4 options, got {len(options)}")
            correct = q.get("correct_answer")
            self.assertTrue(bool(correct), f"Question {idx+1} missing correct_answer")
            self.assertIn(correct, options, f"Question {idx+1} correct_answer not in options list")
            self.assertTrue(bool(q.get("explanation")), f"Question {idx+1} missing explanation")
            print(f"  Question {idx+1}: {q['question'][:50]}... (Correct: {correct})")
        print("[PASS] Quiz module verified with 3 questions, 4 options each, correct answers, and explanations")

    def test_06_summarize_endpoint(self):
        """Test POST /summarize with a multi-paragraph educational passage."""
        passage = (
            "Photosynthesis is the fundamental biological process by which green plants, algae, "
            "and certain bacteria convert light energy into chemical energy stored in glucose molecules. "
            "This biochemical reaction takes place within cellular organelles called chloroplasts, "
            "which contain the green pigment chlorophyll.\n\n"
            "During the light-dependent reactions occurring in the thylakoid membranes, photons of light "
            "are absorbed by chlorophyll, splitting water molecules into oxygen, protons, and electrons. "
            "The released oxygen is expelled into the Earth's atmosphere as a vital byproduct. "
            "Subsequently, during the Calvin cycle in the stroma, carbon dioxide is fixed and converted "
            "into energy-rich carbohydrates. Photosynthesis is the primary engine of planetary biomass production."
        )
        time.sleep(2.0)
        payload = {"text": passage}
        response = client.post("/summarize", json=payload)
        self.assertEqual(response.status_code, 200, f"Summarize failed: {response.text}")
        data = response.json()
        self.assertTrue(bool(data.get("main_summary")))
        self.assertTrue(len(data.get("key_points", [])) >= 1)
        self.assertTrue(data.get("original_word_count", 0) > 0)
        self.assertTrue(data.get("summary_word_count", 0) > 0)
        print(f"[PASS] Summary module verified: saved ~{data.get('reading_time_saved_minutes')} min reading time")

    def test_07_learning_path_endpoint(self):
        """Test POST /learn/recommendations with topic='SQL', level='beginner'."""
        time.sleep(2.0)
        payload = {"topic": "SQL", "level": "beginner"}
        response = client.post("/learn/recommendations", json=payload)
        self.assertEqual(response.status_code, 200, f"Learning path failed: {response.text}")
        data = response.json()
        self.assertEqual(data.get("topic"), "SQL")
        stages = data.get("stages", [])
        self.assertTrue(len(stages) >= 3, f"Expected at least 3 stages, got {len(stages)}")
        
        stage_names = [s.get("stage_name", "").lower() for s in stages]
        self.assertTrue(any("begin" in name for name in stage_names), "Beginner stage missing")
        self.assertTrue(any("inter" in name for name in stage_names), "Intermediate stage missing")
        self.assertTrue(any("adv" in name for name in stage_names), "Advanced stage missing")

        for stage in stages:
            for mod in stage.get("modules", []):
                self.assertTrue(bool(mod.get("title")))
                self.assertTrue(bool(mod.get("what_to_learn")))
                self.assertTrue(bool(mod.get("why_it_matters")))
                self.assertTrue(bool(mod.get("practice_activity")))
        print("[PASS] Learning path module verified: Beginner -> Intermediate -> Advanced progression with resources")

    def test_08_error_handling_empty_inputs(self):
        """Test validation error handling for empty inputs."""
        # Empty QA
        res_qa = client.post("/qa", json={"question": "   "})
        self.assertIn(res_qa.status_code, [400, 422])
        
        # Empty Explain
        res_exp = client.post("/explain", json={"topic": ""})
        self.assertIn(res_exp.status_code, [400, 422])
        
        # Empty Quiz
        res_quiz = client.post("/quiz", json={"topic": "", "text": ""})
        self.assertIn(res_quiz.status_code, [400, 422])
        
        # Text too short for summarize
        res_sum = client.post("/summarize", json={"text": "Short"})
        self.assertIn(res_sum.status_code, [400, 422])
        print("[PASS] Error handling verified for empty and invalid inputs (400/422 status codes)")

    def test_09_error_handling_excessive_length(self):
        """Test rejection of unreasonably long inputs."""
        huge_question = "A" * 1500
        res = client.post("/qa", json={"question": huge_question})
        self.assertIn(res.status_code, [400, 422])
        print("[PASS] Input limit protection verified for excessive lengths")


if __name__ == "__main__":
    unittest.main()
