import json
from pathlib import Path
from typing import Dict, List, Optional
from src.config import STORAGE_DIR
from src.schemas import TopicMastery


class StudentMasteryTracker:
    """
    Tracks topic-level mastery, diagnostic attempts, and mistake patterns.
    Persists data locally in JSON for seamless continuity.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or (STORAGE_DIR / "student_state.json")
        self.masteries: Dict[str, TopicMastery] = {}
        self.history: List[Dict] = []
        self.load()

    def record_attempt(
        self,
        topic: str,
        is_correct: bool,
        error_category: Optional[str] = None,
        misconception: Optional[str] = None,
        question_id: Optional[str] = None
    ):
        """Update mastery scores and record mistake logs."""
        if topic not in self.masteries:
            self.masteries[topic] = TopicMastery(topic=topic)

        m = self.masteries[topic]
        m.attempts += 1
        if is_correct:
            m.correct += 1
        elif error_category and error_category not in m.common_errors:
            m.common_errors.append(error_category)

        m.score_percent = round((m.correct / m.attempts) * 100.0, 1)

        self.history.append({
            "question_id": question_id,
            "topic": topic,
            "is_correct": is_correct,
            "error_category": error_category,
            "misconception": misconception
        })

        self.save()

    def get_weakest_topics(self, limit: int = 3) -> List[str]:
        """Returns the lowest scoring topics that need reinforcement."""
        if not self.masteries:
            return []

        sorted_topics = sorted(
            self.masteries.values(),
            key=lambda tm: (tm.score_percent, -len(tm.common_errors))
        )
        return [tm.topic for tm in sorted_topics[:limit]]

    def get_summary(self) -> Dict[str, Dict]:
        """Returns a clean dictionary of topic masteries."""
        return {
            topic: {
                "attempts": tm.attempts,
                "correct": tm.correct,
                "score_percent": tm.score_percent,
                "common_errors": tm.common_errors
            }
            for topic, tm in self.masteries.items()
        }

    def save(self):
        data = {
            "masteries": {k: v.model_dump() for k, v in self.masteries.items()},
            "history": self.history
        }
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for k, v in data.get("masteries", {}).items():
                    self.masteries[k] = TopicMastery(**v)
                self.history = data.get("history", [])
            except Exception as e:
                print(f"[MasteryTracker] Error loading student state: {e}")
