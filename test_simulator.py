import sys
from pathlib import Path

# Ensure UTF-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.orchestrator import MentorOrchestrator


def run_simulator_tests():
    print("=" * 55)
    print("🎯 Testing Official SAT & GAT Full Exam Simulator Engine")
    print("=" * 55)

    orch = MentorOrchestrator()

    # 1. SAT Full Simulation Test
    print("\n[1/4] Testing SAT Full Simulation (98 Questions, 134 Mins)...")
    sat_full_cfg, sat_full_qs = orch.start_exam_simulation("SAT", length_mode="full")
    assert len(sat_full_qs) == 98, f"Expected 98 questions, got {len(sat_full_qs)}"
    assert sat_full_cfg.duration_minutes == 134, f"Expected 134 mins, got {sat_full_cfg.duration_minutes}"
    rw_count = sum(1 for q in sat_full_qs if "Reading" in q.topic or "Writing" in q.topic or "sat_rw" in q.id)
    print(f"  ✅ SAT Full generated: {len(sat_full_qs)} questions ({rw_count} Reading/Writing, {98 - rw_count} Math)")

    # 2. SAT Half-Length Mock Test
    print("\n[2/4] Testing SAT Half-Length Mock (49 Questions, 67 Mins)...")
    sat_half_cfg, sat_half_qs = orch.start_exam_simulation("SAT", length_mode="half")
    assert len(sat_half_qs) == 49, f"Expected 49 questions, got {len(sat_half_qs)}"
    assert sat_half_cfg.duration_minutes == 67, f"Expected 67 mins, got {sat_half_cfg.duration_minutes}"
    print(f"  ✅ SAT Half-Mock generated: {len(sat_half_qs)} questions")

    # 3. GAT Full & Half Simulation Test
    print("\n[3/4] Testing GAT Full (100 Questions) and Half (50 Questions)...")
    gat_full_cfg, gat_full_qs = orch.start_exam_simulation("GAT", length_mode="full")
    assert len(gat_full_qs) == 100, f"Expected 100 questions, got {len(gat_full_qs)}"
    assert gat_full_cfg.duration_minutes == 120, f"Expected 120 mins, got {gat_full_cfg.duration_minutes}"

    gat_half_cfg, gat_half_qs = orch.start_exam_simulation("GAT", length_mode="half")
    assert len(gat_half_qs) == 50, f"Expected 50 questions, got {len(gat_half_qs)}"
    assert gat_half_cfg.duration_minutes == 60, f"Expected 60 mins, got {gat_half_cfg.duration_minutes}"
    print(f"  ✅ GAT Full (100 Qs) and GAT Half (50 Qs) generated successfully.")

    # 4. Scaled Scoring & Section Breakdown Test
    print("\n[4/4] Testing Official Scaled Scoring...")
    # Simulate answering 40 out of 49 correctly on SAT Half
    sim_answers = {i: q.correct_key for i, q in enumerate(sat_half_qs[:40])}
    sat_score = orch.score_exam_simulation(sat_half_cfg, sat_half_qs, sim_answers)
    assert 400 <= sat_score.scaled_score <= 1600, f"Invalid scaled score: {sat_score.scaled_score}"
    assert "Reading & Writing" in sat_score.section_breakdown
    assert "Math" in sat_score.section_breakdown
    print(f"  ✅ SAT Scaled Score: {sat_score.scaled_score} / 1600 ({sat_score.raw_score_percent}% accuracy)")
    print(f"     Readiness: {sat_score.readiness_level}")
    print(f"     Percentile: {sat_score.percentile_estimate}")
    print(f"     Section Breakdown: {list(sat_score.section_breakdown.keys())}")

    # Simulate GAT scoring
    gat_answers = {i: q.correct_key for i, q in enumerate(gat_half_qs[:38])} # 38/50 = 76%
    gat_score = orch.score_exam_simulation(gat_half_cfg, gat_half_qs, gat_answers)
    assert 0 <= gat_score.scaled_score <= 100, f"Invalid GAT score: {gat_score.scaled_score}"
    assert "Verbal Reasoning" in gat_score.section_breakdown
    assert "Quantitative Reasoning" in gat_score.section_breakdown
    assert "Analytical Reasoning" in gat_score.section_breakdown
    print(f"  ✅ GAT Score: {gat_score.scaled_score} / 100 ({gat_score.raw_score_percent}% accuracy)")
    print(f"     Readiness: {gat_score.readiness_level}")

    print("\n" + "=" * 55)
    print("🎉 ALL SIMULATOR TESTS PASSED!")
    print("=" * 55)


if __name__ == "__main__":
    run_simulator_tests()
