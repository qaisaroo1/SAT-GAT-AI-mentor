from typing import List, Optional
from src.config import GEMINI_API_KEY, DEFAULT_MODEL
from src.schemas import StudyPlan, DailyTask
from src.state.mastery import StudentMasteryTracker

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


class StudySchedulerAgent:
    """
    Dynamic Study Scheduler Agent:
    Evaluates student topic mastery and recurring error patterns to construct
    an adaptive, high-impact daily study itinerary.
    """

    def __init__(self):
        self.client = None
        if GEMINI_API_KEY and genai:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"[StudySchedulerAgent] Client error: {e}")

    def generate_plan(self, tracker: StudentMasteryTracker, exam_type: str = "SAT", days: int = 3) -> StudyPlan:
        """Generates a personalized daily schedule based on weak areas."""
        weak_topics = tracker.get_weakest_topics(limit=3)
        summary = tracker.get_summary()

        if not weak_topics:
            if exam_type.upper() == "SAT":
                weak_topics = ["Linear Equations and Slope-Intercept Form", "Geometry: Circles in the Coordinate Plane"]
            else:
                weak_topics = ["Linear Sequencing Puzzles", "Grouping and Selection Problems"]

        # Clean friendly topic names
        def clean_topic_name(name: str) -> str:
            if "Linear Equations" in name:
                return "Linear Equations"
            if "Circles" in name:
                return "Circle Geometry"
            if "Quadratic" in name:
                return "Quadratic Functions"
            if "Sequencing" in name:
                return "Logic Sequencing"
            if "Grouping" in name:
                return "Grouping Rules"
            return name

        t1 = clean_topic_name(weak_topics[0])
        t2 = clean_topic_name(weak_topics[1] if len(weak_topics) > 1 else weak_topics[0])

        # Simple everyday tasks
        default_tasks = [
            DailyTask(
                day=1,
                focus_topic=t1,
                task_description=f"• Read the main formulas for {t1} (10 mins)\n• Solve 5 practice questions to build confidence (20 mins)",
                estimated_minutes=30
            ),
            DailyTask(
                day=2,
                focus_topic=t2,
                task_description=f"• Review the top exam tricks for {t2} (10 mins)\n• Try 4 quick questions without looking at hints (20 mins)",
                estimated_minutes=30
            ),
            DailyTask(
                day=3,
                focus_topic="Quick Practice Quiz",
                task_description="• Take a 15-minute quick test on both topics to see your improvement!",
                estimated_minutes=20
            )
        ]

        if not self.client:
            return StudyPlan(
                target_exam=exam_type,
                weakest_topics=weak_topics,
                tasks=default_tasks[:days],
                motivational_note="Practice 20-30 minutes a day and you'll see huge improvement!"
            )

        prompt = f"""
You are an expert test prep academic advisor for {exam_type}.
Based on the student's mastery profile below, create an actionable {days}-day personalized study sprint.

STUDENT MASTERY DATA:
{summary}

PRIORITY WEAK TOPICS:
{', '.join(weak_topics)}

REQUIREMENTS:
1. Provide exactly {days} daily tasks focused on targeting their weakest topics and cognitive traps.
2. Include estimated minutes (20-45 mins per day).
3. Include a motivating, realistic closing encouragement.

Return strictly valid JSON adhering to this exact schema:
{{
  "target_exam": "{exam_type}",
  "weakest_topics": {weak_topics},
  "tasks": [
    {{
      "day": 1,
      "focus_topic": "{t1}",
      "task_description": "Review core concepts and solve targeted practice problems",
      "estimated_minutes": 30
    }}
  ],
  "motivational_note": "A motivating, encouraging message."
}}
"""

        try:
            response = self.client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            txt = response.text.strip()
            if txt.startswith("```json"):
                txt = txt[7:]
            if txt.endswith("```"):
                txt = txt[:-3]
            return StudyPlan.model_validate_json(txt.strip())
        except Exception as e:
            print(f"[StudySchedulerAgent] Plan error ({e}). Returning calibrated schedule.")
            return StudyPlan(
                target_exam=exam_type,
                weakest_topics=weak_topics,
                tasks=default_tasks[:days],
                motivational_note="Every mistake is simply diagnostic data to help you improve."
            )
