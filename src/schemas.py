from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    CONCEPTUAL_GAP = "Missing Formula or Rule"
    TRAP_DISTRACTOR = "Fell for a Common Exam Trick"
    CALCULATION_ERROR = "Math Calculation Slip"
    PREMISE_MISREAD = "Misread the Question"


class MCQOption(BaseModel):
    key: str = Field(description="Option letter, e.g. A, B, C, D")
    text: str = Field(description="The option content text")


class Question(BaseModel):
    id: str = Field(description="Unique question identifier")
    exam_type: str = Field(description="SAT or GAT")
    topic: str = Field(description="Topic name, e.g. Linear Equations, Logic Sequencing")
    difficulty: str = Field(description="Easy, Medium, or Hard")
    question: str = Field(description="The question prompt or analytical puzzle premise")
    options: List[MCQOption] = Field(description="List of multiple-choice options")
    correct_key: str = Field(description="The correct option key (e.g. A, B, C, or D)")
    rationale: str = Field(description="Detailed explanation of the correct answer")
    distractor_analysis: Dict[str, str] = Field(
        default_factory=dict,
        description="Explanation of the misconception or error represented by each distractor key"
    )


class ErrorAnalysisResult(BaseModel):
    is_correct: bool
    selected_key: str
    correct_key: str
    category: Optional[ErrorCategory] = None
    diagnosis: str = Field(description="Clear explanation of WHY the student made this choice")
    misconception_name: str = Field(description="Specific misconception (e.g. Inverted Slope, Converse Fallacy)")
    recommended_concept: str = Field(description="The exact topic section the student must review")


class TopicMastery(BaseModel):
    topic: str
    attempts: int = 0
    correct: int = 0
    score_percent: float = 0.0
    common_errors: List[str] = Field(default_factory=list)


class DailyTask(BaseModel):
    day: int = Field(description="Day number in schedule, e.g. 1, 2, 3")
    focus_topic: str = Field(description="Specific weak topic to drill")
    task_description: str = Field(description="Concrete action (e.g. Review Circle Standard Form & solve 5 drill questions)")
    estimated_minutes: int = Field(default=30)


class StudyPlan(BaseModel):
    target_exam: str
    weakest_topics: List[str]
    tasks: List[DailyTask]
    motivational_note: str


class SocraticHint(BaseModel):
    hint_level: int = Field(description="1 (Nudge), 2 (Scaffold), or 3 (Step-Through)")
    hint_text: str = Field(description="The pedagogical guidance without revealing the answer")
    guiding_question: str = Field(description="A thought-provoking question prompting the student's next step")
