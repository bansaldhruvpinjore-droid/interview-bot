# AI Interview Practice Bot -- Version 1 (Hardened Text-Based MVP)

A terminal app that runs you through a 5-question mock interview using a
free AI model (via OpenRouter), gives feedback + a score after each
answer, saves the full session to a file, and logs what happened along
the way.

## Features

- Role-based mock interview (5 questions, adapted to whatever role you enter)
- Per-answer AI feedback with a numeric score out of 10
- Overall summary at the end of the session
- **Session transcripts** saved automatically to `sessions/` as JSON --
  useful for reviewing past practice sessions or reporting on results
- **Logging** to `logs/app.log` -- records every API call attempt,
  retries, and session outcomes
- **Graceful failure handling** -- if the AI service is down or rate
  limited, the bot retries automatically, and if it still fails, it saves
  whatever progress exists and exits cleanly instead of crashing
- **Unit tests** (`pytest`) covering score parsing, transcript saving, and
  retry behavior -- no real API calls needed to run them

## What you need before starting

- Python 3.9+ installed (`python3 --version` to check)
- A free OpenRouter API key: https://openrouter.ai -> sign up -> Keys -> Create Key
  - No credit card required. Free models are rate-limited (roughly 20
    requests/minute, 200/day) but that's plenty for daily interview practice.
  - This project uses `MODEL = "openrouter/free"`, which auto-picks a
    working free model for each call. You can pin a specific model
    instead by editing `MODEL` in `interview.py`.

## Setup

1. Open a terminal in this folder.
2. Create a virtual environment: `python -m venv venv`
3. Activate it:
   - Windows (PowerShell): `venv\Scripts\Activate.ps1`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Add your API key:
   - Windows: `copy .env.example .env`
   - Mac/Linux: `cp .env.example .env`
   Then open `.env` and replace `your-openrouter-api-key-here` with your
   real key. Never commit this file or share it.

## Run it
Type a role (e.g. "Software Engineer", "Data Analyst"), answer 5
questions, and get feedback after each one. At the end you get an
overall summary, and the full session is saved automatically.

## Run the tests
All tests run offline with mocked API responses -- no real network calls,
no API quota used. You should see all tests pass in under 2 seconds.

## Architecture
+-----------------+
             |   User (CLI)    |
             +--------+--------+
                      |  role, answers
                      v
             +-----------------+
             |  interview.py   |
             |  main() loop    |
             +--------+--------+
                      |  prompts
                      v
             +-----------------+
             |  ask_ai()       |---- retries up to 4x on failure
             |  (via OpenAI    |---- raises AIServiceError if
             |   SDK)          |     all retries fail
             +--------+--------+
                      |  HTTPS
                      v
             +-----------------+
             |  OpenRouter API |
             |  (free model)   |
             +-----------------+
Flow summary: the user picks a role -> the bot generates a question via
the AI API -> the user answers -> the bot requests feedback + a score ->
this repeats 5 times -> a final summary is generated -> the full session
(or a partial one, if something failed) is saved to disk as JSON, with
every step logged along the way.

## Project structure
## Known limitations

- Free-tier models vary in quality and speed since they're shared,
  best-effort infrastructure -- occasional repeated or malformed questions
  can happen even with the auto-router
- No voice input/output or webcam features (out of scope for this version)

## Future work

- Web-based UI (Streamlit) instead of terminal
- Voice input (speech-to-text) and AI voice output (text-to-speech)
- Difficulty levels or industry-specific question sets
- Webcam-based emotion/confidence analysis (stretch goal, deliberately
  scoped out of this project)

## Troubleshooting

- ModuleNotFoundError -> venv isn't activated; re-run the activate command
- ERROR: No OPENROUTER_API_KEY found -> check .env exists and has your real key
- AuthenticationError -> key is invalid or revoked; generate a new one at openrouter.ai/keys
- 429 rate limit -> free tier caps around 20 req/min, 200/day; wait and retry
- Bot exits early with "AI service unavailable" -> this is the graceful-failure path working as designed; check logs/app.log for details
