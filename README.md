# 🎓 SAT & GAT AI Mentor: Autonomous Multi-Agent Test Prep System

An Agentic AI educational platform designed for standardized test prep students (Digital SAT and Pakistani GAT-General). Rather than behaving as a generic answer generator, the system acts as a personalized, pedagogical mentor.

---

## 🌟 Key Features

1. **Markdown-Aware RAG Engine:** Indexes prep books while preserving syllabus hierarchy (`# Chapter`, `## Topic`, `### Subtopic`) and LaTeX mathematical notation.
2. **Diagnostic Assessment Agent:** Pulls or dynamically generates calibrated test questions tailored by difficulty and target exam.
3. **Cognitive Error Analysis Agent:** When a student chooses an incorrect option, the agent dissects the student's thought process and classifies the mistake into cognitive failure modes:
   - *Conceptual Gap*
   - *Trap Choice / Cognitive Bias*
   - *Calculation / Arithmetic Mistake*
   - *Misreading Premise / Constraint Overlooked*
4. **Socratic AI Tutor (3-Tier Scaffolding Ladder):** Strictly adheres to pedagogical guardrails—never revealing the raw answer, but delivering:
   - **Level 1 (Nudge):** Focuses student attention on overlooked premises.
   - **Level 2 (Scaffold):** Prompts for intermediate principles or rules.
   - **Level 3 (Step-Through):** Walks through the first calculation step, prompting the student to execute the remainder.
5. **Adaptive Study Scheduler Agent:** Evaluates recurring mistake patterns and topic mastery percentages to generate dynamic 3-day and 7-day focused study sprints.
6. **Full & Half Exam Simulator (Test Day Experience):**
   - **Digital SAT** (Official 98 Qs Full / 49 Qs Half Mock) & **NTS GAT General** (Official 100 Qs Full / 50 Qs Half Mock).
   - **Real-Time Countdown Timer:** Second-by-second countdown with visual urgency alerts.
   - **Question Navigator Palette:** 1-to-98/100 color-coded grid (🟢 Answered, 🔴 Skipped, 🚩 Flagged) with instant jumping.
   - **On-Screen Scientific Calculator:** Integrated popover calculator with basic/scientific arithmetic, powers, roots, constants, and keyboard support.
   - **Official Scaled Scoring:** Scaled 1600 SAT score and 100-point GAT score with percentile and readiness feedback.

---

## 🏗️ Multi-Agent Architecture

```
[Markdown Prep Books] -> [Markdown-Aware Ingestion] -> [Knowledge Store]
                                                            │
┌───────────────────────────────────────────────────────────┴────────────────────────┐
│                                                                                    │
▼                                                                                    ▼
[Diagnostic Agent] ──(Student Attempt)──> [Cognitive Error Agent] ──> [Student Mastery]
                                                      │                      │
                                                      ▼                      ▼
                                            [Socratic Tutor Agent]  [Scheduler Agent]
```

---

