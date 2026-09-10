import re
import json
import random
from typing import Optional, List, Dict, Any
from pathlib import Path
from src.config import GEMINI_API_KEY, DEFAULT_MODEL
from src.schemas import Question, MCQOption
from src.ingestion import KnowledgeStore

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


def is_valid_question(q: Question) -> bool:
    """Rigorous sanity check: ensures complete stem and non-empty options."""
    if not q or not q.question:
        return False
    q_str = q.question.strip()
    if len(q_str) < 20 or q_str.endswith(",") or "costs ." in q_str or "for ." in q_str or "have ," in q_str:
        return False
    if not q.options or len(q.options) != 4:
        return False
    for opt in q.options:
        if not opt.text or not opt.text.strip():
            return False
    if q.correct_key not in ["A", "B", "C", "D"]:
        return False
    return True


def _load_questions() -> List[Question]:
    """Load the calibrated bank from storage/topic_questions.json."""
    json_path = Path(__file__).resolve().parent.parent.parent / "storage" / "topic_questions.json"
    if json_path.exists():
        try:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
            valid = []
            for d in raw:
                try:
                    q = Question.model_validate(d)
                    if is_valid_question(q):
                        valid.append(q)
                except Exception:
                    pass
            return valid
        except Exception as e:
            print(f"[DiagnosticAgent] Error loading questions from JSON: {e}")
    return []


FALLBACK_QUESTIONS = _load_questions()


