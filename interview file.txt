"""
Text-Only Interview Bot (Version 1 MVP)
----------------------------------------
A terminal app that:
  1. Asks the user to pick a role
  2. Generates interview questions with a free AI model via OpenRouter
  3. Takes typed answers
  4. Gets AI feedback + a score for each answer
  5. Prints a final summary

Run with: python interview.py
"""

import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

load_dotenv()  # reads variables from a local .env file

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    print("ERROR: No OPENROUTER_API_KEY found.")
    print("Create a .env file (copy .env.example) and add your key.")
    sys.exit(1)

# OpenRouter is OpenAI-compatible — same SDK, just a different base_url + key
client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

# "openrouter/free" auto-picks a working free model for you.
# To pin a specific one instead, use an id ending in ":free", e.g.
# "meta-llama/llama-3.3-70b:free" or "deepseek/deepseek-r1-distill:free"
MODEL = "openrouter/free"

NUM_QUESTIONS = 5


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def ask_ai(prompt: str) -> str:
    """Send a single prompt to the model via OpenRouter and return the text response."""
    last_error = None
    for attempt in range(4):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content
            if content:
                return content.strip()
        except Exception as e:
            last_error = e
            print(f"Attempt {attempt + 1} failed ({type(e).__name__}), retrying in 10s...")
            time.sleep(10)
    raise RuntimeError(f"Failed after 4 attempts. Last error: {last_error}")


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


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    role = get_role()
    print(f"\nGreat — starting a {NUM_QUESTIONS}-question mock interview for: {role}\n")

    transcript = []
    asked_questions = []

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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterview cancelled. Bye!")
        sys.exit(0)
