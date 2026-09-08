from typing import Optional, Dict, Any, List
from src.ingestion import KnowledgeStore, initialize_default_knowledge_base
from src.state.mastery import StudentMasteryTracker
from src.agents.diagnostic_agent import DiagnosticAgent
from src.agents.error_agent import CognitiveErrorAgent
from src.agents.socratic_agent import SocraticTutorAgent
from src.agents.scheduler_agent import StudySchedulerAgent
from src.schemas import Question, ErrorAnalysisResult, SocraticHint, StudyPlan


class MentorOrchestrator:
    """
    Central Multi-Agent Coordinator for the SAT & GAT AI Mentor.
    Connects knowledge ingestion, assessment, error diagnosis, Socratic tutoring,
    and adaptive scheduling into a seamless learning loop.
    """

    def __init__(self):
        self.knowledge_store = initialize_default_knowledge_base()
        self.tracker = StudentMasteryTracker()
        self.diagnostic_agent = DiagnosticAgent(self.knowledge_store)
        self.error_agent = CognitiveErrorAgent()
        self.socratic_agent = SocraticTutorAgent()
        self.scheduler_agent = StudySchedulerAgent()

    def get_available_topics(self, exam_type: str = "SAT") -> List[str]:
        """Fetch all available syllabus topics from the indexed prep books."""
        raw_topics = self.knowledge_store.get_topics_by_exam(exam_type)
        
        # Standard curated high-yield topics
        if exam_type.upper() == "SAT":
            curated = [
                "Linear Equations and Slope-Intercept Form",
                "Systems of Linear Equations",
                "Quadratic Functions and Parabola Properties",
                "Geometry: Circles in the Coordinate Plane"
            ]
            # Check if official College Board sample questions are indexed
            has_official_pdf = any("Section / Page" in str(t) for t in raw_topics)
            if has_official_pdf:
                curated.append("Digital SAT: Reading & Writing (Official College Board)")
                curated.append("Digital SAT: Math & Problem Solving (Official College Board)")
            return curated
        else:
            return [
                "Linear Sequencing Puzzles",
                "Grouping and Selection Problems",
                "Sample Analytical Scenario: University Department Presentations"
            ]

    def get_topic_lesson(self, topic: str, exam_type: str = "SAT") -> str:
        """Fetch curated curriculum lesson text in simple, friendly English."""
        if "Reading & Writing" in topic:
            return """
### 📚 Digital SAT Reading & Writing: Comprehensive Guide

The Digital SAT combines Reading and Writing into **54 questions across two 32-minute modules**. Every question features a concise, focused passage (25 to 150 words) with exactly **one question**.

---

### 🏛️ The 4 Official Content Domains

#### 1. Information and Ideas (~26% of the exam)
This domain tests your ability to comprehend, analyze, and synthesize information:
* **Central Ideas and Details:** Identify the primary argument or locate key supporting facts.
* **Command of Evidence (Textual & Quantitative):** Choose which sentence or chart data strengthens or weakens an argument.
* **Inferences:** Determine the most logical conclusion to complete a passage.

#### 2. Craft and Structure (~28% of the exam)
This domain evaluates vocabulary, comprehension of rhetoric, and multi-text reasoning:
* **Words in Context:** Determine the exact meaning of a high-utility word based on tone and surrounding clues.
* **Text Structure and Purpose:** Explain *why* the author wrote a particular sentence or how the argument progresses.
* **Cross-Text Connections:** Compare two authors with differing viewpoints on the same historical, literary, or scientific subject.

#### 3. Expression of Ideas (~20% of the exam)
This domain tests effective revision and logical organization:
* **Transitions:** Choose the best transitional word (*Therefore*, *However*, *Moreover*, *Specifically*).
* **Rhetorical Synthesis:** You are given bulleted student research notes and must select the single choice that accomplishes a specific assigned writing goal (e.g., *"emphasize a similarity"* or *"introduce a researcher"*).

#### 4. Standard English Conventions (~26% of the exam)
This domain tests core grammar and sentence mechanics:
* **Sentence Boundaries:** Correctly using periods, semicolons, colons, and dashes to prevent comma splices and run-ons.
* **Agreement & Modifiers:** Ensuring subjects match verbs, pronoun references are unambiguous, and modifying phrases are placed directly next to what they describe.

---

### ⚠️ Top 4 Exam Traps to Watch Out For
1. **The "Too Extreme" Trap:** Be skeptical of options using absolute words like *always*, *never*, *impossible*, or *completely* when the author only used moderate words like *often* or *suggests*.
2. **The "Real-World True" Trap:** An option might be a scientifically true fact in the real world, but if it is NOT directly stated or supported in the passage, it is **wrong**.
3. **The "Half-Right, Half-Wrong" Trap:** An option might start off with phrases identical to the text, but twist the final two words into something incorrect. Read all four options completely!
4. **The False Transition Trap:** Remember: *Therefore* indicates a direct result or consequence; *Moreover* adds another supporting point; *However* introduces a contrast or counter-argument.

---

### 📝 Complete Walkthrough Example (From Official College Board)

**Passage:**
> *"To dye wool, Navajo (Diné) weaver Lillie Taylor uses plants and vegetables from Arizona, where she lives. For example, she achieved the deep reds and browns featured in her 2003 rug 'In the Path of the Four Seasons' by using Arizona dock roots, drying and grinding them before mixing the powder with water to create a dye bath. To intensify the appearance of certain colors, Taylor also sometimes mixes in clay obtained from nearby soil."*

**Question:** Which choice best states the main idea of the text?
* **A)** *Reds and browns are not commonly featured in most of Taylor's rugs.* ❌ **(Trap: Opposite of passage)** The passage says she famously used them, not that they are unusual.
* **B)** *In the Path of the Four Seasons is widely acclaimed for its innovative weaving techniques.* ❌ **(Trap: Not in text)** The passage mentions the rug, but never claims it is "widely acclaimed" or discusses "weaving techniques".
* **C)** *Taylor draws on local resources in the approach she uses to dye wool.* ✅ **(CORRECT)** Summarizes the central point: she uses local Arizona dock roots, plants, and nearby soil clay.
* **D)** *Taylor finds it difficult to locate Arizona dock root in the desert.* ❌ **(Trap: Unsupported assumption)** The passage never mentions any difficulty in finding roots.
"""
        elif "Math & Problem Solving" in topic:
            return """
### 📌 What This Section Tests
The SAT Math section tests 4 main areas:
* **Algebra:** Linear equations ($y = mx + b$) and systems of equations.
* **Advanced Math:** Quadratics ($ax^2 + bx + c$) and parabolas.
* **Geometry:** Circles in the coordinate plane and triangles.
* **Word Problems:** Percentages, ratios, and rates.

---

### 💡 Top 3 Simple Strategies
1. **Reread the Target:** Did the question ask for $x$, or for $x + 2$, or the radius $r$?
2. **Watch the Negative Signs:** For perpendicular slopes, flip the fraction AND change the sign ($1/2 \implies -2$).
3. **Radius vs Area Trap:** In circle equations, the right side is $r^2$. Always take the square root to find $r$!
"""

        # For specific math chapters, fetch from knowledge store
        content = self.knowledge_store.get_topic_content(topic, exam_type)
        # Clean any raw Section / Page header artifacts
        clean_content = content.replace("## Section / Page", "### Section")
        return clean_content

    def get_diagnostic_question(
        self, 
        exam_type: str = "SAT", 
        topic: Optional[str] = None,
        exclude_id: Optional[str] = None
    ) -> Question:
        """Step 1: Serve a calibrated diagnostic question."""
        return self.diagnostic_agent.generate_question(
            exam_type=exam_type, 
            topic=topic,
            exclude_id=exclude_id
        )

    def get_topic_quiz(self, topic: str, exam_type: str = "SAT") -> List[Question]:
        """Fetch full 5-question calibrated quiz set for a specific topic."""
        return self.diagnostic_agent.get_topic_quiz_questions(topic=topic, exam_type=exam_type)

    def get_custom_quiz(
        self,
        topic: str,
        exam_type: str = "SAT",
        count: int = 5,
        difficulty: str = "Medium",
        use_ai: bool = False,
        weak_concepts: Optional[List[str]] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Question]:
        """Dynamically generate or select a custom quiz with variable count, difficulty, and AI options."""
        return self.diagnostic_agent.generate_quiz(
            topic=topic,
            exam_type=exam_type,
            count=count,
            difficulty=difficulty,
            use_ai=use_ai,
            weak_concepts=weak_concepts,
            exclude_ids=exclude_ids
        )

    def set_api_key(self, api_key: str) -> bool:
        """Update API key across all LLM agents."""
        return self.diagnostic_agent.set_api_key(api_key)

    def evaluate_answer(
        self,
        question: Question,
        selected_key: str,
        student_notes: Optional[str] = None
    ) -> ErrorAnalysisResult:
        """Step 2: Diagnose the answer and update student mastery profile."""
        result = self.error_agent.analyze(question, selected_key, student_notes)

        # Update persistent mastery state
        self.tracker.record_attempt(
            topic=question.topic,
            is_correct=result.is_correct,
            error_category=result.category.value if result.category else None,
            misconception=result.misconception_name,
            question_id=question.id
        )

        return result

    def get_socratic_hint(
        self,
        question: Question,
        hint_level: int = 1,
        student_mistake: Optional[str] = None
    ) -> SocraticHint:
        """Step 3: Provide guided Socratic hint without revealing answers."""
        return self.socratic_agent.generate_hint(
            question=question,
            student_mistake=student_mistake,
            hint_level=hint_level
        )

    def create_adaptive_schedule(self, exam_type: str = "SAT", days: int = 3) -> StudyPlan:
        """Step 4: Generate prioritized daily study itinerary."""
        return self.scheduler_agent.generate_plan(self.tracker, exam_type=exam_type, days=days)

    def get_student_mastery_stats(self) -> Dict[str, Any]:
        """Returns student mastery percentages and weakest topics."""
        return {
            "summary": self.tracker.get_summary(),
            "weakest_topics": self.tracker.get_weakest_topics(limit=3)
        }
