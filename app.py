"""
app.py
------
Streamlit Web Application for the AI Quiz Generator Assistant.
Features:
- Gemini API-powered Quiz Generation
- Interactive Quiz Taking with Timer
- Automatic Scoring & Detailed Feedback
- History Tracking & JSON Persistence
- Quiz & Results Export (TXT)
"""

import time
import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import local helper modules
from utils import (
    validate_inputs,
    validate_api_key,
    calculate_score,
    format_time,
    load_history,
    save_history_entry,
    clear_history,
    export_quiz_to_text,
    export_results_to_text,
)
from generator import generate_quiz

# --------------------------------------------------------------------------
# Page Configuration & Styling
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern glassmorphism aesthetic
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Header Styling */
    .app-header {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }
    
    .app-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }

    /* Cards */
    .quiz-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }

    .stat-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.2rem;
        font-weight: 700;
        color: #38bdf8;
    }

    .stat-label {
        color: #94a3b8;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Badge tags */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-correct { background-color: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; }
    .badge-wrong { background-color: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
    .badge-info { background-color: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #0284c7; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Session State Initialization
# --------------------------------------------------------------------------
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_meta" not in st.session_state:
    st.session_state.quiz_meta = {}
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "score_results" not in st.session_state:
    st.session_state.score_results = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None


# --------------------------------------------------------------------------
# Sidebar Configuration
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    env_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=env_api_key,
        type="password",
        help="Enter your Google Gemini API key or set GOOGLE_API_KEY in .env",
    )
    
    st.markdown("---")
    st.markdown("## 🎯 Quiz Parameters")
    
    topic_input = st.text_input(
        "Quiz Topic",
        placeholder="e.g., Python Data Structures, Solar System, World War II",
        help="Type any topic you want to generate a quiz for",
    )
    
    col1, col2 = st.columns(2)
    with col1:
        num_questions = st.number_input("Questions", min_value=1, max_value=25, value=5)
    with col2:
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        
    question_type = st.selectbox(
        "Question Type",
        ["Multiple Choice", "True / False"]
    )
    
    generate_button = st.button("🚀 Generate Quiz", use_container_width=True, type="primary")


# --------------------------------------------------------------------------
# App Header & Navigation Tabs
# --------------------------------------------------------------------------
st.markdown('<div class="app-header">🧠 AI Quiz Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Create, take, and master instant AI-generated quizzes on any topic!</div>', unsafe_allow_html=True)

tab_quiz, tab_history, tab_about = st.tabs(["📝 Quiz Workspace", "📜 Quiz History", "ℹ️ About & Help"])


# --------------------------------------------------------------------------
# Quiz Generation Handler
# --------------------------------------------------------------------------
if generate_button:
    # Validate API Key
    api_valid, api_msg = validate_api_key(api_key_input)
    if not api_valid:
        st.error(api_msg)
    else:
        # Validate inputs
        input_valid, input_msg = validate_inputs(topic_input, num_questions)
        if not input_valid:
            st.error(input_msg)
        else:
            with st.spinner(f"Generating a {difficulty} {num_questions}-question quiz on '{topic_input}' using Gemini..."):
                try:
                    quiz = generate_quiz(
                        topic=topic_input,
                        num_questions=int(num_questions),
                        difficulty=difficulty,
                        question_type=question_type,
                        api_key=api_key_input,
                    )
                    st.session_state.quiz_data = quiz
                    st.session_state.quiz_meta = {
                        "topic": topic_input,
                        "difficulty": difficulty,
                        "question_type": question_type,
                        "num_questions": len(quiz),
                    }
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.score_results = None
                    st.session_state.start_time = time.time()
                    st.success("Quiz generated successfully! Complete the questions below.")
                except Exception as e:
                    st.error(f"Error generating quiz: {e}")


# --------------------------------------------------------------------------
# Tab 1: Quiz Workspace
# --------------------------------------------------------------------------
with tab_quiz:
    if st.session_state.quiz_data is None:
        st.info("👈 Set your topic and parameters in the sidebar, then click **Generate Quiz** to start!")
    else:
        meta = st.session_state.quiz_meta
        quiz = st.session_state.quiz_data

        # Top Bar Info
        meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
        with meta_col1:
            st.markdown(f"**Topic:** {meta.get('topic')}")
        with meta_col2:
            st.markdown(f"**Difficulty:** {meta.get('difficulty')}")
        with meta_col3:
            st.markdown(f"**Type:** {meta.get('question_type')}")
        with meta_col4:
            if st.session_state.start_time and not st.session_state.quiz_submitted:
                elapsed = time.time() - st.session_state.start_time
                st.markdown(f"⏱️ **Time Elapsed:** {format_time(elapsed)}")
            else:
                st.markdown("⏱️ **Status:** Completed" if st.session_state.quiz_submitted else "⏱️ **Ready**")

        st.markdown("---")

        # ------------------------------------------------------------------
        # Active Quiz Taking View
        # ------------------------------------------------------------------
        if not st.session_state.quiz_submitted:
            st.markdown("### Answer the Questions:")
            
            with st.form("quiz_form"):
                for idx, q in enumerate(quiz):
                    st.markdown(f"#### Q{idx + 1}. {q.get('question')}")
                    options = q.get("options", [])
                    
                    selected_option = st.radio(
                        label=f"Select answer for Q{idx + 1}:",
                        options=options,
                        key=f"q_{idx}",
                        index=None,
                        label_visibility="collapsed",
                    )
                    if selected_option:
                        st.session_state.user_answers[idx] = selected_option
                    st.markdown("")

                submit_quiz_button = st.form_submit_button("🏁 Submit Quiz", use_container_width=True, type="primary")

            if submit_quiz_button:
                scores = calculate_score(quiz, st.session_state.user_answers)
                st.session_state.score_results = scores
                st.session_state.quiz_submitted = True
                
                # Save entry to local history file
                save_history_entry(
                    topic=meta.get("topic", ""),
                    difficulty=meta.get("difficulty", ""),
                    question_type=meta.get("question_type", ""),
                    num_questions=len(quiz),
                    score_data=scores,
                )
                st.rerun()

        # ------------------------------------------------------------------
        # Quiz Results & Score Breakdown View
        # ------------------------------------------------------------------
        else:
            scores = st.session_state.score_results
            st.markdown("## 📊 Quiz Results")

            # Stat summary row
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.markdown(f'<div class="stat-box"><div class="stat-number">{scores["percentage"]}%</div><div class="stat-label">Score</div></div>', unsafe_allow_html=True)
            with s2:
                st.markdown(f'<div class="stat-box"><div class="stat-number">{scores["correct"]}/{scores["total"]}</div><div class="stat-label">Correct</div></div>', unsafe_allow_html=True)
            with s3:
                st.markdown(f'<div class="stat-box"><div class="stat-number">{scores["wrong"]}</div><div class="stat-label">Wrong</div></div>', unsafe_allow_html=True)
            with s4:
                elapsed_str = format_time(time.time() - st.session_state.start_time) if st.session_state.start_time else "N/A"
                st.markdown(f'<div class="stat-box"><div class="stat-number">{elapsed_str}</div><div class="stat-label">Time Taken</div></div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### Detailed Question Review")

            for idx, item in enumerate(scores["breakdown"]):
                badge_class = "badge-correct" if item["is_correct"] else "badge-wrong"
                badge_label = "✓ CORRECT" if item["is_correct"] else "✗ INCORRECT"
                
                st.markdown(
                    f"""
                    <div class="quiz-card">
                        <span class="badge {badge_class}">{badge_label}</span>
                        <strong style="font-size: 1.1rem;">Q{idx + 1}. {item['question']}</strong>
                        <p style="margin-top: 0.8rem; margin-bottom: 0.3rem;"><strong>Your Answer:</strong> {item['user_answer']}</p>
                        <p style="margin-bottom: 0.8rem;"><strong>Correct Answer:</strong> {item['correct_answer']}</p>
                        <div style="background: rgba(255,255,255,0.05); padding: 0.8rem; border-radius: 6px; border-left: 3px solid #38bdf8;">
                            💡 <strong>Explanation:</strong> {item['explanation']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown("### 📥 Export & Downloads")

            exp1, exp2 = st.columns(2)
            with exp1:
                quiz_txt = export_quiz_to_text(quiz, meta)
                st.download_button(
                    label="📄 Download Quiz & Answer Key (TXT)",
                    data=quiz_txt,
                    file_name=f"quiz_{meta.get('topic', 'quiz').lower().replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with exp2:
                results_txt = export_results_to_text(quiz, scores, meta)
                st.download_button(
                    label="📊 Download Results Report (TXT)",
                    data=results_txt,
                    file_name=f"results_{meta.get('topic', 'quiz').lower().replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            st.markdown("")
            if st.button("🔄 Retake or Create New Quiz", use_container_width=True, type="secondary"):
                st.session_state.quiz_data = None
                st.session_state.quiz_submitted = False
                st.session_state.score_results = None
                st.rerun()


# --------------------------------------------------------------------------
# Tab 2: Quiz History
# --------------------------------------------------------------------------
with tab_history:
    st.markdown("### 📜 Past Quiz Performance")
    history_records = load_history()

    if not history_records:
        st.info("No saved quiz history yet. Complete a quiz to view past results here!")
    else:
        st.markdown(f"Total quizzes completed: **{len(history_records)}**")
        st.dataframe(history_records, use_container_width=True)

        if st.button("🗑️ Clear History", type="secondary"):
            clear_history()
            st.success("History cleared successfully!")
            st.rerun()


# --------------------------------------------------------------------------
# Tab 3: About & Help
# --------------------------------------------------------------------------
with tab_about:
    st.markdown(
        """
        ### About AI Quiz Generator Assistant
        This application uses Google's **Gemini AI** to create customized, high-quality quizzes on any topic in seconds.

        #### Features:
        - 🤖 **AI-Powered Question Generation**: Tailored questions by topic, count, difficulty, and question type.
        - ⏱️ **Timer & Instant Scoring**: Track your speed and receive automatic percentage scores.
        - 💡 **Explanations**: Learn from detailed explanations for every correct answer.
        - 💾 **Local Persistence**: Saves quiz scores locally to `quiz_history.json`.
        - 📥 **Export**: Download quizzes and results reports for offline practice or study.

        #### Setup Instructions:
        1. Obtain a Gemini API Key from [Google AI Studio](https://aistudio.google.com/).
        2. Paste your API key in the sidebar or set `GOOGLE_API_KEY` in your `.env` file.
        3. Run the app using:
           ```bash
           python -m streamlit run app.py
           ```
        """
    )