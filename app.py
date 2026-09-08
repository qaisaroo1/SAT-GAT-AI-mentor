import os
import urllib.parse
import streamlit as st
from src.orchestrator import MentorOrchestrator
from src.schemas import Question, ErrorAnalysisResult, SocraticHint

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
if "orchestrator" not in st.session_state:
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
            if st.button("✨ Start Fresh Quiz (Different Questions)", type="primary", use_container_width=True, key=f"btn_fresh_{is_standalone}"):
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
            if st.button("🔄 Retake Same Questions", use_container_width=True, key=f"btn_retake_{is_standalone}"):
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


# ================= CASE B: MAIN STUDY DASHBOARD =================
st.markdown("<div class='main-header'>🎯 AI Mentor: Study & Diagnostic System</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Learn the concept first with Markdown RAG, then test your skills with cognitive diagnosis</div>", unsafe_allow_html=True)

# Workflow Tabs: 1. Study & Targeted Quiz vs 2. Free Diagnostic Drill
tab_study, tab_drill = st.tabs(["📚 1. Study Topic & Take Quiz", "⚡ 2. Quick Diagnostic Drill"])

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
