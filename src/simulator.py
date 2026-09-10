import json
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from src.schemas import Question, MCQOption, ExamSimulationConfig, ScaledExamScore
from src.config import STORAGE_DIR, DATA_DIR


class ExamSimulator:
    """
    Official Exam Simulator Engine for SAT and GAT General:
    - Builds authentic 98-question SAT or 100-question GAT exams (Full mode)
    - Builds authentic 49-question SAT or 50-question GAT mocks (Half mode)
    - Distributes questions across authentic sections (RW & Math for SAT; Verbal, Quant, Analytical for GAT)
    - Calculates official scaled scores (400-1600 SAT, 0-100 GAT) and section sub-scores
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or STORAGE_DIR
        self.base_questions: List[Question] = self._load_base_questions()

    def _load_base_questions(self) -> List[Question]:
        json_path = self.storage_dir / "topic_questions.json"
        if json_path.exists():
            try:
                raw = json.loads(json_path.read_text(encoding="utf-8"))
                valid = []
                for q_dict in raw:
                    try:
                        q = Question.model_validate(q_dict)
                        # Sanitize: ensure no empty options and complete stems
                        has_empty = any(not opt.text or not opt.text.strip() for opt in q.options)
                        q_str = q.question.strip()
                        if not has_empty and len(q_str) >= 20 and not q_str.endswith(",") and "costs ." not in q_str and "for ." not in q_str:
                            valid.append(q)
                    except Exception:
                        pass
                return valid
            except Exception as e:
                print(f"[ExamSimulator] Error loading topic_questions: {e}")
        return []

    def get_config(self, exam_type: str, length_mode: str = "full") -> ExamSimulationConfig:
        exam_upper = exam_type.upper()
        mode_lower = length_mode.lower()

        if exam_upper == "SAT":
            if mode_lower == "half":
                return ExamSimulationConfig(
                    exam_type="SAT",
                    length_mode="half",
                    total_questions=49,
                    duration_minutes=67,
                    sections=["Reading & Writing (27 Qs)", "Math (22 Qs)"]
                )
            else:
                return ExamSimulationConfig(
                    exam_type="SAT",
                    length_mode="full",
                    total_questions=98,
                    duration_minutes=134,
                    sections=["Reading & Writing (54 Qs)", "Math (44 Qs)"]
                )
        else:  # GAT
            if mode_lower == "half":
                return ExamSimulationConfig(
                    exam_type="GAT",
                    length_mode="half",
                    total_questions=50,
                    duration_minutes=60,
                    sections=["Verbal Reasoning (20 Qs)", "Quantitative Reasoning (18 Qs)", "Analytical Reasoning (12 Qs)"]
                )
            else:
                return ExamSimulationConfig(
                    exam_type="GAT",
                    length_mode="full",
                    total_questions=100,
                    duration_minutes=120,
                    sections=["Verbal Reasoning (40 Qs)", "Quantitative Reasoning (35 Qs)", "Analytical Reasoning (25 Qs)"]
                )

    def _create_variation(self, base_q: Question, idx: int, prefix: str) -> Question:
        q_copy = base_q.model_copy(deep=True)
        q_copy.id = f"{prefix}_{base_q.id}_v{idx}"

        # Deterministic shuffle based on seed
        rng = random.Random(hash(f"{q_copy.id}_{idx}"))
        opts = list(q_copy.options)
        rng.shuffle(opts)

        keys = ["A", "B", "C", "D"]
        new_opts = []
        new_correct = "A"
        new_distractor_analysis = {}

        for k, opt in zip(keys, opts):
            if opt.key == q_copy.correct_key:
                new_correct = k
            else:
                old_analysis = q_copy.distractor_analysis.get(opt.key, "Selected alternative distractor trap.")
                new_distractor_analysis[k] = old_analysis
            clean_txt = opt.text.strip() if (opt.text and opt.text.strip()) else f"Option {k}"
            new_opts.append(MCQOption(key=k, text=clean_txt))

        q_copy.options = new_opts
        q_copy.correct_key = new_correct
        q_copy.distractor_analysis = new_distractor_analysis
        return q_copy

    def assemble_exam(self, exam_type: str, length_mode: str = "full") -> List[Question]:
        exam_upper = exam_type.upper()
        mode_lower = length_mode.lower()
        exam_questions: List[Question] = []

        if exam_upper == "SAT":
            rw_target = 27 if mode_lower == "half" else 54
            math_target = 22 if mode_lower == "half" else 44

            sat_qs = [q for q in self.base_questions if q.exam_type.upper() == "SAT"]
            rw_pool = [q for q in sat_qs if "Reading" in q.topic or "Writing" in q.topic]
            math_pool = [q for q in sat_qs if "Reading" not in q.topic and "Writing" not in q.topic]

            if not rw_pool:
                rw_pool = sat_qs[:10]
            if not math_pool:
                math_pool = sat_qs[10:] if len(sat_qs) > 10 else sat_qs

            # 1. Fill Reading & Writing Section
            rw_selected = []
            for i in range(rw_target):
                base = rw_pool[i % len(rw_pool)]
                if i < len(rw_pool):
                    rw_selected.append(base.model_copy(deep=True))
                else:
                    rw_selected.append(self._create_variation(base, i, "sat_rw"))
            random.Random(42).shuffle(rw_selected)

            # 2. Fill Math Section
            math_selected = []
            for i in range(math_target):
                base = math_pool[i % len(math_pool)]
                if i < len(math_pool):
                    math_selected.append(base.model_copy(deep=True))
                else:
                    math_selected.append(self._create_variation(base, i, "sat_math"))
            random.Random(84).shuffle(math_selected)

            exam_questions = rw_selected + math_selected

        else:  # GAT General
            v_target = 20 if mode_lower == "half" else 40
            q_target = 18 if mode_lower == "half" else 35
            a_target = 12 if mode_lower == "half" else 25

            gat_qs = [q for q in self.base_questions if q.exam_type.upper() == "GAT"]
            ana_pool = [q for q in gat_qs if "Analytical" in q.topic or "Sequencing" in q.topic or "Grouping" in q.topic]
            verbal_pool = [q for q in gat_qs if "Verbal" in q.topic or "English" in q.topic or "Reading" in q.topic]
            quant_pool = [q for q in gat_qs if "Quantitative" in q.topic or "Math" in q.topic or "Arithmetic" in q.topic or "Equations" in q.topic]

            if not ana_pool:
                ana_pool = gat_qs if gat_qs else self.base_questions[:10]
            if not verbal_pool:
                verbal_pool = [q for q in self.base_questions if "Reading" in q.topic or "Writing" in q.topic] or ana_pool
            if not quant_pool:
                quant_pool = [q for q in self.base_questions if "Linear" in q.topic or "Quadratic" in q.topic or "Geometry" in q.topic] or ana_pool

            # Assemble Verbal
            verbal_selected = []
            for i in range(v_target):
                base = verbal_pool[i % len(verbal_pool)]
                if i < len(verbal_pool):
                    verbal_selected.append(base.model_copy(deep=True))
                else:
                    verbal_selected.append(self._create_variation(base, i, "gat_v"))

            # Assemble Quantitative
            quant_selected = []
            for i in range(q_target):
                base = quant_pool[i % len(quant_pool)]
                if i < len(quant_pool):
                    quant_selected.append(base.model_copy(deep=True))
                else:
                    quant_selected.append(self._create_variation(base, i, "gat_q"))

            # Assemble Analytical
            ana_selected = []
            for i in range(a_target):
                base = ana_pool[i % len(ana_pool)]
                if i < len(ana_pool):
                    ana_selected.append(base.model_copy(deep=True))
                else:
                    ana_selected.append(self._create_variation(base, i, "gat_a"))

            exam_questions = verbal_selected + quant_selected + ana_selected

        return exam_questions

    def score_exam(
        self,
        config: ExamSimulationConfig,
        questions: List[Question],
        user_answers: Dict[int, str]
    ) -> ScaledExamScore:
        total_q = len(questions)
        attempted = sum(1 for idx in range(total_q) if idx in user_answers and user_answers[idx])
        correct_count = sum(1 for idx, q in enumerate(questions) if user_answers.get(idx) == q.correct_key)
        raw_pct = (correct_count / total_q * 100.0) if total_q > 0 else 0.0

        section_metrics: Dict[str, Dict[str, Any]] = {}
        topic_mistakes: Dict[str, int] = {}

        if config.exam_type.upper() == "SAT":
            rw_cutoff = 27 if config.length_mode == "half" else 54
            rw_qs = questions[:rw_cutoff]
            math_qs = questions[rw_cutoff:]

            rw_correct = sum(1 for idx, q in enumerate(rw_qs) if user_answers.get(idx) == q.correct_key)
            math_correct = sum(1 for idx, q in enumerate(math_qs) if user_answers.get(rw_cutoff + idx) == q.correct_key)

            rw_total = len(rw_qs)
            math_total = len(math_qs)

            rw_scaled = int(200 + (rw_correct / rw_total * 600)) if rw_total > 0 else 200
            math_scaled = int(200 + (math_correct / math_total * 600)) if math_total > 0 else 200
            total_scaled = rw_scaled + math_scaled

            section_metrics["Reading & Writing"] = {
                "total": rw_total,
                "correct": rw_correct,
                "percent": round((rw_correct / rw_total * 100.0), 1) if rw_total > 0 else 0,
                "scaled_score": rw_scaled,
                "max_score": 800
            }
            section_metrics["Math"] = {
                "total": math_total,
                "correct": math_correct,
                "percent": round((math_correct / math_total * 100.0), 1) if math_total > 0 else 0,
                "scaled_score": math_scaled,
                "max_score": 800
            }

            max_scaled = 1600
            if total_scaled >= 1450:
                percentile = "98th - 99th Percentile"
                readiness = "🌟 Elite / Top University Ready (Ivy & Tier 1)"
            elif total_scaled >= 1300:
                percentile = "86th - 92nd Percentile"
                readiness = "🎯 Highly Competitive (Top 10% Nationwide)"
            elif total_scaled >= 1150:
                percentile = "65th - 75th Percentile"
                readiness = "📈 Solid Foundation (Selective Colleges)"
            elif total_scaled >= 950:
                percentile = "40th - 50th Percentile"
                readiness = "⚠️ Moderate (Focus on Math & Grammar Traps)"
            else:
                percentile = "Below 35th Percentile"
                readiness = "🚨 Core Remediation Needed"

        else:  # GAT General
            v_cutoff = 20 if config.length_mode == "half" else 40
            q_cutoff = v_cutoff + (18 if config.length_mode == "half" else 35)

            v_qs = questions[:v_cutoff]
            q_qs = questions[v_cutoff:q_cutoff]
            a_qs = questions[q_cutoff:]

            v_correct = sum(1 for idx, q in enumerate(v_qs) if user_answers.get(idx) == q.correct_key)
            q_correct = sum(1 for idx, q in enumerate(q_qs) if user_answers.get(v_cutoff + idx) == q.correct_key)
            a_correct = sum(1 for idx, q in enumerate(a_qs) if user_answers.get(q_cutoff + idx) == q.correct_key)

            v_total = len(v_qs)
            q_total = len(q_qs)
            a_total = len(a_qs)

            total_scaled = int(round(raw_pct))
            max_scaled = 100

            section_metrics["Verbal Reasoning"] = {
                "total": v_total,
                "correct": v_correct,
                "percent": round((v_correct / v_total * 100.0), 1) if v_total > 0 else 0,
                "scaled_score": v_correct if config.length_mode == "full" else int(v_correct * 2),
                "max_score": 40 if config.length_mode == "full" else 40
            }
            section_metrics["Quantitative Reasoning"] = {
                "total": q_total,
                "correct": q_correct,
                "percent": round((q_correct / q_total * 100.0), 1) if q_total > 0 else 0,
                "scaled_score": q_correct if config.length_mode == "full" else int(q_correct * 2),
                "max_score": 35 if config.length_mode == "full" else 35
            }
            section_metrics["Analytical Reasoning"] = {
                "total": a_total,
                "correct": a_correct,
                "percent": round((a_correct / a_total * 100.0), 1) if a_total > 0 else 0,
                "scaled_score": a_correct if config.length_mode == "full" else int(a_correct * 2),
                "max_score": 25 if config.length_mode == "full" else 25
            }

            if total_scaled >= 80:
                percentile = "95th+ Percentile"
                readiness = "🌟 Outstanding (Top MS/MPhil & PhD Eligibility)"
            elif total_scaled >= 70:
                percentile = "85th - 94th Percentile"
                readiness = "🎯 High Merit (Competitive for Direct HEC Scholarships)"
            elif total_scaled >= 50:
                percentile = "50th - 70th Percentile"
                readiness = "✅ Qualified (Meets General University Passing Threshold)"
            else:
                percentile = "Below 50th Percentile"
                readiness = "⚠️ Below Passing Cutoff (50 marks required for NTS GAT)"

        # Identify weak topics
        for idx, q in enumerate(questions):
            ans = user_answers.get(idx)
            if ans != q.correct_key:
                topic_mistakes[q.topic] = topic_mistakes.get(q.topic, 0) + 1

        sorted_weak = sorted(topic_mistakes.items(), key=lambda x: x[1], reverse=True)
        weak_topics = [t for t, _ in sorted_weak[:3]]
        if not weak_topics and len(questions) > 0:
            weak_topics = ["No major weak topics found! Excellent performance."]

        rec = f"Focus next revision on: {', '.join(weak_topics[:2])}. Use the 3-day adaptive sprint to shore up these topics."

        return ScaledExamScore(
            exam_type=config.exam_type,
            length_mode=config.length_mode,
            total_questions=total_q,
            attempted_count=attempted,
            correct_count=correct_count,
            raw_score_percent=round(raw_pct, 1),
            scaled_score=total_scaled,
            max_scaled_score=max_scaled,
            section_breakdown=section_metrics,
            percentile_estimate=percentile,
            readiness_level=readiness,
            weak_topics=weak_topics,
            recommendation=rec
        )
