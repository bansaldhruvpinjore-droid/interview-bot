"""
Text-Only Interview Bot (Version 1 -- hardened)
------------------------------------------------
A terminal app that:
  1. Asks the user to pick a role
  2. Generates interview questions across varied categories with a free
     AI model via OpenRouter
  3. Takes typed answers
  4. Gets AI feedback + a score for each answer
  5. Prints a final summary
  6. Saves the full session to a JSON transcript file
  7. Logs events to a file, and exits gracefully (saving partial progress)
     if the AI service fails.

Run with: python interview.py
"""

import os
import re
import sys
import json
import time
import random
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

SESSIONS_DIR = "sessions"
LOGS_DIR = "logs"
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "app.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("interview_bot")

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    logger.error("No OPENROUTER_API_KEY found in environment.")
    print("ERROR: No OPENROUTER_API_KEY found.")
    print("Create a .env file (copy .env.example) and add your key.")
    sys.exit(1)

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

MODEL = "openrouter/free"
NUM_QUESTIONS = 5

QUESTION_CATEGORIES = [
    "Behavioral (a story about a past experience)",
    "Technical / role-specific skills",
    "Problem-solving / analytical thinking",
    "Communication and stakeholder management",
    "Leadership and ownership",
    "Situational judgment (a hypothetical scenario)",
]

CATEGORY_ANGLES = {
    "Behavioral (a story about a past experience)": [
        "a conflict with a coworker or teammate",
        "a project that failed or went wrong",
        "receiving critical feedback",
        "working under a tight deadline",
        "mentoring or helping someone else",
    ],
    "Technical / role-specific skills": [
        "debugging a hard-to-find issue",
        "designing a system or architecture",
        "evaluating a trade-off between two technical approaches",
        "learning a new tool or technology quickly",
        "improving performance or scalability",
    ],
    "Problem-solving / analytical thinking": [
        "handling incomplete or messy data/information",
        "breaking down an ambiguous problem",
        "prioritizing competing tasks with limited resources",
        "making a decision without complete information",
        "root-causing a recurring issue",
    ],
    "Communication and stakeholder management": [
        "explaining a technical concept to a non-technical audience",
        "managing disagreement between stakeholders",
        "delivering unwelcome news",
        "aligning a team around a shared goal",
        "negotiating scope or timeline",
    ],
    "Leadership and ownership": [
        "taking initiative without being asked",
        "owning a mistake and fixing it",
        "leading without formal authority",
        "motivating a struggling team member",
        "driving a project to completion despite obstacles",
    ],
    "Situational judgment (a hypothetical scenario)": [
        "an unexpected production or operational issue",
        "a sudden change in requirements or priorities",
        "an ethical dilemma",
        "a resource or staffing shortage",
        "conflicting instructions from two managers",
    ],
}


def pick_angle(category: str) -> str:
    return random.choice(CATEGORY_ANGLES.get(category, [""]))


class AIServiceError(Exception):
    """Raised when the AI backend fails after all retries are exhausted."""
    pass


def ask_ai(prompt: str, temperature: float = 0.8) -> str:
    last_error = None
    for attempt in range(1, 5):
        try:
            logger.info(f"Calling AI model (attempt {attempt}/4)...")
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=500,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content
            if content:
                logger.info("AI call succeeded.")
                return content.strip()
            logger.warning("AI returned an empty response, retrying...")
        except Exception as e:
            last_error = e
            logger.warning(f"AI call failed ({type(e).__name__}: {e}), retrying in 10s...")
        time.sleep(10)

    logger.error(f"AI service failed after 4 attempts. Last error: {last_error}")
    raise AIServiceError(f"AI service unavailable after 4 attempts: {last_error}")


