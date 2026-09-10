from typing import Optional
from src.config import GEMINI_API_KEY, DEFAULT_MODEL
from src.schemas import Question, ErrorAnalysisResult, ErrorCategory

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


class CognitiveErrorAgent:
    """
    Cognitive Error Analysis Agent:
    Diagnoses WHY a student answered incorrectly. Dissects misconceptions,
    identifies trap patterns, and provides actionable remediation targets.
    """

    def __init__(self):
        self.client = None
        if GEMINI_API_KEY and genai:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"[CognitiveErrorAgent] Client error: {e}")

    def analyze(self, question: Question, selected_key: str, student_notes: Optional[str] = None) -> ErrorAnalysisResult:
        """Evaluate student selection and classify the cognitive error."""
        is_correct = (selected_key.strip().upper() == question.correct_key.strip().upper())

        if is_correct:
            return ErrorAnalysisResult(
                is_correct=True,
                selected_key=selected_key,
                correct_key=question.correct_key,
                category=None,
                diagnosis="Correct! Excellent mastery of this concept.",
                misconception_name="None",
                recommended_concept=f"Proceed to next difficulty level in {question.topic}"
            )

        # Distractor rationale from question metadata
        distractor_hint = question.distractor_analysis.get(
            selected_key.upper(),
            "Selected an incorrect option reflecting an underlying conceptual or procedural error."
        )

        # Default classification based on common patterns
        category = ErrorCategory.TRAP_DISTRACTOR
        lower_hint = distractor_hint.lower()
        if "formula" in lower_hint or "rule" in lower_hint or "concept" in lower_hint:
            category = ErrorCategory.CONCEPTUAL_GAP
        elif "sign" in lower_hint or "arithmetic" in lower_hint or "calculation" in lower_hint:
            category = ErrorCategory.CALCULATION_ERROR
        elif "constraint" in lower_hint or "explicit" in lower_hint or "premise" in lower_hint:
            category = ErrorCategory.PREMISE_MISREAD

        # Clean up LaTeX dollar symbols for friendly display
        clean_hint = distractor_hint.replace("$r^2$", "r²").replace("$r$", "r").replace("$", "")

        if not self.client:
            return ErrorAnalysisResult(
                is_correct=False,
                selected_key=selected_key,
                correct_key=question.correct_key,
                category=category,
                diagnosis=clean_hint,
                misconception_name=f"{category.value}",
                recommended_concept=f"Review section on '{question.topic}'"
            )

        prompt = f"""
You are a cognitive assessment specialist analyzing a student's mistake on an exam question ({question.exam_type}).

QUESTION:
{question.question}

OPTIONS:
{chr(10).join([f"{opt.key}: {opt.text}" for opt in question.options])}

CORRECT OPTION: {question.correct_key}
STUDENT SELECTED: {selected_key}
KNOWN DISTRACTOR CONTEXT: {distractor_hint}
STUDENT WORK/NOTES: {student_notes or 'None provided'}

TASK:
1. Explain WHY the student made this choice (the underlying thought process or flawed assumption).
2. Classify into category: MUST be exactly one of: 'Missing Formula or Rule', 'Fell for a Common Exam Trick', 'Math Calculation Slip', 'Misread the Question'.
3. Name the specific misconception (e.g. 'Inverted Slope', 'Converse Fallacy', 'Radius vs Area Confusion').
4. Specify the exact concept section to review.

Return strictly valid JSON adhering to this exact schema:
{{
  "is_correct": false,
  "selected_key": "{selected_key}",
  "correct_key": "{question.correct_key}",
  "category": "Missing Formula or Rule",
  "diagnosis": "Detailed reason why the student made this choice",
  "misconception_name": "Specific misconception name",
  "recommended_concept": "Concept section to review"
}}
"""

        try:
            response = self.client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            txt = response.text.strip()
            if txt.startswith("```json"):
                txt = txt[7:]
            if txt.endswith("```"):
                txt = txt[:-3]
            return ErrorAnalysisResult.model_validate_json(txt.strip())
        except Exception as e:
            print(f"[CognitiveErrorAgent] Analysis error ({e}). Using deterministic rule.")
            return ErrorAnalysisResult(
                is_correct=False,
                selected_key=selected_key,
                correct_key=question.correct_key,
                category=category,
                diagnosis=distractor_hint,
                misconception_name=f"{category.value}",
                recommended_concept=f"Review {question.topic}"
            )