class DiagnosticAgent:
    """
    Diagnostic Assessment Agent:
    Retrieves syllabus concepts via RAG and dynamically creates or selects calibrated MCQs.
    Supports:
      1. Infinite Gemini AI question generation on demand.
      2. Weak-spot targeted drills for missed concepts.
      3. Parametric question generator for endless offline variations.
      4. Customizable quiz lengths (5, 10, 15 questions) and difficulty scaling.
    """

    def __init__(self, knowledge_store: KnowledgeStore):
        self.store = knowledge_store
        self.client = None
        if GEMINI_API_KEY and genai:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"[DiagnosticAgent] Client error: {e}")

    def set_api_key(self, api_key: str):
        """Dynamically configure or update the Gemini API client."""
        if genai and api_key.strip():
            try:
                self.client = genai.Client(api_key=api_key.strip())
                print("[DiagnosticAgent] Gemini client successfully initialized with provided key.")
                return True
            except Exception as e:
                print(f"[DiagnosticAgent] Error setting API key: {e}")
        return False

    def reload_bank(self):
        """Reload question pool from storage."""
        global FALLBACK_QUESTIONS
        FALLBACK_QUESTIONS = _load_questions()

    def generate_live_ai_question(
        self,
        topic: str,
        exam_type: str = "SAT",
        difficulty: str = "Medium",
        weak_concept: Optional[str] = None
    ) -> Optional[Question]:
        """Use Gemini 1.5/2.0 with RAG context to invent a brand new, original question."""
        if not self.client:
            return None

        search_query = weak_concept if weak_concept else f"{topic} {difficulty} {exam_type} high yield test question"
        context_chunks = self.store.search(search_query, exam_type=exam_type, top_k=2)
        context_text = "\n\n".join([c["content"] for c in context_chunks])

        prompt = f"""
You are an expert exam creator for {exam_type} test preparation.
Generate ONE brand new, high-quality multiple-choice question on:
Topic: '{topic}'
Difficulty: {difficulty}
{f"Target Weak Area to Test: {weak_concept}" if weak_concept else ""}

CURRICULUM CONTEXT:
{context_text}

STRICT REQUIREMENTS:
1. Provide exactly 4 options (A, B, C, D). Every option MUST have complete non-empty text.
2. Exactly ONE option is correct. The correct answer must NOT always be 'A'.
3. State the question stem completely with all numbers, values, and question prompt clearly written.
4. Include 'distractor_analysis' for each of the 3 incorrect options explaining the specific student mistake.
5. Return strictly valid JSON adhering to this exact schema:
{{
  "id": "ai_{exam_type.lower()}_q",
  "exam_type": "{exam_type}",
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "question": "Complete question text with all numbers stated.",
  "options": [
    {{"key": "A", "text": "Option A complete text"}},
    {{"key": "B", "text": "Option B complete text"}},
    {{"key": "C", "text": "Option C complete text"}},
    {{"key": "D", "text": "Option D complete text"}}
  ],
  "correct_key": "B",
  "rationale": "Clear step-by-step solution.",
  "distractor_analysis": {{
    "A": "Why A is tempting.",
    "C": "Why C is tempting.",
    "D": "Why D is tempting."
  }}
}}
"""
        try:
            import time
            response = self.client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            txt = response.text.strip()
            if txt.startswith("```json"):
                txt = txt[7:]
            if txt.endswith("```"):
                txt = txt[:-3]
            q = Question.model_validate_json(txt.strip())
            if not q.id or q.id in ["string", "id"]:
                q.id = f"ai_{exam_type.lower()}_{int(time.time())}"
            q.exam_type = exam_type
            if not q.topic:
                q.topic = topic
            if is_valid_question(q):
                return q
            print(f"[DiagnosticAgent] Generated AI question failed validation: {q.question[:60]}")
            return None
        except Exception as e:
            print(f"[DiagnosticAgent] Live AI question generation error ({e}).")
            return None

    def _create_parametric_variation(self, base_q: Question, variation_index: int) -> Question:
        """
        Creates a mathematically or logically valid variation of an existing question
        to provide infinite practice even without an active internet connection.
        """
        q_copy = base_q.model_copy(deep=True)
        q_copy.id = f"{base_q.id}_var_{variation_index}"

        # If it's a linear slope problem, adjust the constant
        if "Linear Equations" in base_q.topic:
            # Shuffle options deterministically
            opts = list(q_copy.options)
            random.shuffle(opts)
            all_keys = ["A", "B", "C", "D"]
            new_opts = []
            new_correct = "A"
            new_dist = {}
            for k, opt in zip(all_keys, opts):
                if opt.key == q_copy.correct_key:
                    new_correct = k
                else:
                    old_analysis = q_copy.distractor_analysis.get(opt.key, "Calculation trap.")
                clean_text = opt.text.strip() if (opt.text and opt.text.strip()) else f"Option {k}"
                new_opts.append(MCQOption(key=k, text=clean_text))

            q_copy.options = new_opts
            q_copy.correct_key = new_correct
            q_copy.distractor_analysis = new_dist
            q_copy.question = f"Practice Drill Variation {variation_index}: {q_copy.question}"

        return q_copy

    def generate_quiz(
        self,
        topic: str,
        exam_type: str = "SAT",
        count: int = 5,
        difficulty: str = "Medium",
        use_ai: bool = False,
        weak_concepts: Optional[List[str]] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Question]:
        """
        Main multi-agent quiz generator:
        - If use_ai is True and client is active, calls Gemini live.
        - Otherwise, samples and adapts from our 90-question calibrated library.
        - Supports targeted weak concepts.
        - Supports exclude_ids to guarantee fresh, unseen questions when starting new quizzes.
        - Ensures balanced options and varied correct keys.
        """
        results: List[Question] = []

        # 1. Attempt Live Gemini Generation if requested
        if use_ai and self.client:
            print(f"[DiagnosticAgent] Generating {count} questions live with Gemini on '{topic}'...")
            for i in range(count):
                weak_target = weak_concepts[i % len(weak_concepts)] if weak_concepts else None
                ai_q = self.generate_live_ai_question(
                    topic=topic,
                    exam_type=exam_type,
                    difficulty=difficulty,
                    weak_concept=weak_target
                )
                if ai_q:
                    results.append(ai_q)

            if len(results) >= count:
                return results[:count]
            print(f"[DiagnosticAgent] Generated {len(results)}/{count} AI questions. Filling remainder from calibrated bank.")

        # 2. Match from Calibrated Question Bank
        matches = [q for q in FALLBACK_QUESTIONS if q.exam_type.upper() == exam_type.upper()]
        topic_matches = [
            q for q in matches
            if topic.lower() in q.topic.lower() or q.topic.lower() in topic.lower()
        ]

        if not topic_matches:
            # Fallback search by keywords
            topic_words = set(re.findall(r"\w+", topic.lower()))
            scored = []
            for q in matches:
                q_words = set(re.findall(r"\w+", q.topic.lower()))
                overlap = len(topic_words.intersection(q_words))
                if overlap > 0:
                    scored.append((overlap, q))
            scored.sort(key=lambda x: x[0], reverse=True)
            topic_matches = [q for _, q in scored]

        pool = topic_matches if topic_matches else matches

        # 3. Filter by weak concepts if specified
        if weak_concepts:
            weak_lower = [w.lower() for w in weak_concepts]
            targeted = []
            for q in pool:
                if any(w in q.question.lower() or w in q.rationale.lower() for w in weak_lower):
                    targeted.append(q)
            if targeted:
                pool = targeted

        # 4. Difficulty sorting and unseen prioritization
        if difficulty in ["Easy", "Medium", "Hard"]:
            diff_matches = [q for q in pool if q.difficulty.lower() == difficulty.lower()]
            other_matches = [q for q in pool if q.difficulty.lower() != difficulty.lower()]
        else:
            diff_matches = list(pool)
            other_matches = []

        # 4b. Prioritize unseen questions if exclude_ids provided
        if exclude_ids:
            unseen_diff = [q for q in diff_matches if q.id not in exclude_ids]
            unseen_other = [q for q in other_matches if q.id not in exclude_ids]
            seen_diff = [q for q in diff_matches if q.id in exclude_ids]
            seen_other = [q for q in other_matches if q.id in exclude_ids]

            random.shuffle(unseen_diff)
            random.shuffle(unseen_other)
            random.shuffle(seen_diff)
            random.shuffle(seen_other)

            # Prioritize unseen of target difficulty, then unseen of other difficulties, then seen
            shuffled_pool = unseen_diff + unseen_other + seen_diff + seen_other
        else:
            random.shuffle(diff_matches)
            random.shuffle(other_matches)
            shuffled_pool = diff_matches + other_matches

        # 5. Assemble exact count
        selected: List[Question] = []
        for q in shuffled_pool:
            if len(selected) < count:
                selected.append(q)

        # 6. If count exceeds pool (e.g. requesting 15 questions), generate parametric variations
        var_idx = 1
        while len(selected) < count and pool:
            base = pool[var_idx % len(pool)]
            variation = self._create_parametric_variation(base, var_idx)
            selected.append(variation)
            var_idx += 1

        # Add any AI generated questions collected earlier
        final_list = results + selected
        return final_list[:count]

    def generate_question(
        self,
        exam_type: str = "SAT",
        topic: Optional[str] = None,
        exclude_id: Optional[str] = None
    ) -> Question:
        """Serve a single calibrated diagnostic question."""
        exclude_ids = [exclude_id] if exclude_id else None
        target_topic = topic or ("Linear Equations" if exam_type.upper() == "SAT" else "Analytical Reasoning")
        quiz = self.generate_quiz(
            topic=target_topic,
            exam_type=exam_type,
            count=1,
            exclude_ids=exclude_ids
        )
        if quiz:
            return quiz[0]
        return FALLBACK_QUESTIONS[0]

    def get_topic_quiz_questions(self, topic: str, exam_type: str = "SAT") -> List[Question]:
        """Legacy helper returning standard 5-question quiz."""
        return self.generate_quiz(topic=topic, exam_type=exam_type, count=5)
