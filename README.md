# AI Interview Practice Bot — Version 1 (Text-Only MVP)

A terminal app that runs you through a 5-question mock interview using Claude,
and gives you feedback + a score after each answer, plus a final summary.

This is intentionally simple: no web framework, no database, no voice.
Just Python + an API call. Get this fully working before moving on to
Version 2 (web app).

## What you need before starting

- Python 3.9+ installed (`python3 --version` to check)
- A free OpenRouter API key: https://openrouter.ai → sign up → **Keys** → **Create Key**
  - No credit card required. Free models are rate-limited (roughly 20
    requests/minute, 200/day) but that's plenty for daily interview practice.
  - This project uses `model = "openrouter/free"`, which auto-picks a
    working free model for you. To pin a specific one instead, edit `MODEL`
    in `interview.py` to something like `meta-llama/llama-3.3-70b:free`
    (see openrouter.ai/models, filter by free).

## Setup (do this once)

1. **Open a terminal in this folder.**

2. **Create a virtual environment** (keeps this project's packages separate
   from everything else on your machine):

   ```bash
   python3 -m venv venv
   ```

3. **Activate it:**

   - Mac/Linux: `source venv/bin/activate`
   - Windows (PowerShell): `venv\Scripts\Activate.ps1`
   - Windows (cmd): `venv\Scripts\activate.bat`

   You'll know it worked because your terminal prompt will show `(venv)` at
   the start of the line.

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Add your API key:**

   Windows (PowerShell): `copy .env.example .env`
   Mac/Linux: `cp .env.example .env`

   Then open `.env` in a text editor and paste your real key in place of
   `your-openrouter-api-key-here`. Never commit this file to git or share
   it — treat it like a password.

## Run it

```bash
python interview.py
```

You'll be asked to type a role (e.g. "Software Engineer", "Product Manager",
"Data Analyst"), then you'll go through 5 questions, typing your answer to
each one and getting feedback right away. At the end you get an overall
summary and score.

## If something breaks

- **`ModuleNotFoundError`** → your virtual environment probably isn't
  activated. Re-run the activate command from step 3.
- **`ERROR: No OPENROUTER_API_KEY found`** → check that `.env` exists (not
  just `.env.example`) and that the key is pasted in correctly with no
  quotes or extra spaces.
- **`AuthenticationError` from the API** → your key is invalid or was
  revoked. Generate a new one at openrouter.ai/keys.
- **`429` rate limit errors** → free tier is capped around 20 requests/min
  and 200/day. Wait a bit, or switch `MODEL` in `interview.py` to a
  specific `:free` model if `openrouter/free` keeps landing on a busy one.
- **Slow or inconsistent answers** → free models vary in quality/speed since
  they're shared, best-effort infrastructure. If it's inconsistent, pin a
  specific model (e.g. `deepseek/deepseek-r1-distill:free`) instead of the
  auto-router.

## Once this works, try tweaking it

Small changes that'll teach you a lot before you move to Version 2:

- Change `NUM_QUESTIONS` at the top of `interview.py`
- Adjust the prompts in `generate_question` or `get_feedback` to change the
  interviewer's style (harsher, friendlier, more technical, etc.)
- Save the transcript to a `.txt` file at the end instead of just printing it
- Add a difficulty level the user picks alongside the role

## Project structure

```
interview-bot/
├── interview.py       # main script — all the logic lives here
├── requirements.txt   # Python packages this project needs
├── .env.example        # template for your API key — copy to .env
├── .env                 # your actual key (you create this, never share it)
└── README.md           # this file
```

## Next step

Once you can comfortably run this, answer questions, and read the feedback
without errors — you're done with Version 1. Version 2 wraps this same
logic in a simple web UI (Flask or Streamlit) so it runs in a browser
instead of the terminal.