def parse_score(feedback: str) -> Optional[int]:
    match = re.search(r"Score:\s*(\d{1,2})\s*/\s*10", feedback, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def assign_categories(num_questions: int) -> list:
    pool = QUESTION_CATEGORIES.copy()
    random.shuffle(pool)
    if num_questions <= len(pool):
        return pool[:num_questions]
    result = []
    while len(result) < num_questions:
        random.shuffle(pool)
        result.extend(pool)
    return result[:num_questions]


def is_too_similar(question: str, asked_so_far: list, threshold: float = 0.55) -> bool:
    q_words = set(re.findall(r"\w+", question.lower()))
    for prev in asked_so_far:
        prev_words = set(re.findall(r"\w+", prev.lower()))
        if not q_words or not prev_words:
            continue
        overlap = len(q_words & prev_words) / len(q_words | prev_words)
        if overlap > threshold:
            return True
    return False


def get_role() -> str:
    print("=" * 50)
    print("  AI INTERVIEW PRACTICE BOT")
    print("=" * 50)
    role = input("\nWhat role are you practicing for? (e.g. Software Engineer): ").strip()
    while not role:
        role = input("Please enter a role: ").strip()
    return role


def generate_question(role: str, question_number: int, asked_so_far: list, category: str) -> str:
    already_asked = "\n".join(f"- {q}" for q in asked_so_far) or "None yet"
    angle = pick_angle(category)
    angle_line = f"\nSpecific angle to focus on: {angle}" if angle else ""
    prompt = f"""You are an interviewer for a {role} position.
Generate ONE realistic interview question (question #{question_number} of {NUM_QUESTIONS}).

Category for this question: {category}{angle_line}

Rules:
- The question MUST fit the category above, and should draw on the specific angle if one is given.
- Do not repeat or closely resemble any of these already-asked questions:
{already_asked}
- Return ONLY the question text, nothing else (no preamble, no numbering)."""

    question = ask_ai(prompt, temperature=0.9)

    if is_too_similar(question, asked_so_far):
        logger.warning("Generated question too similar to a previous one, regenerating...")
        retry_prompt = prompt + (
            "\n\nIMPORTANT: Your previous attempt was too similar to an "
            "already-asked question. Use a genuinely different scenario, "
            "wording, and angle this time, while staying in the same category."
        )
        question = ask_ai(retry_prompt, temperature=1.0)

    return question


def get_feedback(role: str, question: str, answer: str) -> str:
    prompt = f"""You are an experienced interviewer/coach for a {role} position.

Question asked: {question}
Candidate's answer: {answer}

Give concise, constructive feedback (3-5 sentences) covering:
- What was strong about the answer
- What could be improved
- A score out of 10

Format your response as:
Score: X/10
Feedback: <your feedback>"""
    return ask_ai(prompt, temperature=0.5)


def generate_summary(role: str, transcript: list) -> str:
    formatted = "\n\n".join(
        f"Q{i+1}: {t['question']}\nAnswer: {t['answer']}\n{t['feedback']}"
        for i, t in enumerate(transcript)
    )
    prompt = f"""You just finished coaching a candidate through a {NUM_QUESTIONS}-question
mock interview for a {role} role. Here is the full transcript:

{formatted}

Write a short overall summary (5-8 sentences):
- Overall performance impression
- 2-3 recurring strengths
- 2-3 things to work on before a real interview
- An overall score out of 10"""
    return ask_ai(prompt, temperature=0.5)


def save_transcript(role: str, transcript: list, summary: Optional[str], completed: bool) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_role = role.lower().replace(" ", "-")
    filename = f"{timestamp}_{safe_role}.json"
    filepath = os.path.join(SESSIONS_DIR, filename)

    session_data = {
        "role": role,
        "timestamp": datetime.now().isoformat(),
        "completed": completed,
        "num_questions_answered": len(transcript),
        "transcript": transcript,
        "summary": summary,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)

    logger.info(f"Transcript saved to {filepath}")
    return filepath


def main():
    role = get_role()
    logger.info(f"Session started for role: {role}")
    print(f"\nGreat -- starting a {NUM_QUESTIONS}-question mock interview for: {role}\n")

    transcript = []
    asked_questions = []
    categories = assign_categories(NUM_QUESTIONS)

    try:
        for i in range(1, NUM_QUESTIONS + 1):
            category = categories[i - 1]
            print(f"\n--- Question {i}/{NUM_QUESTIONS} ({category}) ---")
            question = generate_question(role, i, asked_questions, category)
            asked_questions.append(question)
            print(f"\nInterviewer: {question}\n")

            answer = input("Your answer: ").strip()
            while not answer:
                answer = input("(Please type an answer): ").strip()

            print("\nGetting feedback...")
            feedback = get_feedback(role, question, answer)
            print(f"\n{feedback}")

            transcript.append({"question": question, "answer": answer, "feedback": feedback, "category": category})

        print("\n" + "=" * 50)
        print("  INTERVIEW COMPLETE -- GENERATING SUMMARY")
        print("=" * 50)
        summary = generate_summary(role, transcript)
        print(f"\n{summary}\n")

        filepath = save_transcript(role, transcript, summary, completed=True)
        print(f"Session saved to: {filepath}")
        logger.info("Session completed successfully.")

    except AIServiceError as e:
        logger.error(f"Session ended early due to AI service failure: {e}")
        print("\n" + "=" * 50)
        print("  Sorry, the AI service is unavailable right now.")
        print("  Ending the session early -- your progress so far is saved.")
        print("=" * 50)
        filepath = save_transcript(role, transcript, summary=None, completed=False)
        print(f"Partial session saved to: {filepath}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterview cancelled. Bye!")
        logger.info("Session cancelled by user (KeyboardInterrupt).")
        sys.exit(0)
