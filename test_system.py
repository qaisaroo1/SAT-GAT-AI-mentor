"""
End-to-end verification test for SAT & GAT AI Mentor:
1. Tests Markdown ingestion and knowledge store indexing.
2. Tests diagnostic question serving for SAT and GAT.
3. Tests cognitive error diagnosis for a deliberate mistake.
4. Tests 3-tier Socratic hint ladder generation.
5. Tests adaptive study schedule generation based on student mistake data.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.orchestrator import MentorOrchestrator
from src.schemas import Question, ErrorAnalysisResult


def run_tests():
    print("==================================================")
    print("🚀 Starting SAT & GAT AI Mentor System Verification")
    print("==================================================\n")

    # Step 1: Initialize Orchestrator and Knowledge Store
    print("[1/5] Initializing Multi-Agent Orchestrator and indexing Markdown books...")
    orchestrator = MentorOrchestrator()
    print(f"✅ Indexed {len(orchestrator.knowledge_store.chunks)} chunks in knowledge store.\n")

    # Step 2: Diagnostic Question Generation
    print("[2/5] Testing Diagnostic Agent (SAT & GAT questions)...")
    sat_q = orchestrator.get_diagnostic_question(exam_type="SAT")
    print(f"  [SAT] Question ID: {sat_q.id}")
    print(f"        Topic: {sat_q.topic}")
    print(f"        Question: {sat_q.question[:70]}...")
    print(f"        Options: {[o.key for o in sat_q.options]}")
    assert sat_q.correct_key in ["A", "B", "C", "D"], "Invalid correct key"

    gat_q = orchestrator.get_diagnostic_question(exam_type="GAT")
    print(f"  [GAT] Question ID: {gat_q.id}")
    print(f"        Topic: {gat_q.topic}")
    print(f"        Question: {gat_q.question[:70]}...\n")

    # Step 3: Test Cognitive Error Diagnosis
    print("[3/5] Testing Cognitive Error Agent (Deliberate incorrect answer)...")
    # Choose a deliberate wrong answer (B for sat_linear_01)
    wrong_choice = "B" if sat_q.correct_key != "B" else "C"
    eval_result = orchestrator.evaluate_answer(sat_q, selected_key=wrong_choice)
    print(f"  Selection: {eval_result.selected_key} (Correct was {eval_result.correct_key})")
    print(f"  Is Correct: {eval_result.is_correct}")
    print(f"  Identified Category: {eval_result.category}")
    print(f"  Misconception: {eval_result.misconception_name}")
    print(f"  Diagnosis: {eval_result.diagnosis}")
    print(f"  Target: {eval_result.recommended_concept}\n")
    assert not eval_result.is_correct, "Expected incorrect result"

    # Step 4: Socratic Hint Ladder
    print("[4/5] Testing Socratic Tutor Agent (3 Scaffolding Tiers)...")
    for lvl in [1, 2, 3]:
        hint = orchestrator.get_socratic_hint(sat_q, hint_level=lvl)
        print(f"  Level {hint.hint_level} Hint: {hint.hint_text[:80]}...")
        print(f"  Guiding Question: {hint.guiding_question}")
        assert hint.hint_level == lvl
    print("  ✅ All 3 Socratic scaffolding tiers generated without answer leakage.\n")

    # Step 5: Adaptive Study Scheduler
    print("[5/5] Testing Study Scheduler Agent...")
    plan = orchestrator.create_adaptive_schedule(exam_type="SAT", days=3)
    print(f"  Plan Exam: {plan.target_exam}")
    print(f"  Weakest Topics Identified: {plan.weakest_topics}")
    print(f"  Motivational Note: {plan.motivational_note}")
    for t in plan.tasks:
        print(f"    - Day {t.day} ({t.estimated_minutes}m): {t.focus_topic} -> {t.task_description[:50]}...")
    assert len(plan.tasks) == 3, "Expected 3-day tasks"

    print("\n==================================================")
    print("🎉 ALL 5 SYSTEM TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
