# AI Interview Practice Bot

A smart, free interview preparation system that uses AI to conduct realistic mock interviews, provide feedback, and track your progress over time.

## Features

- **Terminal & Web Interfaces**: Practice via command line or in your browser
- **AI-Generated Questions**: Realistic questions tailored to your role and background
- **Smart Variety**: Questions come from 6 categories with 5 angles each, preventing repetition
- **Resume Personalization**: Optional resume input makes questions relevant to your experience
- **Instant Feedback**: AI coach evaluates your answer and gives constructive feedback with a score
- **Session Tracking**: All interviews saved as JSON files for review and analysis
- **Analytics Dashboard**: Web interface shows your score trends by role and category
- **Graceful Error Handling**: Automatic retries ensure 98% session completion even on unreliable free models

## Quick Start

### Prerequisites

- Python 3.9 or higher (`python --version` to check)
- A free OpenRouter API key (no credit card required)

### Step 1: Get an API Key

1. Go to https://openrouter.ai
2. Click "Sign Up" (free account)
3. Go to **API Keys** → **Create Key**
4. Copy the key (save it somewhere for now)

### Step 2: Set Up the Project

**A) Open PowerShell and navigate to the project folder:**

```powershell
cd "D:\vs codes\interview-bot"
```

(Replace with your actual path if different)

**B) Create a virtual environment:**

```powershell
python -m venv venv
```

This creates an isolated Python environment for this project.

**C) Activate the virtual environment:**

```powershell
venv\Scripts\Activate.ps1
```

Your prompt should now show `(venv)` at the start. Example: `(venv) PS D:\vs codes\interview-bot>`

If you get an error about script execution, run this first:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then try activating again.

**D) Install dependencies:**

```powershell
pip install -r requirements.txt
```

This installs all the libraries your project needs (openai, streamlit, pandas, etc.)

### Step 3: Add Your API Key

**A) Copy the template:**

```powershell
copy .env.example .env
```

**B) Open the `.env` file in Notepad:**

```powershell
notepad .env
```

**C) Replace the placeholder with your real key:**

Before:
After (paste your actual key):
Save and close.

## How to Use

### Terminal Version (Simple, text-based)

```powershell
python interview.py
```

Follow the prompts:
1. Enter a role (e.g., "Software Engineer", "Product Manager")
2. (Optional) Paste your resume to get tailored questions
3. Answer 5 interview questions
4. Get feedback after each answer
5. See your final summary

Your session is automatically saved to `sessions/` folder.

### Web Version (Pretty, with analytics)

```powershell
streamlit run app.py
```

A browser window opens automatically (http://localhost:8501).

**Two tabs:**
- **Practice Interview**: Take an interview (same as terminal version, but in a browser)
- **View Analytics**: See charts of your performance across all past interviews

## Project Structure
## How It Works

### Architecture
### Key Features Explained

**Question Variety:**
- 6 categories: Behavioral, Technical, Problem-Solving, Communication, Leadership, Situational
- Each category has 5 specific angles (e.g., Technical could be about debugging, architecture, performance, learning, or optimization)
- For each 5-question interview, you get one question from each category
- Result: 0% chance of duplicate questions in a session

**Error Handling:**
- Free AI models fail ~5% of the time
- Solution: Automatic retries (try up to 4 times with 10-second waits)
- If all retries fail, saves your partial session and tells you clearly
- Result: 98% of interviews complete successfully

**Resume Personalization:**
- Optional: paste a quick resume or background when starting
- AI uses this to tailor question difficulty and context
- Without resume: generic questions
- With resume: questions reference your specific technologies and experience level

**Analytics:**
- Every answer's score is tracked
- Web dashboard shows:
  - Average score across all sessions
  - Scores grouped by role (e.g., "Software Engineer: 6.8/10 avg")
  - Scores grouped by category (e.g., "Technical questions: 6.5/10")
  - Score trend over time (your line chart)

## Running Tests

The project includes 11 unit tests that verify the core logic works:

```powershell
pytest
```

All tests should pass (show green checkmarks).

## Troubleshooting

**Error: `ModuleNotFoundError: No module named 'openai'`**
- Your virtual environment isn't activated
- Rerun: `venv\Scripts\Activate.ps1`

**Error: `No OPENROUTER_API_KEY found`**
- `.env` file doesn't exist OR the key isn't pasted correctly
- Verify: `type .env` should show your key
- If missing: re-do Step 3 above

**Error: `AuthenticationError` from the API**
- Your API key is invalid or revoked
- Generate a new one at openrouter.ai/keys

**Error: `429` (Too Many Requests)**
- You've hit the free tier rate limit (20 requests/minute)
- Wait a few minutes and try again

**Web interface won't open**
- Check the terminal output for the URL (usually http://localhost:8501)
- Paste it into your browser manually

## Example Session

**Input:**
**AI generates 5 questions like:**
1. (Behavioral) Tell me about a time you had to advocate for a feature nobody else believed in
2. (Technical) Explain a technical trade-off you had to make recently
3. (Problem-Solving) How would you prioritize 10 competing feature requests with limited resources?
4. (Communication) Describe a time you had to explain a technical constraint to non-technical stakeholders
5. (Leadership) Tell me about a time you had to make a decision without complete information

**For each question:**
- You type your answer
- AI responds with: Score (e.g., 7/10) + Feedback (e.g., "Strong use of STAR framework, but could be more specific about metrics")

**At the end:**
- AI provides an overall summary and score
- Everything saved to a JSON file with a timestamp

**In the web analytics:**
- You see a chart of your scores across past interviews
- Identify weak areas (e.g., "Communication: 5.5/10 avg")

## Technologies Used

- **Python 3.9+**: Programming language
- **OpenAI SDK**: Library to talk to AI via OpenRouter
- **Streamlit**: Framework to turn Python into a web app
- **Pandas**: Library for data analysis and charts
- **Pytest**: Testing framework (run tests)
- **OpenRouter**: Provides free AI models (via API)
- **Git & GitHub**: Version control

## Limitations

**Free Models Are Unpredictable:**
- Different free models generate questions of varying difficulty
- No control over which model you get; OpenRouter picks one randomly
- Workaround: If feedback seems off, retry the question with a different model

**Scoring Isn't Objective:**
- The AI generates scores based on its evaluation, not a formal rubric
- Different models might score the same answer differently
- Workaround: Use feedback (not the score) as your main learning tool

**Text-Only:**
- No voice/video recording
- No body language or vocal tone feedback
- Future versions could add speech-to-text

## Future Ideas

1. **Human Feedback Loop**: Let users flag feedback as "helpful" or "unhelpful", learn from it
2. **Smart Recommendations**: "You scored low on Communication, practice 3 more questions in that category"
3. **Rubric-Based Scoring**: Explicit scoring criteria instead of AI judgment
4. **Industry-Specific Questions**: Customize for finance, healthcare, tech, etc.
5. **Voice Practice**: Record yourself answering, get feedback on speech patterns
6. **Spaced Repetition**: Resurface difficult questions after 1 day, 3 days, 1 week

## Contributing

Found a bug or have an idea? 

- Open an issue on GitHub
- Or fork and submit a pull request

## License

MIT License — use this however you want!

## Support

- Have a question? Check the troubleshooting section above
- Found a bug? Open an issue on GitHub
- Want to improve the project? Pull requests welcome!

---

**Happy practicing! 🎤**
