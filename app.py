import os
import time
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components
from src.orchestrator import MentorOrchestrator
from src.schemas import (
    Question, ErrorAnalysisResult, SocraticHint,
    ExamSimulationConfig, ScaledExamScore
)

# Page configuration
st.set_page_config(
    page_title="AI Mentor | SAT & GAT Prep",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Clean, Jargon-Free, Dark/Light Friendly)
st.markdown("""
<style>
    .main-header { 
        font-size: 2.3rem; 
        font-weight: 800; 
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem; 
    }
    .sub-header { font-size: 1.05rem; opacity: 0.85; margin-bottom: 1.2rem; }
    .agent-pill { display: inline-block; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 600; margin-right: 6px; }
    .agent-active { background-color: #2563EB; color: #FFFFFF; border: 1px solid #60A5FA; }
    .agent-idle { background-color: rgba(156, 163, 175, 0.2); color: #9CA3AF; border: 1px solid rgba(156, 163, 175, 0.3); }
    .lesson-box { 
        background: rgba(59, 130, 246, 0.08); 
        border-left: 5px solid #3B82F6; 
        border-radius: 8px; 
        padding: 18px; 
        margin-bottom: 20px; 
    }
    .error-diagnosis-card { 
        background: rgba(239, 68, 68, 0.12); 
        border-left: 5px solid #EF4444; 
        border-radius: 8px; 
        padding: 16px; 
        margin-top: 14px; 
    }
    .success-card { 
        background: rgba(34, 197, 94, 0.12); 
        border-left: 5px solid #22C55E; 
        border-radius: 8px; 
        padding: 16px; 
        margin-top: 14px; 
    }
    .hint-card { 
        background: rgba(245, 158, 11, 0.12); 
        border-left: 5px solid #F59E0B; 
        border-radius: 8px; 
        padding: 16px; 
        margin-top: 14px; 
    }
    .quiz-launch-btn {
        display: block;
        width: 100%;
        text-align: center;
        background: linear-gradient(90deg, #2563EB, #4F46E5);
        color: #FFFFFF !important;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 16px;
        text-decoration: none !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.25);
        transition: all 0.2s ease-in-out;
        box-sizing: border-box;
    }
    .quiz-launch-btn:hover {
        background: linear-gradient(90deg, #1D4ED8, #4338CA);
        box-shadow: 0 6px 12px -2px rgba(37, 99, 235, 0.35);
        transform: translateY(-1px);
        color: #FFFFFF !important;
    }
    .focus-card {
        background: #FFFFFF;
        border: 1px solid #FED7AA;
        border-left: 5px solid #EA580C;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "orchestrator" not in st.session_state or not hasattr(st.session_state.orchestrator, "start_exam_simulation"):
    st.session_state.orchestrator = MentorOrchestrator()

if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "eval_result" not in st.session_state:
    st.session_state.eval_result = None

if "hint_history" not in st.session_state:
    st.session_state.hint_history = []

if "active_agent" not in st.session_state:
    st.session_state.active_agent = "Curriculum Agent"

if "target_topic" not in st.session_state:
    st.session_state.target_topic = None

if "last_selected_topic" not in st.session_state:
    st.session_state.last_selected_topic = None

if "last_exam_type" not in st.session_state:
    st.session_state.last_exam_type = None

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0

if "quiz_evals" not in st.session_state:
    st.session_state.quiz_evals = {}

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False

if "show_inline_quiz" not in st.session_state:
    st.session_state.show_inline_quiz = False

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

# Simulator state
if "sim_active" not in st.session_state:
    st.session_state.sim_active = False

if "sim_completed" not in st.session_state:
    st.session_state.sim_completed = False

if "sim_config" not in st.session_state:
    st.session_state.sim_config = None

if "sim_questions" not in st.session_state:
    st.session_state.sim_questions = []

if "sim_index" not in st.session_state:
    st.session_state.sim_index = 0

if "sim_answers" not in st.session_state:
    st.session_state.sim_answers = {}

if "sim_flagged" not in st.session_state:
    st.session_state.sim_flagged = set()

if "sim_start_time" not in st.session_state:
    st.session_state.sim_start_time = None

if "sim_score" not in st.session_state:
    st.session_state.sim_score = None

if not hasattr(st.session_state.orchestrator, "start_exam_simulation"):
    st.session_state.orchestrator = MentorOrchestrator()
orchestrator: MentorOrchestrator = st.session_state.orchestrator

# Read URL Query Parameters for new tab launch
params = st.query_params
url_mode = params.get("mode", "")
url_exam = params.get("exam", "")
url_topic = params.get("topic", "")

# Determine Exam Type default
default_exam_idx = 0
if url_exam and url_exam.upper() in ["SAT", "GAT"]:
    default_exam_idx = 0 if url_exam.upper() == "SAT" else 1
elif st.session_state.last_exam_type:
    default_exam_idx = 0 if st.session_state.last_exam_type == "SAT" else 1


# ================= REUSABLE QUIZ WORKFLOW COMPONENT =================
def render_quiz_flow(orchestrator: MentorOrchestrator, exam_type: str, is_standalone: bool = False):
    """
    Renders the adaptive quiz:
    - Pre-quiz customization (Length: 5, 10, 15 | Difficulty: Easy, Medium, Hard | Bank vs AI)
    - Real test interface (unselected radio, no spoilers during quiz)
    - Full performance rating, 'Why you did this wrong' diagnosis, and one-click Weak-Spot Drill
    """
    target_topic = st.session_state.target_topic or "Section Quiz"

    # 1. PRE-QUIZ CUSTOMIZATION & CONFIRMATION SCREEN
    if not st.session_state.quiz_started:
        st.markdown(f"""
        <div class='lesson-box' style='background: #f8fafc; border: 2px solid #3B82F6; border-radius: 12px; padding: 24px; text-align: center; margin-top: 15px;'>
            <h2 style='color: #1e293b; margin-top: 0;'>🎯 Ready to Test Your Knowledge?</h2>
            <h3 style='color: #2563EB; margin: 8px 0;'>Topic: <strong>{target_topic}</strong></h3>
            <span style='background: #DBEAFE; color: #1E40AF; padding: 4px 14px; border-radius: 12px; font-weight: 600; font-size: 14px;'>Exam: {exam_type}</span>
            <p style='color: #475569; font-size: 15px; max-width: 650px; margin: 14px auto 10px auto;'>
                Customize your quiz below or jump straight in. Questions are automatically balanced across all choices (A, B, C, D) with full mistake diagnosis at the end.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Quiz Customization Controls
        with st.container():
            c_len, c_diff, c_src = st.columns([1, 1, 1.2])
            with c_len:
                q_count = st.selectbox(
                    "Quiz Length",
                    [5, 10, 15],
                    index=0,
                    format_func=lambda x: f"{x} Questions",
                    key=f"cfg_len_{is_standalone}"
                )
            with c_diff:
                q_diff = st.selectbox(
                    "Difficulty",
                    ["Medium", "Easy", "Hard"],
                    index=0,
                    format_func=lambda x: f"{x} Level",
                    key=f"cfg_diff_{is_standalone}"
                )
            with c_src:
                has_key = bool(st.session_state.gemini_api_key)
                src_options = ["Calibrated & Parametric Bank", "✨ Live Gemini AI"] if has_key else ["Calibrated & Parametric Bank"]
                q_source = st.selectbox(
                    "Question Source",
                    src_options,
                    index=0,
                    key=f"cfg_src_{is_standalone}",
                    help="Connect Gemini API key in sidebar to enable Live Gemini AI generation"
                )

        col_l, col_btn, col_r = st.columns([1, 2, 1])
        with col_btn:
            btn_label = f"🚀 Start {q_count}-Question Quiz ({q_diff})"
            if st.button(btn_label, type="primary", use_container_width=True, key=f"btn_launch_quiz_{target_topic}_{is_standalone}"):
                use_ai = (q_source == "✨ Live Gemini AI")
                with st.spinner(f"Preparing {q_count} {q_diff} questions on '{target_topic}'..."):
                    st.session_state.quiz_questions = orchestrator.get_custom_quiz(
                        topic=target_topic,
                        exam_type=exam_type,
                        count=q_count,
                        difficulty=q_diff,
                        use_ai=use_ai
                    )
                st.session_state.quiz_started = True
                st.session_state.quiz_index = 0
                st.session_state.quiz_evals = {}
                st.session_state.quiz_answers = {}
                st.session_state.quiz_completed = False
                st.session_state.hint_history = []
                st.session_state.active_agent = "Diagnostic Agent"
                st.rerun()
        return

    # 2. END-OF-QUIZ SCORECARD & WEAK-SPOT DRILL
    if st.session_state.quiz_completed:
        total_q = len(st.session_state.quiz_questions)
        correct_count = sum(1 for res in st.session_state.quiz_evals.values() if res.is_correct)
        score_pct = int((correct_count / total_q) * 100) if total_q > 0 else 0

        st.markdown(f"""
        <div class='success-card' style='padding: 24px; margin-bottom: 20px; border-radius: 12px;'>
            <h2 style='margin:0;'>🏆 Quiz Complete: {target_topic}</h2>
            <h3 style='margin:10px 0 0 0;'>Final Score: {correct_count} / {total_q} ({score_pct}%)</h3>
        </div>
        """, unsafe_allow_html=True)
        st.progress(1.0)

        # Performance summary rating
        if score_pct == 100:
            st.balloons()
            st.success("🌟 **Outstanding! Perfect Score (100%)** — You answered all questions correctly!")
        elif score_pct >= 80:
            st.info(f"🟢 **Great Performance ({score_pct}%)!** — Strong understanding with just minor slips to review.")
        elif score_pct >= 60:
            st.warning(f"🟡 **Solid Effort ({score_pct}%)!** — You know the fundamentals, but a few questions tripped you up.")
        else:
            st.error(f"🔴 **Needs Focused Practice ({score_pct}%)!** — Review the diagnostic explanations below before moving forward.")

        # Gather missed questions
        missed_items = []
        for idx, q_item in enumerate(st.session_state.quiz_questions):
            res = st.session_state.quiz_evals.get(idx)
            if not res or not res.is_correct:
                missed_items.append((idx + 1, q_item, res))

        # ================= TARGETED WEAK-SPOT AI DRILL BUTTON =================
        if missed_items:
            weak_concepts = [res.recommended_concept for _, _, res in missed_items if res and res.recommended_concept]
            st.markdown(f"""
            <div style='background: #EFF6FF; border: 2px solid #3B82F6; border-radius: 10px; padding: 18px; margin: 18px 0;'>
                <h4 style='color: #1E40AF; margin-top:0;'>⚡ Turn Mistakes Into Points: Targeted Weak-Spot Drill</h4>
                <p style='color: #1E3A8A; margin-bottom: 12px;'>
                    You missed {len(missed_items)} concept(s). Would you like to do a quick 3-question drill focused <strong>strictly on your weak spots</strong>?
                </p>
            </div>
            """, unsafe_allow_html=True)

            col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
            with col_w2:
                if st.button("🎯 Launch Targeted Weak-Spot Drill (3 Questions)", type="primary", use_container_width=True, key=f"btn_launch_weak_drill_{is_standalone}"):
                    with st.spinner("Generating targeted questions on your weak spots..."):
                        st.session_state.quiz_questions = orchestrator.get_custom_quiz(
                            topic=target_topic,
                            exam_type=exam_type,
                            count=3,
                            difficulty="Medium",
                            use_ai=bool(st.session_state.gemini_api_key),
                            weak_concepts=weak_concepts
                        )
                    st.session_state.quiz_started = True
                    st.session_state.quiz_index = 0
                    st.session_state.quiz_evals = {}
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_completed = False
                    st.session_state.hint_history = []
                    st.rerun()

        # ================= WHY YOU GOT IT WRONG & WHAT TO FOCUS ON =================
        st.markdown("---")
        if not missed_items:
            st.markdown(f"""
            <div style='background: #F0FDF4; border-left: 5px solid #22C55E; border-radius: 8px; padding: 20px; margin-bottom: 20px;'>
                <h4 style='color: #15803D; margin-top:0;'>🎉 Mastery Confirmed: Zero Mistakes!</h4>
                <p style='color: #166534; margin:0;'>
                    You correctly answered every question in <strong>{target_topic}</strong> without missing any concepts. You are ready for the next syllabus topic!
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### 🎯 Why You Got Questions Wrong & What to Focus More On")
            st.markdown(f"""
            <div style='background: #FFFBEB; border-left: 5px solid #F59E0B; border-radius: 8px; padding: 18px; margin-bottom: 20px;'>
                <h4 style='color: #B45309; margin-top:0;'>📌 Breakdown of Your {len(missed_items)} Missed Question(s)</h4>
                <p style='color: #78350F; margin-bottom: 0;'>
                    Here is the exact reason behind each mistake and what you need to focus on:
                </p>
            </div>
            """, unsafe_allow_html=True)

            for q_num, q_item, res in missed_items:
                user_choice = st.session_state.quiz_answers.get(q_num - 1, "Not Answered")
                concept_name = res.recommended_concept if res and res.recommended_concept else q_item.topic
                trap_explanation = res.diagnosis if res else "Missed question."
                clean_trap = trap_explanation.replace("$r^2$", "r²").replace("$r$", "r").replace("$", "")
                mistake_cat = res.category.value if (res and res.category) else "Exam Trap"
                
                with st.container():
                    st.markdown(f"""
                    <div class='focus-card'>
                        <h4 style='margin:0 0 8px 0; color: #C2410C;'>
                            ❌ Question {q_num} Breakdown: Your Answer was Option {user_choice} (Correct was Option {q_item.correct_key})
                        </h4>
                        <p style='margin:0 0 6px 0; color: #1E293B;'>
                            <strong>Mistake Type:</strong> <span style='background:#FEE2E2; color:#991B1B; padding:2px 8px; border-radius:6px; font-weight:600;'>{mistake_cat}</span>
                        </p>
                        <p style='margin:0 0 8px 0; color: #334155;'>
                            <strong>Why you did this wrong:</strong> {clean_trap}
                        </p>
                        <p style='margin:0 0 6px 0; color: #0369A1;'>
                            <strong>🎯 What to focus more on:</strong> <code>{concept_name}</code>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        # ================= QUESTION-BY-QUESTION FULL SOLUTIONS =================
        st.markdown("---")
        st.markdown("### 📋 Complete Question-by-Question Solutions")
        for idx, q_item in enumerate(st.session_state.quiz_questions):
            user_res = st.session_state.quiz_evals.get(idx)
            user_choice = st.session_state.quiz_answers.get(idx, "Not Answered")
            status_badge = "✅ Correct" if (user_res and user_res.is_correct) else "❌ Missed"

            with st.expander(f"Question {idx + 1}: {status_badge} (Your Answer: Option {user_choice} | Correct: Option {q_item.correct_key})", expanded=(not user_res or not user_res.is_correct)):
                st.markdown(f"**Question:** {q_item.question}")
                for opt in q_item.options:
                    prefix = "👉 " if opt.key == user_choice else "• "
                    suffix = " *(Your Choice)*" if opt.key == user_choice else ""
                    if opt.key == q_item.correct_key:
                        suffix += " ✅ *(Correct Answer)*"
                    st.write(f"{prefix}**{opt.key}:** {opt.text} {suffix}")

                clean_rat = q_item.rationale.replace("$r^2$", "r²").replace("$r$", "r").replace("$", "")
                st.markdown("**How to solve it step-by-step:**")
                st.write(clean_rat)

        # Bottom actions
        col_fresh, col_retake, col_nav = st.columns([1.2, 1, 1])
        with col_fresh:
            if st.button("✨ Start Fresh Quiz", type="primary", use_container_width=True, key=f"btn_fresh_{is_standalone}"):
                seen_ids = [q.id for q in st.session_state.quiz_questions]
                curr_count = len(st.session_state.quiz_questions)
                with st.spinner("Loading brand-new, unseen questions..."):
                    st.session_state.quiz_questions = orchestrator.get_custom_quiz(
                        topic=target_topic,
                        exam_type=exam_type,
                        count=curr_count,
                        difficulty="Medium",
                        use_ai=bool(st.session_state.gemini_api_key),
                        exclude_ids=seen_ids
                    )
                st.session_state.quiz_index = 0
                st.session_state.quiz_evals = {}
                st.session_state.quiz_answers = {}
                st.session_state.quiz_completed = False
                st.session_state.hint_history = []
                st.session_state.quiz_started = True
                st.rerun()

        with col_retake:
            if st.button("🔄 Retake Quiz", use_container_width=True, key=f"btn_retake_{is_standalone}"):
                st.session_state.quiz_index = 0
                st.session_state.quiz_evals = {}
                st.session_state.quiz_answers = {}
                st.session_state.quiz_completed = False
                st.session_state.hint_history = []
                st.session_state.quiz_started = True
                st.rerun()

        with col_nav:
            if is_standalone:
                st.link_button("📖 Return to Main Dashboard", url="/", use_container_width=True)
            else:
                if st.button("📖 Close Quiz & Return", use_container_width=True, key="btn_close_inline"):
                    st.session_state.show_inline_quiz = False
                    st.session_state.quiz_started = False
                    st.rerun()
        return

    # 3. ACTIVE QUIZ RUNNER (Strictly NO spoilers during test)
    total_q = len(st.session_state.quiz_questions)
    curr_idx = min(st.session_state.quiz_index, total_q - 1)
    q: Question = st.session_state.quiz_questions[curr_idx]
    st.session_state.current_question = q

    col_main, col_tutor = st.columns([1.15, 0.85], gap="large")

    with col_main:
        st.markdown(f"### 📝 {q.topic}")
        st.markdown(f"**Question {curr_idx + 1} of {total_q}**")
        st.progress((curr_idx + 1) / total_q)
        st.caption(f"Difficulty: **{q.difficulty}** &nbsp;|&nbsp; Exam: **{q.exam_type}**")

        st.markdown(f"**{q.question}**")

        options_dict = {f"{opt.key}: {opt.text}": opt.key for opt in q.options}
        
        # Check if user already picked an answer for this question
        prev_ans = st.session_state.quiz_answers.get(curr_idx)
        def_idx = None
        if prev_ans is not None:
            for opt_idx, opt in enumerate(q.options):
                if opt.key == prev_ans:
                    def_idx = opt_idx
                    break

        # Render radio button with index=None if not yet answered (Option A is NOT pre-selected!)
        selected_label = st.radio(
            "Choose your answer:",
            list(options_dict.keys()),
            index=def_idx,
            key=f"q_{q.id}_{curr_idx}_{exam_type}_{is_standalone}"
        )
        selected_key = options_dict[selected_label] if selected_label else None

        # Automatically record selection
        if selected_key:
            st.session_state.quiz_answers[curr_idx] = selected_key

        # Status caption
        if curr_idx in st.session_state.quiz_answers:
            st.caption(f"📌 Your selected choice: **Option {st.session_state.quiz_answers[curr_idx]}** *(Saved)*")
        else:
            st.caption("⚪ *No option selected yet. Click an option above to choose your answer.*")

        st.markdown("")

        # Quiz Navigation Controls
        is_last = (curr_idx == total_q - 1)
        col_prev, col_hint, col_next = st.columns([1, 1.2, 1.5])
        
        with col_prev:
            prev_clicked = st.button("⬅️ Previous", disabled=(curr_idx == 0), use_container_width=True, key=f"btn_prev_{is_standalone}")
        
        with col_hint:
            hint_clicked = st.button("Request Hint 💡", use_container_width=True, key=f"btn_hint_{is_standalone}")
        
        with col_next:
            if is_last:
                next_clicked = st.button("🏆 Submit Quiz & View Results", type="primary", use_container_width=True, key=f"btn_next_{is_standalone}")
            else:
                next_clicked = st.button(f"Next Question ({curr_idx + 2}/{total_q}) ➡️", type="primary", use_container_width=True, key=f"btn_next_{is_standalone}")

        if prev_clicked:
            st.session_state.quiz_index = max(0, curr_idx - 1)
            st.session_state.hint_history = []
            st.rerun()

        if hint_clicked:
            st.session_state.active_agent = "Socratic Tutor Agent"
            next_lvl = len(st.session_state.hint_history) + 1
            hint_res = orchestrator.get_socratic_hint(q, hint_level=next_lvl)
            st.session_state.hint_history.append(hint_res)
            st.rerun()

        if next_clicked:
            if curr_idx not in st.session_state.quiz_answers:
                st.warning("⚠️ Please select an answer before proceeding.")
            else:
                if is_last:
                    # Evaluate all answers together at the end
                    st.session_state.active_agent = "Cognitive Error Agent"
                    for q_i, q_item in enumerate(st.session_state.quiz_questions):
                        chosen_opt = st.session_state.quiz_answers.get(q_i)
                        if chosen_opt:
                            eval_res = orchestrator.evaluate_answer(q_item, chosen_opt)
                            st.session_state.quiz_evals[q_i] = eval_res
                        else:
                            st.session_state.quiz_evals[q_i] = ErrorAnalysisResult(
                                is_correct=False,
                                selected_key="None",
                                correct_key=q_item.correct_key,
                                category=None,
                                diagnosis="Question was skipped.",
                                recommended_concept=f"Review {q_item.topic}"
                            )
                    st.session_state.quiz_completed = True
                else:
                    st.session_state.quiz_index = curr_idx + 1
                st.session_state.hint_history = []
                st.rerun()

    with col_tutor:
        st.markdown("### 🦉 Socratic AI Tutor")
        st.caption("Guiding inquiry without spoiling answers")

        if not st.session_state.hint_history:
            st.info("💡 Stuck on this question? Click **'Request Hint 💡'** to receive a gentle, step-by-step mathematical clue.")
        else:
            for hint in st.session_state.hint_history:
                level_labels = {
                    1: "Clue 1: Where to Start",
                    2: "Clue 2: Formula / Rule",
                    3: "Clue 3: Step-by-Step Help"
                }
                lvl_name = level_labels.get(hint.hint_level, f"Clue {hint.hint_level}")
                st.markdown(f"""
                <div class='hint-card'>
                    <strong>💡 {lvl_name}</strong>
                    <p>{hint.hint_text}</p>
                    <p><em>❓ {hint.guiding_question}</em></p>
                </div>
                """, unsafe_allow_html=True)

            if len(st.session_state.hint_history) < 3:
                if st.button("💡 Need More Help? Show Next Clue", use_container_width=True, key=f"btn_unlock_hint_{is_standalone}"):
                    st.session_state.active_agent = "Socratic Tutor Agent"
                    next_lvl = len(st.session_state.hint_history) + 1
                    hint_res = orchestrator.get_socratic_hint(q, hint_level=next_lvl)
                    st.session_state.hint_history.append(hint_res)
                    st.rerun()
            else:
                st.success("🎉 You have all 3 clues! Use them to choose your answer.")



# ================= REUSABLE EXAM SIMULATOR COMPONENT =================
def render_simulator_flow(orchestrator: MentorOrchestrator, exam_type: str, initial_mode: str = "full", is_standalone: bool = False):
    """
    Renders the official exam simulator:
    - Pre-exam confirmation screen with rules and specs (asks first!)
    - Real-time test screen with live countdown timer, palette grid, formula sheet, and auto-save
    - Authentic scaled score reporting (400-1600 SAT, 0-100 GAT), section breakdown, and review
    """

    # 1. PRE-EXAM CONFIRMATION & SETUP SCREEN (ASKS FIRST!)
    if not st.session_state.sim_active and not st.session_state.sim_completed:
        st.markdown(f"""
        <div class='lesson-box' style='background: #f8fafc; border: 2px solid #2563EB; border-radius: 12px; padding: 26px; text-align: center; margin-top: 15px;'>
            <h2 style='color: #1e293b; margin-top: 0;'>🎯 Ready for the Test Day Simulator?</h2>
            <h3 style='color: #2563EB; margin: 8px 0;'>Exam: <strong>{exam_type}</strong></h3>
            <span style='background: #DBEAFE; color: #1E40AF; padding: 4px 14px; border-radius: 12px; font-weight: 600; font-size: 14px;'>Official Timed Mode</span>
            <p style='color: #475569; font-size: 15px; max-width: 680px; margin: 14px auto 10px auto;'>
                Confirm your test settings below. Once you click <strong>Start Exam Now</strong>, the official countdown timer will begin and your test session will be locked until submission.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_cfg1, col_cfg2 = st.columns([1.2, 1])
        with col_cfg1:
            sat_full_txt = "Full Exam (98 Questions, 134 Mins)"
            sat_half_txt = "Half-Length Mock (49 Questions, 67 Mins)"
            gat_full_txt = "Full Exam (100 Questions, 120 Mins)"
            gat_half_txt = "Half-Length Mock (50 Questions, 60 Mins)"

            mode_opts = [sat_full_txt, sat_half_txt] if exam_type == "SAT" else [gat_full_txt, gat_half_txt]
            default_idx = 0 if initial_mode.lower() == "full" else 1
            sim_mode_label = st.radio(
                "Select Exam Format:",
                mode_opts,
                index=default_idx,
                key=f"radio_sim_mode_{is_standalone}"
            )
            chosen_mode = "full" if "Full Exam" in sim_mode_label else "half"

        with col_cfg2:
            st.markdown("#### 📋 Test Specifications")
            if exam_type == "SAT":
                if chosen_mode == "full":
                    st.write("• **Total Questions:** 98 (54 Reading & Writing + 44 Math)")
                    st.write("• **Duration:** 134 Minutes (Official College Board)")
                    st.write("• **Scoring Scale:** 400 – 1600 Scaled Points")
                else:
                    st.write("• **Total Questions:** 49 (27 Reading & Writing + 22 Math)")
                    st.write("• **Duration:** 67 Minutes")
                    st.write("• **Scoring Scale:** Calibrated to 400 – 1600")
            else:
                if chosen_mode == "full":
                    st.write("• **Total Questions:** 100 (40 Verbal + 35 Quant + 25 Analytical)")
                    st.write("• **Duration:** 120 Minutes (Official NTS standard)")
                    st.write("• **Passing Cutoff:** 50 Marks (Out of 100)")
                else:
                    st.write("• **Total Questions:** 50 (20 Verbal + 18 Quant + 12 Analytical)")
                    st.write("• **Duration:** 60 Minutes")
                    st.write("• **Passing Cutoff:** 50% Scaled")

        st.markdown("---")
        col_l, col_btn, col_r = st.columns([1, 2, 1])
        with col_btn:
            start_btn_txt = f"🚀 Start {exam_type} {'Full Exam' if chosen_mode == 'full' else 'Half Mock'} Now"
            if st.button(start_btn_txt, type="primary", use_container_width=True, key=f"btn_start_sim_now_{is_standalone}"):
                with st.spinner(f"Assembling official {exam_type} simulation set..."):
                    cfg, qs = orchestrator.start_exam_simulation(exam_type=exam_type, length_mode=chosen_mode)
                    st.session_state.sim_config = cfg
                    st.session_state.sim_questions = qs
                    st.session_state.sim_index = 0
                    st.session_state.sim_answers = {}
                    st.session_state.sim_flagged = set()
                    st.session_state.sim_start_time = time.time()
                    st.session_state.sim_active = True
                    st.session_state.sim_completed = False
                    st.session_state.sim_score = None
                    st.rerun()
        return

    # 2. ACTIVE EXAM SIMULATION (TIMED)
    elif st.session_state.sim_active and not st.session_state.sim_completed:
        cfg = st.session_state.sim_config
        qs = st.session_state.sim_questions
        curr_idx = st.session_state.sim_index
        total_q = len(qs)
        q = qs[curr_idx]

        # Timer calculation
        elapsed_sec = int(time.time() - st.session_state.sim_start_time)
        total_allowed_sec = cfg.duration_minutes * 60
        remaining_sec = max(0, total_allowed_sec - elapsed_sec)
        rem_min = remaining_sec // 60
        rem_sec = remaining_sec % 60
        timer_str = f"{rem_min:02d}:{rem_sec:02d}"

        # Header Status Bar
        col_hdr1, col_hdr2, col_calc, col_hdr3, col_hdr4 = st.columns([1.3, 1.1, 0.9, 0.9, 0.8])
        with col_hdr1:
            st.markdown(f"#### 🎓 {cfg.exam_type} Simulation ({cfg.length_mode.title()})")
            st.caption(f"Topic: **{q.topic}**")
        with col_hdr2:
            timer_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                    background: transparent;
                }}
                #countdown-box {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 40px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #F1F5F9;
                    border: 1px solid #CBD5E1;
                    border-radius: 8px;
                    font-weight: 700;
                    font-size: 16px;
                    color: #16A34A;
                    box-sizing: border-box;
                }}
            </style>
            </head>
            <body>
            <div id="countdown-box">
                ⏱️&nbsp;<span id="time-display">--:--</span>&nbsp;remaining
            </div>
            <script>
                let timeLeft = {remaining_sec};
                function updateClock() {{
                    if (timeLeft <= 0) {{
                        document.getElementById("time-display").innerText = "00:00 (Time Up!)";
                        document.getElementById("countdown-box").style.color = "#DC2626";
                        return;
                    }}
                    let m = Math.floor(timeLeft / 60);
                    let s = timeLeft % 60;
                    let mStr = (m < 10 ? "0" : "") + m;
                    let sStr = (s < 10 ? "0" : "") + s;
                    document.getElementById("time-display").innerText = mStr + ":" + sStr;
                    if (timeLeft < 300) {{
                        document.getElementById("countdown-box").style.color = "#DC2626";
                    }} else if (timeLeft < 900) {{
                        document.getElementById("countdown-box").style.color = "#EA580C";
                    }} else {{
                        document.getElementById("countdown-box").style.color = "#16A34A";
                    }}
                    timeLeft--;
                }}
                updateClock();
                setInterval(updateClock, 1000);
            </script>
            </body>
            </html>
            """
            components.html(timer_html, height=44)
        with col_calc:
            with st.popover("🔢 Calculator", use_container_width=True):
                calc_html = """
                <!DOCTYPE html>
                <html>
                <head>
                <meta charset="utf-8">
                <style>
                    * {
                        box-sizing: border-box;
                        margin: 0;
                        padding: 0;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        user-select: none;
                    }
                    body {
                        background: #0F172A;
                        color: #F8FAFC;
                        padding: 6px;
                        border-radius: 8px;
                    }
                    #calc-container {
                        width: 100%;
                        max-width: 270px;
                        margin: 0 auto;
                    }
                    #calc-display {
                        background: #1E293B;
                        border: 1px solid #334155;
                        border-radius: 6px;
                        padding: 6px 10px;
                        text-align: right;
                        margin-bottom: 6px;
                        min-height: 48px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    }
                    #calc-expr {
                        font-size: 11px;
                        color: #94A3B8;
                        height: 15px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }
                    #calc-val {
                        font-size: 20px;
                        font-weight: 700;
                        color: #38BDF8;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }
                    .grid {
                        display: grid;
                        grid-template-columns: repeat(4, 1fr);
                        gap: 5px;
                    }
                    button {
                        height: 35px;
                        border-radius: 6px;
                        border: 1px solid #334155;
                        font-size: 14px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: background 0.1s ease, transform 0.05s ease;
                        background: #1E293B;
                        color: #F1F5F9;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    button:hover { background: #334155; }
                    button:active { transform: scale(0.96); }
                    button.op { background: #0284C7; color: white; border-color: #0369A1; }
                    button.op:hover { background: #0369A1; }
                    button.eq { background: #16A34A; color: white; border-color: #15803D; }
                    button.eq:hover { background: #15803D; }
                    button.clear { background: #DC2626; color: white; border-color: #B91C1C; }
                    button.clear:hover { background: #B91C1C; }
                    button.fn { background: #334155; color: #CBD5E1; font-size: 13px; }
                </style>
                </head>
                <body tabindex="0">
                <div id="calc-container">
                    <div id="calc-display">
                        <div id="calc-expr"></div>
                        <div id="calc-val">0</div>
                    </div>
                    <div class="grid">
                        <button class="fn" onclick="insert('Math.sqrt(')" title="Square root">√</button>
                        <button class="fn" onclick="insert('**')" title="Power (x^y)">xʸ</button>
                        <button class="fn" onclick="insert('Math.PI')" title="Pi">π</button>
                        <button class="clear" onclick="clearAll()" title="All Clear">AC</button>

                        <button class="fn" onclick="insert('(')">(</button>
                        <button class="fn" onclick="insert(')')">)</button>
                        <button class="fn" onclick="backspace()" title="Backspace">⌫</button>
                        <button class="op" onclick="insert('/')" title="Divide">÷</button>

                        <button onclick="insert('7')">7</button>
                        <button onclick="insert('8')">8</button>
                        <button onclick="insert('9')">9</button>
                        <button class="op" onclick="insert('*')" title="Multiply">×</button>

                        <button onclick="insert('4')">4</button>
                        <button onclick="insert('5')">5</button>
                        <button onclick="insert('6')">6</button>
                        <button class="op" onclick="insert('-')" title="Subtract">−</button>

                        <button onclick="insert('1')">1</button>
                        <button onclick="insert('2')">2</button>
                        <button onclick="insert('3')">3</button>
                        <button class="op" onclick="insert('+')" title="Add">+</button>

                        <button class="fn" onclick="toggleSign()" title="Negate">±</button>
                        <button onclick="insert('0')">0</button>
                        <button onclick="insert('.')">.</button>
                        <button class="eq" onclick="calculate()" title="Equals">=</button>
                    </div>
                </div>
                <script>
                let expr = "";
                let lastResult = null;

                function updateDisplay() {
                    let displayExpr = expr.replace(/Math\\.sqrt\\(/g, "√(")
                                          .replace(/Math\\.PI/g, "π")
                                          .replace(/\\*\\*/g, "^")
                                          .replace(/\\*/g, "×")
                                          .replace(/\\//g, "÷");
                    document.getElementById("calc-expr").innerText = displayExpr;
                    if (!expr) {
                        document.getElementById("calc-val").innerText = lastResult !== null ? lastResult : "0";
                    }
                }

                function insert(val) {
                    if (lastResult !== null && expr === "") {
                        if (['+', '-', '*', '/', '**'].includes(val)) {
                            expr = "" + lastResult;
                        } else {
                            lastResult = null;
                        }
                    }
                    expr += val;
                    updateDisplay();
                }

                function clearAll() {
                    expr = "";
                    lastResult = null;
                    document.getElementById("calc-expr").innerText = "";
                    document.getElementById("calc-val").innerText = "0";
                }

                function backspace() {
                    if (expr.endsWith("Math.sqrt(")) {
                        expr = expr.slice(0, -10);
                    } else if (expr.endsWith("Math.PI")) {
                        expr = expr.slice(0, -7);
                    } else if (expr.endsWith("**")) {
                        expr = expr.slice(0, -2);
                    } else {
                        expr = expr.slice(0, -1);
                    }
                    updateDisplay();
                }

                function toggleSign() {
                    if (expr) {
                        if (expr.startsWith("-(")) {
                            expr = expr.slice(2, -1);
                        } else {
                            expr = "-(" + expr + ")";
                        }
                    } else if (lastResult !== null) {
                        expr = "-(" + lastResult + ")";
                    }
                    updateDisplay();
                }

                function calculate() {
                    if (!expr) return;
                    try {
                        let sanitized = expr;
                        let openCount = (sanitized.match(/\\(/g) || []).length;
                        let closeCount = (sanitized.match(/\\)/g) || []).length;
                        while (openCount > closeCount) {
                            sanitized += ")";
                            closeCount++;
                        }
                        let res = Function('"use strict"; return (' + sanitized + ')')();
                        if (typeof res === 'number' && !isNaN(res) && isFinite(res)) {
                            if (!Number.isInteger(res)) {
                                res = parseFloat(res.toFixed(6));
                            }
                            lastResult = res;
                            document.getElementById("calc-val").innerText = res;
                            expr = "";
                        } else {
                            document.getElementById("calc-val").innerText = "Error";
                        }
                    } catch (e) {
                        document.getElementById("calc-val").innerText = "Error";
                    }
                }

                window.addEventListener('keydown', function(e) {
                    if (e.key >= '0' && e.key <= '9') {
                        insert(e.key);
                    } else if (e.key === '+' || e.key === '-' || e.key === '*' || e.key === '/' || e.key === '.') {
                        insert(e.key);
                    } else if (e.key === '^') {
                        insert('**');
                    } else if (e.key === '(' || e.key === ')') {
                        insert(e.key);
                    } else if (e.key === 'Enter' || e.key === '=') {
                        e.preventDefault();
                        calculate();
                    } else if (e.key === 'Backspace') {
                        e.preventDefault();
                        backspace();
                    } else if (e.key === 'Escape' || e.key.toLowerCase() === 'c') {
                        clearAll();
                    }
                });
                window.focus();
                </script>
                </body>
                </html>
                """
                components.html(calc_html, height=350)
        with col_hdr3:
            is_flagged = (curr_idx in st.session_state.sim_flagged)
            flag_label = "🚩 Flagged" if is_flagged else "🏳️ Flag Question"
            if st.button(flag_label, use_container_width=True, key=f"btn_flag_{curr_idx}_{is_standalone}"):
                if is_flagged:
                    st.session_state.sim_flagged.remove(curr_idx)
                else:
                    st.session_state.sim_flagged.add(curr_idx)
                st.rerun()
        with col_hdr4:
            answered_count = len(st.session_state.sim_answers)
            st.markdown(f"<div style='text-align:right; font-size:14px; padding-top:8px;'><strong>{answered_count}/{total_q}</strong> Answered</div>", unsafe_allow_html=True)

        st.progress((curr_idx + 1) / total_q)

        # Question Main Box
        st.markdown(f"""
        <div style='background: white; border: 1px solid #CBD5E1; border-radius: 12px; padding: 22px; margin: 15px 0;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                <span style='background: #F1F5F9; color: #334155; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 14px;'>Question {curr_idx + 1} of {total_q}</span>
                <span style='background: #EFF6FF; color: #1D4ED8; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px;'>{q.difficulty} Level</span>
            </div>
            <h4 style='color: #0F172A; margin: 12px 0 16px 0; font-weight: 600; line-height: 1.5;'>{q.question}</h4>
        </div>
        """, unsafe_allow_html=True)

        # Multiple Choice Options
        options_dict = {f"({opt.key}) {opt.text}": opt.key for opt in q.options}
        current_saved_key = st.session_state.sim_answers.get(curr_idx)
        default_opt_idx = None
        for i_opt, opt in enumerate(q.options):
            if opt.key == current_saved_key:
                default_opt_idx = i_opt
                break

        selected_label = st.radio(
            "Choose your answer:",
            options=list(options_dict.keys()),
            index=default_opt_idx,
            key=f"sim_radio_{curr_idx}_{q.id}_{is_standalone}",
            label_visibility="collapsed"
        )
        if selected_label:
            st.session_state.sim_answers[curr_idx] = options_dict[selected_label]

        st.markdown("")

        # Bottom Action Bar
        col_b1, col_b2, col_b3 = st.columns([1, 1, 1.3])
        with col_b1:
            if st.button("⬅️ Previous Question", disabled=(curr_idx == 0), use_container_width=True, key=f"btn_sim_prev_{curr_idx}_{is_standalone}"):
                st.session_state.sim_index = max(0, curr_idx - 1)
                st.rerun()

        with col_b2:
            if st.button("Next Question ➡️", disabled=(curr_idx == total_q - 1), use_container_width=True, key=f"btn_sim_next_{curr_idx}_{is_standalone}"):
                st.session_state.sim_index = min(total_q - 1, curr_idx + 1)
                st.rerun()

        with col_b3:
            unanswered_cnt = total_q - len(st.session_state.sim_answers)
            submit_warn = f" ({unanswered_cnt} unanswered)" if unanswered_cnt > 0 else ""
            if st.button(f"🏁 Submit & Score Exam{submit_warn}", type="primary", use_container_width=True, key=f"btn_sim_submit_{curr_idx}_{is_standalone}"):
                with st.spinner("Calculating authentic scaled scores and section diagnostics..."):
                    score_res = orchestrator.score_exam_simulation(cfg, qs, st.session_state.sim_answers)
                    st.session_state.sim_score = score_res
                    st.session_state.sim_completed = True
                    st.session_state.sim_active = False
                    st.rerun()

        st.markdown("---")

        # Question Palette (Questions 1 to N) Placed BELOW the Question
        unanswered_count = total_q - len(st.session_state.sim_answers)
        with st.expander(f"📋 Question Navigator (Questions 1 to {total_q}) — Click any number to jump directly", expanded=True):
            st.markdown(f"""
            <div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; align-items: center;'>
                <span><strong>Palette Status:</strong></span>
                <span style='color: #16A34A; font-weight: 700;'>🟢 Answered ({len(st.session_state.sim_answers)})</span>
                <span style='color: #DC2626; font-weight: 700;'>🔴 Skipped / Unanswered ({unanswered_count})</span>
                <span style='color: #D97706; font-weight: 700;'>🚩 Flagged ({len(st.session_state.sim_flagged)})</span>
                <span style='color: #2563EB; font-weight: 700;'>🎯 Current Question (#{curr_idx + 1})</span>
            </div>
            """, unsafe_allow_html=True)

            col_pal_info, col_pal_jump = st.columns([2, 1.2])
            with col_pal_info:
                st.caption(f"Click any question number below to solve it immediately without pressing Previous:")
            with col_pal_jump:
                next_unanswered = next((i for i in range(total_q) if i not in st.session_state.sim_answers and i != curr_idx), None)
                if next_unanswered is not None:
                    if st.button(f"⚡ Jump to Next Skipped (🔴 Q{next_unanswered + 1})", use_container_width=True, key=f"btn_jump_unans_{curr_idx}_{is_standalone}"):
                        st.session_state.sim_index = next_unanswered
                        st.rerun()

            cols_per_row = 10
            for row_start in range(0, total_q, cols_per_row):
                row_cols = st.columns(cols_per_row)
                for c_offset in range(cols_per_row):
                    q_num = row_start + c_offset
                    if q_num < total_q:
                        with row_cols[c_offset]:
                            is_current = (q_num == curr_idx)
                            is_ans = (q_num in st.session_state.sim_answers)
                            is_flg = (q_num in st.session_state.sim_flagged)

                            q_label = str(q_num + 1)
                            if is_flg:
                                badge = f"🚩 {q_label}"
                            elif is_ans:
                                badge = f"🟢 {q_label}"
                            else:
                                badge = f"🔴 {q_label}"

                            btn_type = "primary" if is_current else "secondary"
                            tooltip = f"Question {q_label}: {'Answered (Option ' + st.session_state.sim_answers[q_num] + ')' if is_ans else 'Skipped / Unanswered'} — Click to open"
                            if st.button(badge, type=btn_type, use_container_width=True, key=f"palette_q_{q_num}_{is_standalone}", help=tooltip):
                                st.session_state.sim_index = q_num
                                st.rerun()

        # Collapsible Reference Sheet
        with st.expander("📐 Reference Formula Sheet & Rules", expanded=False):
            if cfg.exam_type == "SAT":
                st.write("• **Area of Circle:** A = πr² | **Circumference:** C = 2πr")
                st.write("• **Pythagorean Theorem:** a² + b² = c²")
                st.write("• **Special Right Triangles:** 30°-60°-90° (x, x√3, 2x) | 45°-45°-90° (x, x, x√2)")
                st.write("• **Slope-Intercept Form:** y = mx + b | **Perpendicular Slope:** m_perp = -1/m")
                st.write("• **Circle Standard Form:** (x - h)² + (y - k)² = r²")
            else:
                st.write("• **Average / Mean:** Sum of values / Count")
                st.write("• **Work Rate:** 1/T_total = 1/T_1 + 1/T_2")
                st.write("• **Relative Speed (Opposite Directions):** Speed_1 + Speed_2")
                st.write("• **Relative Speed (Same Direction):** |Speed_1 - Speed_2|")

    # 3. POST-EXAM DIAGNOSTIC SCORECARD & SCALED REPORT
    elif st.session_state.sim_completed and st.session_state.sim_score:
        score = st.session_state.sim_score
        cfg = st.session_state.sim_config
        qs = st.session_state.sim_questions

        # Grand Scaled Score Banner
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1E3A8A, #3B82F6); border-radius: 14px; padding: 28px; color: white; margin-bottom: 20px;'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <h3 style='margin:0; color:#93C5FD; font-size:16px; text-transform:uppercase; letter-spacing:1px;'>Official Test Simulation Report</h3>
                    <h1 style='margin:6px 0; font-size:42px; font-weight:800; color:white;'>{score.scaled_score} <span style='font-size:24px; opacity:0.8;'>/ {score.max_scaled_score}</span></h1>
                    <div style='font-size:16px; color:#E0E7FF;'>Raw Accuracy: <strong>{score.correct_count} / {score.total_questions}</strong> ({score.raw_score_percent}%) | Attempted: {score.attempted_count}</div>
                </div>
                <div style='text-align:right;'>
                    <div style='background:rgba(255,255,255,0.2); padding:8px 18px; border-radius:20px; font-weight:700; font-size:16px; margin-bottom:6px;'>{score.percentile_estimate}</div>
                    <div style='font-size:14px; color:#DBEAFE;'>{score.readiness_level}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Section-by-Section Cards
        st.markdown("### 📊 Section-by-Section Scaled Performance")
        sec_cols = st.columns(len(score.section_breakdown))
        for i_col, (sec_name, sec_data) in enumerate(score.section_breakdown.items()):
            with sec_cols[i_col]:
                max_pts = sec_data.get('max_score', 800 if cfg.exam_type=='SAT' else 40)
                st.markdown(f"""
                <div style='background:white; border:1px solid #E2E8F0; border-radius:10px; padding:16px; text-align:center;'>
                    <h4 style='margin:0 0 6px 0; color:#1E293B;'>{sec_name}</h4>
                    <h2 style='margin:0; color:#2563EB;'>{sec_data.get('scaled_score', 0)} <span style='font-size:14px; color:#64748B;'>/ {max_pts}</span></h2>
                    <p style='margin:6px 0 0 0; color:#475569; font-size:14px;'>Accuracy: <strong>{sec_data.get('correct', 0)} / {sec_data.get('total', 0)}</strong> ({sec_data.get('percent', 0)}%)</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Weak Areas & Adaptive Action
        st.markdown("### 🎯 Priority Weak Areas & Action Plan")
        st.info(f"💡 **Recommendation:** {score.recommendation}")

        col_act1, col_act2 = st.columns([1.5, 1])
        with col_act1:
            if st.button("📅 Generate 3-Day Personalized Study Sprint for Weak Areas", type="primary", use_container_width=True, key=f"btn_sim_sched_{is_standalone}"):
                st.session_state.active_agent = "Scheduler Agent"
                plan = orchestrator.create_adaptive_schedule(exam_type=cfg.exam_type, days=3)
                st.session_state.study_plan = plan
                st.success("🎉 Adaptive Study Sprint generated based on your exam mistakes! Check the sidebar.")

        with col_act2:
            if st.button("🔄 Take Another Exam Simulation", use_container_width=True, key=f"btn_sim_restart_{is_standalone}"):
                st.session_state.sim_active = False
                st.session_state.sim_completed = False
                st.session_state.sim_config = None
                st.session_state.sim_questions = []
                st.session_state.sim_index = 0
                st.session_state.sim_answers = {}
                st.session_state.sim_flagged = set()
                st.session_state.sim_start_time = None
                st.session_state.sim_score = None
                st.rerun()

        st.markdown("---")

        # Question-by-Question Detailed Review
        st.markdown("### 📋 Complete Question-by-Question Solutions & Mistake Diagnosis")
        filter_opt = st.radio("Filter Review:", ["Show All Questions", "Missed Questions Only", "Flagged Questions Only"], horizontal=True, key=f"review_filter_{is_standalone}")

        for idx, q_item in enumerate(qs):
            user_choice = st.session_state.sim_answers.get(idx, "None")
            is_correct = (user_choice == q_item.correct_key)
            is_flagged = (idx in st.session_state.sim_flagged)

            if filter_opt == "Missed Questions Only" and is_correct:
                continue
            if filter_opt == "Flagged Questions Only" and not is_flagged:
                continue

            status_badge = "✅ Correct" if is_correct else ("⚪ Skipped" if user_choice == "None" else "❌ Missed")
            flag_marker = " 🚩" if is_flagged else ""

            with st.expander(f"Q{idx + 1}: {status_badge}{flag_marker} (Your Answer: {user_choice} | Correct: {q_item.correct_key}) — {q_item.topic}", expanded=(not is_correct)):
                st.markdown(f"**Question:** {q_item.question}")
                for opt in q_item.options:
                    prefix = "👉 " if opt.key == user_choice else "• "
                    suffix = " *(Your Answer)*" if opt.key == user_choice else ""
                    if opt.key == q_item.correct_key:
                        suffix += " ✅ *(Correct Answer)*"
                    st.write(f"{prefix}**{opt.key}:** {opt.text} {suffix}")

                st.markdown("**How to solve it:**")
                clean_rat = q_item.rationale.replace("$r^2$", "r²").replace("$r$", "r").replace("$", "")
                st.write(clean_rat)

                if not is_correct and user_choice in q_item.distractor_analysis:
                    trap_explanation = q_item.distractor_analysis[user_choice]
                    st.markdown(f"""
                    <div style='background:#FEF2F2; border-left:4px solid #EF4444; padding:10px 14px; border-radius:6px; margin-top:8px;'>
                        <strong style='color:#991B1B;'>Why you missed this:</strong> <span style='color:#374151;'>{trap_explanation}</span>
                    </div>
                    """, unsafe_allow_html=True)


# ================= SIDEBAR =================
with st.sidebar:
    st.title("🎓 AI Prep Mentor")
    st.caption("Agentic Test Preparation & Study System")

    exam_type = st.radio("Select Target Exam", ["SAT", "GAT"], index=default_exam_idx, horizontal=True)

    # Automatically reset quiz state if exam type changed
    if st.session_state.last_exam_type is not None and st.session_state.last_exam_type != exam_type:
        st.session_state.last_exam_type = exam_type
        st.session_state.hint_history = []
        st.session_state.eval_result = None
        st.session_state.current_question = None
        st.session_state.target_topic = None
        st.session_state.last_selected_topic = None
        st.session_state.quiz_questions = []
        st.session_state.quiz_index = 0
        st.session_state.quiz_evals = {}
        st.session_state.quiz_answers = {}
        st.session_state.quiz_completed = False
        st.session_state.quiz_started = False
        st.session_state.show_inline_quiz = False
        st.session_state.sim_active = False
        st.session_state.sim_completed = False
        st.session_state.sim_config = None
        st.session_state.sim_questions = []
        st.session_state.sim_index = 0
        st.session_state.sim_answers = {}
        st.session_state.sim_flagged = set()
        st.session_state.sim_start_time = None
        st.session_state.sim_score = None
        st.rerun()
    else:
        st.session_state.last_exam_type = exam_type

    if st.button("🔄 Refresh / Clear Session", use_container_width=True):
        st.session_state.hint_history = []
        st.session_state.eval_result = None
        st.session_state.current_question = None
        st.session_state.target_topic = None
        st.session_state.last_selected_topic = None
        st.session_state.quiz_questions = []
        st.session_state.quiz_index = 0
        st.session_state.quiz_evals = {}
        st.session_state.quiz_answers = {}
        st.session_state.quiz_completed = False
        st.session_state.quiz_started = False
        st.session_state.show_inline_quiz = False
        st.session_state.sim_active = False
        st.session_state.sim_completed = False
        st.session_state.sim_config = None
        st.session_state.sim_questions = []
        st.session_state.sim_index = 0
        st.session_state.sim_answers = {}
        st.session_state.sim_flagged = set()
        st.session_state.sim_start_time = None
        st.session_state.sim_score = None
        st.rerun()

    st.divider()

    # Optional Gemini Key Manager
    with st.expander("🔑 Gemini API Key (Optional)", expanded=False):
        st.caption("Paste your Gemini API key to enable live AI question generation. Otherwise, the app seamlessly runs on the expanded 90+ question bank.")
        api_input = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_api_key, key="input_api_key")
        if st.button("Save Key", use_container_width=True, key="btn_save_key"):
            if api_input.strip():
                st.session_state.gemini_api_key = api_input.strip()
                orchestrator.set_api_key(api_input.strip())
                st.success("✅ Gemini Connected!")
            else:
                st.session_state.gemini_api_key = ""
                st.info("Cleared key. Using calibrated library.")

    st.divider()

    # Multi-Agent Status Inspector
    st.subheader("🤖 Active Agent Swarm")
    agents = ["Curriculum Agent", "Diagnostic Agent", "Cognitive Error Agent", "Socratic Tutor Agent", "Scheduler Agent"]
    for ag in agents:
        status_class = "agent-active" if st.session_state.active_agent == ag else "agent-idle"
        icon = "⚡" if st.session_state.active_agent == ag else "💤"
        st.markdown(f"<span class='agent-pill {status_class}'>{icon} {ag}</span>", unsafe_allow_html=True)

    st.divider()

    # Student Mastery Dashboard
    st.subheader("📊 Your Mastery Profile")
    stats = orchestrator.get_student_mastery_stats()
    summary = stats["summary"]

    if summary:
        for topic, data in summary.items():
            st.write(f"**{topic}**")
            st.progress(data["score_percent"] / 100.0)
            st.caption(f"Accuracy: {data['score_percent']}% ({data['correct']}/{data['attempts']})")
    else:
        st.info("Study a portion and take a quiz to generate your mastery baseline.")

    st.divider()

    # Adaptive Scheduler Trigger
    st.subheader("📅 Adaptive Study Sprint")
    if st.button("Generate Dynamic Schedule", use_container_width=True):
        st.session_state.active_agent = "Scheduler Agent"
        plan = orchestrator.create_adaptive_schedule(exam_type=exam_type, days=3)
        st.session_state.study_plan = plan

    if "study_plan" in st.session_state:
        plan = st.session_state.study_plan
        st.success(f"**{plan.target_exam} 3-Day Sprint Ready!**")
        st.caption(f"_{plan.motivational_note}_")
        for task in plan.tasks:
            with st.expander(f"Day {task.day}: {task.focus_topic} ({task.estimated_minutes}m)"):
                st.write(task.task_description)


# Fetch available topics for this exam
available_topics = orchestrator.get_available_topics(exam_type=exam_type)


# ================= CASE A: DEDICATED NEW-TAB QUIZ MODE =================
if url_mode == "quiz":
    target_topic = url_topic or st.session_state.target_topic or available_topics[0]
    st.session_state.target_topic = target_topic

    st.markdown("<div class='main-header'>🎯 AI Mentor: Section Quiz Mode</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>Dedicated quiz window for <strong>{target_topic}</strong> ({exam_type})</div>", unsafe_allow_html=True)

    col_nav, _ = st.columns([1.5, 2.5])
    with col_nav:
        st.link_button("📖 Return to Full Study Mentor", url="/", use_container_width=True)

    st.markdown("---")

    # Load questions for this topic if needed
    if not st.session_state.quiz_questions or st.session_state.last_selected_topic != target_topic:
        st.session_state.last_selected_topic = target_topic
        st.session_state.quiz_questions = orchestrator.get_topic_quiz(target_topic, exam_type=exam_type)
        st.session_state.quiz_index = 0
        st.session_state.quiz_evals = {}
        st.session_state.quiz_answers = {}
        st.session_state.quiz_completed = False
        st.session_state.hint_history = []

    render_quiz_flow(orchestrator, exam_type, is_standalone=True)
    st.stop()


# ================= CASE A2: DEDICATED NEW-TAB SIMULATOR MODE =================
if url_mode == "sim":
    url_length = params.get("length", "full")
    st.markdown("<div class='main-header'>🎯 AI Mentor: Exam Simulation Mode</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>Dedicated test window for <strong>{exam_type}</strong> ({url_length.title()} Exam)</div>", unsafe_allow_html=True)

    col_nav, _ = st.columns([1.5, 2.5])
    with col_nav:
        st.link_button("📖 Return to Main Dashboard", url="/", use_container_width=True)

    st.markdown("---")
    render_simulator_flow(orchestrator, exam_type, initial_mode=url_length, is_standalone=True)
    st.stop()


# ================= CASE B: MAIN STUDY DASHBOARD =================
st.markdown("<div class='main-header'>🎯 AI Mentor: Study & Diagnostic System</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Learn the concept first with Markdown RAG, then test your skills with cognitive diagnosis</div>", unsafe_allow_html=True)

# Dynamic Simulator Tab Badge
if st.session_state.get("sim_active", False):
    tab3_label = "🎯 3. Full Exam Simulator (🔴 LIVE EXAM IN PROGRESS)"
elif st.session_state.get("sim_completed", False):
    tab3_label = "🎯 3. Full Exam Simulator (🏆 SCORECARD READY)"
else:
    tab3_label = "🎯 3. Full Exam Simulator"

# Dynamic Simulator Tab Badge
if st.session_state.get("sim_active", False):
    tab3_label = "🎯 3. Full Exam Simulator (🔴 LIVE EXAM IN PROGRESS)"
elif st.session_state.get("sim_completed", False):
    tab3_label = "🎯 3. Full Exam Simulator (🏆 SCORECARD READY)"
else:
    tab3_label = "🎯 3. Full Exam Simulator"

# Quick Launch Banner on Dashboard (Opens in New Tab with Confirmation Screen)
with st.container():
    full_url = f"/?mode=sim&exam={exam_type}&length=full"
    half_url = f"/?mode=sim&exam={exam_type}&length=half"

    col_ban_info, col_ban_full, col_ban_half = st.columns([2.2, 1.3, 1.3])
    with col_ban_info:
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #1E3A8A, #2563EB); border-radius: 8px; padding: 12px 16px; color: white;'>
            <div style='font-size: 15px; font-weight: 700;'>🎯 Official Test Day Simulator Ready</div>
            <div style='font-size: 13px; color: #DBEAFE;'>Practice with official timing, full question counts, and authentic scaled scores.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_ban_full:
        full_label = f"🚀 Full Exam ({'98 Qs' if exam_type == 'SAT' else '100 Qs'}) ↗"
        st.markdown(f"""
        <a href="{full_url}" target="_blank" class="quiz-launch-btn">
            {full_label}
        </a>
        """, unsafe_allow_html=True)
    with col_ban_half:
        half_label = f"⚡ Half Mock ({'49 Qs' if exam_type == 'SAT' else '50 Qs'}) ↗"
        st.markdown(f"""
        <a href="{half_url}" target="_blank" class="quiz-launch-btn">
            {half_label}
        </a>
        """, unsafe_allow_html=True)

st.markdown("")

# Workflow Tabs: 1. Study & Targeted Quiz vs 2. Free Diagnostic Drill vs 3. Full Exam Simulator
tab_study, tab_drill, tab_sim = st.tabs([
    "📚 1. Study Topic & Take Quiz",
    "⚡ 2. Quick Diagnostic Drill",
    tab3_label
])
# ================= TAB 1: STUDY THEN QUIZ =================
with tab_study:
    st.markdown("### 📖 Step 1: Review What to Study")
    st.caption("The Curriculum Agent pulls the exact theory, formulas, and traps from your prep book.")

    selected_topic = st.selectbox(
        "Choose syllabus topic to study:",
        available_topics,
        key=f"topic_selector_{exam_type}"
    )

    # When dropdown changes, update target topic and reset inline quiz
    if st.session_state.last_selected_topic != selected_topic:
        st.session_state.last_selected_topic = selected_topic
        st.session_state.target_topic = selected_topic
        st.session_state.quiz_questions = orchestrator.get_topic_quiz(selected_topic, exam_type=exam_type)
        st.session_state.quiz_started = False
        st.session_state.show_inline_quiz = False
        st.session_state.quiz_index = 0
        st.session_state.quiz_evals = {}
        st.session_state.quiz_answers = {}
        st.session_state.quiz_completed = False
        st.session_state.hint_history = []

    # Fetch and display lesson material cleanly
    lesson_text = orchestrator.get_topic_lesson(selected_topic, exam_type=exam_type)
    
    with st.container():
        st.markdown(f"""
        <div class='lesson-box'>
            <h4>📘 Study Guide: {selected_topic}</h4>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(lesson_text)

    # Section Quiz Launch Area
    encoded_topic = urllib.parse.quote(selected_topic)
    quiz_newtab_url = f"/?mode=quiz&exam={exam_type}&topic={encoded_topic}"

    st.markdown("---")
    st.markdown("### 🎯 Step 2: Test Yourself with a Custom Quiz")
    st.write(f"Ready to test your knowledge on **{selected_topic}**?")

    col_newtab, col_inline = st.columns([1.2, 1], gap="medium")
    with col_newtab:
        st.markdown(f"""
        <a href="{quiz_newtab_url}" target="_blank" class="quiz-launch-btn">
            🚀 Start Quiz (Opens in New Tab) ↗
        </a>
        """, unsafe_allow_html=True)
    with col_inline:
        if st.button("📝 Or Practice Here in this Window", use_container_width=True, key="btn_practice_inline"):
            st.session_state.target_topic = selected_topic
            st.session_state.quiz_questions = orchestrator.get_topic_quiz(selected_topic, exam_type=exam_type)
            st.session_state.quiz_started = False
            st.session_state.show_inline_quiz = True
            st.session_state.quiz_index = 0
            st.session_state.quiz_evals = {}
            st.session_state.quiz_answers = {}
            st.session_state.quiz_completed = False
            st.session_state.hint_history = []
            st.rerun()

    # If student chose to practice in this window, render quiz flow below
    if st.session_state.get("show_inline_quiz", False):
        st.markdown("---")
        render_quiz_flow(orchestrator, exam_type, is_standalone=False)


# ================= TAB 2: RAPID DRILL =================
with tab_drill:
    st.markdown("### ⚡ Mixed Diagnostic Challenge")
    st.caption("Test across random syllabus topics to uncover hidden weak spots.")
    
    col_d1, col_d2 = st.columns([1, 1])
    with col_d1:
        drill_count = st.selectbox("Drill Length", [5, 10, 15], index=0, format_func=lambda x: f"{x} Questions", key="drill_len")
    with col_d2:
        drill_diff = st.selectbox("Difficulty", ["Medium", "Easy", "Hard"], index=0, key="drill_diff")

    if st.button("🎲 Generate Mixed Challenge", type="primary", use_container_width=True, key="btn_gen_mixed"):
        st.session_state.active_agent = "Diagnostic Agent"
        st.session_state.target_topic = "Mixed Diagnostic Challenge"
        
        st.session_state.quiz_questions = orchestrator.get_custom_quiz(
            topic="Mixed Diagnostic Challenge",
            exam_type=exam_type,
            count=drill_count,
            difficulty=drill_diff,
            use_ai=bool(st.session_state.gemini_api_key)
        )
        st.session_state.quiz_index = 0
        st.session_state.quiz_evals = {}
        st.session_state.quiz_answers = {}
        st.session_state.quiz_completed = False
        st.session_state.quiz_started = True
        st.session_state.hint_history = []
        st.session_state.show_drill_quiz = True
        st.rerun()

    if st.session_state.get("show_drill_quiz", False) and st.session_state.quiz_questions:
        st.markdown("---")
        render_quiz_flow(orchestrator, exam_type, is_standalone=False)



# ================= TAB 3: FULL & HALF EXAM SIMULATOR =================
with tab_sim:
    render_simulator_flow(orchestrator, exam_type, initial_mode="full", is_standalone=False)
