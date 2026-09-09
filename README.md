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

## 🚀 Quickstart Guide

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/qaisaroo1/SAT-GAT-AI-mentor.git
cd SAT-GAT-AI-mentor

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key *(Optional)*
> **Note:** The system is **100% operational offline** out-of-the-box using the embedded official past papers, pre-calibrated question bank, and offline grading. If you want live dynamic question generation from Google Gemini, add your key to `.env`:
```env
GEMINI_API_KEY=your_google_ai_studio_api_key_here
```

### 3. Run Verification Tests
```bash
python test_system.py
python test_simulator.py
```

### 4. Launch the Web Interface
```bash
streamlit run app.py
```

---

## 👥 Hackathon Presentation Highlights (For Pak Angels Judges)
- **Local Impact:** Tackles **GAT Analytical Reasoning**, the most difficult section for Pakistani graduate students, alongside global **Digital SAT Quantitative**.
- **Pedagogical Integrity:** Replaces answer-leaking LLM behavior with active Socratic learning.
- **Cost Accessibility:** Delivers $100/hr private tutoring expertise at zero cost on responsive web and mobile browsers.
