"""
Text-Only Interview Bot (Version 1 — hardened)
------------------------------------------------
A terminal app that:
  1. Asks the user to pick a role
  2. Generates interview questions with a free AI model via OpenRouter
  3. Takes typed answers
  4. Gets AI feedback + a score for each answer
  5. Prints a final summary
  6. Saves the full session to a JSON transcript file
  7. Logs events to a file, and exits gracefully (saving partial progress)
     if the AI service fails.

Run with: python interview.py
"""

import os
import sys
import json
import time
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


class AIServiceError(Exception):
    """Raised when the AI backend fails after all retries are exhausted."""
    pass


def ask_ai(prompt: str) -> str:
    last_error = None
    for attempt in range(1, 5):
        try:
            logger.info(f"Calling AI model (attempt {attempt}/4)...")
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=500,
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


def get_role() -> str:
    print("=" * 50)
    print("  AI INTERVIEW PRACTICE BOT")
    print("=" * 50)
    role = input("\nWhat role are you practicing for? (e.g. Software Engineer): ").strip()
    while not role:
        role = input("Please enter a role: ").strip()
    return role


def generate_question(role: str, question_number: int, asked_so_far: list) -> str:
    already_asked = "\n".join(f"- {q}" for q in asked_so_far) or "None yet"
    prompt = f"""You are an interviewer for a {role} position.
Generate ONE realistic interview question (question #{question_number} of {NUM_QUESTIONS}).

Rules:
- Do not repeat or closely resemble any of these already-asked questions:
{already_asked}
- Mix behavioral and technical/role-specific questions across the session.
- Return ONLY the question text, nothing else (no preamble, no numbering)."""
    return ask_ai(prompt)


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
    return ask_ai(prompt)


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
    return ask_ai(prompt)


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
    print(f"\nGreat — starting a {NUM_QUESTIONS}-question mock interview for: {role}\n")

    transcript = []
    asked_questions = []

    try:
        for i in range(1, NUM_QUESTIONS + 1):
            print(f"\n--- Question {i}/{NUM_QUESTIONS} ---")
            question = generate_question(role, i, asked_questions)
            asked_questions.append(question)
            print(f"\nInterviewer: {question}\n")

            answer = input("Your answer: ").strip()
            while not answer:
                answer = input("(Please type an answer): ").strip()

            print("\nGetting feedback...")
            feedback = get_feedback(role, question, answer)
            print(f"\n{feedback}")

            transcript.append({"question": question, "answer": answer, "feedback": feedback})

        print("\n" + "=" * 50)
        print("  INTERVIEW COMPLETE — GENERATING SUMMARY")
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
        print("  Ending the session early — your progress so far is saved.")
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
