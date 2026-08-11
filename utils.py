"""
utils.py
--------
Helper functions for the AI Quiz Generator Assistant.
Contains input validation, score calculation, timer formatting,
local JSON-based history persistence, and text export helpers.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_history.json")


# --------------------------------------------------------------------------
# Input validation
# --------------------------------------------------------------------------

def validate_inputs(topic: str, num_questions: int) -> Tuple[bool, str]:
    """Validate user-provided inputs before calling the AI model."""
    if topic is None or not topic.strip():
        return False, "Please enter a topic for the quiz."
    if len(topic.strip()) < 2:
        return False, "Topic must be at least 2 characters long."
    if len(topic.strip()) > 200:
        return False, "Topic is too long. Please keep it under 200 characters."
    if not isinstance(num_questions, int):
        return False, "Number of questions must be a whole number."
    if num_questions < 1:
        return False, "Number of questions must be at least 1."
    if num_questions > 25:
        return False, "Please request 25 questions or fewer per quiz."
    return True, ""


def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """Check that a Google API key is present before attempting generation."""
    if not api_key or not api_key.strip():
        return False, (
            "GOOGLE_API_KEY is missing. Please add it to your .env file "
            "(see .env.example) and restart the app."
        )
    return True, ""


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

def calculate_score(quiz: List[Dict[str, Any]], user_answers: Dict[int, str]) -> Dict[str, Any]:
    """Calculate the final score for a completed quiz."""
    total = len(quiz)
    correct_count = 0
    breakdown = []

    for idx, question in enumerate(quiz):
        user_answer = user_answers.get(idx, None)
        correct_answer = question.get("correct_answer", "")
        is_correct = (
            user_answer is not None
            and str(user_answer).strip().lower() == str(correct_answer).strip().lower()
        )
        if is_correct:
            correct_count += 1

        breakdown.append({
            "question": question.get("question", ""),
            "options": question.get("options", []),
            "user_answer": user_answer if user_answer is not None else "No answer",
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": question.get("explanation", ""),
        })

    wrong_count = total - correct_count
    percentage = round((correct_count / total) * 100, 2) if total > 0 else 0.0

    return {
        "total": total,
        "correct": correct_count,
        "wrong": wrong_count,
        "percentage": percentage,
        "breakdown": breakdown,
    }


# --------------------------------------------------------------------------
# Timer formatting
# --------------------------------------------------------------------------

def format_time(seconds: float) -> str:
    """Format a duration in seconds as MM:SS for display in the quiz timer."""
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


# --------------------------------------------------------------------------
# History persistence (quiz history + score history)
# --------------------------------------------------------------------------

def load_history() -> List[Dict[str, Any]]:
    """Load quiz/score history from the local JSON file. Returns [] if none exists."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def save_history_entry(
    topic: str,
    difficulty: str,
    question_type: str,
    num_questions: int,
    score_data: Dict[str, Any],
) -> None:
    """Append a completed quiz's summary to the local history file."""
    history = load_history()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "topic": topic,
        "difficulty": difficulty,
        "question_type": question_type,
        "num_questions": num_questions,
        "correct": score_data["correct"],
        "wrong": score_data["wrong"],
        "percentage": score_data["percentage"],
    }
    history.insert(0, entry)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except OSError:
        pass


def clear_history() -> None:
    """Delete all saved quiz/score history."""
    if os.path.exists(HISTORY_FILE):
        try:
            os.remove(HISTORY_FILE)
        except OSError:
            pass


# --------------------------------------------------------------------------
# Export helpers (download quiz / results as text files)
# --------------------------------------------------------------------------

def export_quiz_to_text(quiz: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    """Build a plain-text version of the quiz (questions + answer key) for download."""
    lines = []
    lines.append(f"AI QUIZ GENERATOR - {meta.get('topic', '').upper()}")
    lines.append(f"Difficulty: {meta.get('difficulty', '')} | Type: {meta.get('question_type', '')}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    for idx, q in enumerate(quiz, start=1):
        lines.append(f"Q{idx}. {q.get('question', '')}")
        for opt_letter, opt in zip("ABCD", q.get("options", [])):
            lines.append(f"   {opt_letter}. {opt}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("ANSWER KEY")
    lines.append("=" * 60)
    for idx, q in enumerate(quiz, start=1):
        lines.append(f"Q{idx}: {q.get('correct_answer', '')}")
        lines.append(f"   Explanation: {q.get('explanation', '')}")
        lines.append("")

    return "\n".join(lines)


def export_results_to_text(quiz: List[Dict[str, Any]], score_data: Dict[str, Any], meta: Dict[str, Any]) -> str:
    """Build a plain-text results report (score + per-question breakdown) for download."""
    lines = []
    lines.append(f"AI QUIZ GENERATOR - RESULTS: {meta.get('topic', '').upper()}")
    lines.append(f"Difficulty: {meta.get('difficulty', '')} | Type: {meta.get('question_type', '')}")
    lines.append(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append(
        f"Score: {score_data['correct']}/{score_data['total']} "
        f"({score_data['percentage']}%)  |  Wrong: {score_data['wrong']}"
    )
    lines.append("=" * 60)
    lines.append("")

    for idx, item in enumerate(score_data["breakdown"], start=1):
        status = "CORRECT" if item["is_correct"] else "WRONG"
        lines.append(f"Q{idx}. [{status}] {item['question']}")
        lines.append(f"   Your answer:    {item['user_answer']}")
        lines.append(f"   Correct answer: {item['correct_answer']}")
        lines.append(f"   Explanation:    {item['explanation']}")
        lines.append("")

    return "\n".join(lines)
