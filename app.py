"""
AI Interview Practice Bot -- Web UI (Version 2)
-------------------------------------------------
A Streamlit web interface wrapping the same core logic as interview.py
(question generation, feedback, scoring, transcript saving, retry/error
handling, and analytics). Run with:

    streamlit run app.py
"""

import streamlit as st
import interview
import pandas as pd

st.set_page_config(page_title="AI Interview Practice Bot", page_icon=":microphone:", layout="wide")


def init_state():
    defaults = {
        "phase": "role_input",
        "role": "",
        "resume": None,
        "question_num": 1,
        "current_question": None,
        "current_category": None,
        "categories": [],
        "asked_questions": [],
        "transcript": [],
        "summary": None,
        "error_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()


init_state()

st.title("AI Interview Practice Bot")
st.caption("Practice a 5-question mock interview and get AI feedback after each answer.")

sidebar = st.sidebar
with sidebar:
    st.subheader("Menu")
    page = st.radio("Select", ["Practice Interview", "View Analytics"], label_visibility="collapsed")


if page == "View Analytics":
    st.subheader("Analytics Dashboard")
    
    sessions = interview.load_all_sessions()
    
    if not sessions:
        st.info("No completed sessions yet. Start practicing to build your analytics!")
    else:
        analytics_data = []
        for session in sessions:
            if session.get("completed") and session.get("transcript"):
                for item in session.get("transcript", []):
                    score = interview.parse_score(item.get("feedback", ""))
                    if score:
                        analytics_data.append({
                            "role": session.get("role"),
                            "date": session.get("timestamp", "").split("T")[0],
                            "score": score,
                            "category": item.get("category"),
                        })
        
        if analytics_data:
            df = pd.DataFrame(analytics_data)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sessions", len(sessions))
            with col2:
                avg_score = df["score"].mean()
                st.metric("Average Score", f"{avg_score:.1f}/10")
            with col3:
                st.metric("Questions Answered", len(df))
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Score by Role")
                role_scores = df.groupby("role")["score"].agg(["mean", "count"]).reset_index()
                role_scores.columns = ["Role", "Average Score", "Count"]
                st.bar_chart(data=role_scores.set_index("Role")["Average Score"])
            
            with col2:
                st.subheader("Score by Category")
                cat_scores = df.groupby("category")["score"].mean().reset_index()
                cat_scores.columns = ["Category", "Average Score"]
                st.bar_chart(data=cat_scores.set_index("Category")["Average Score"])
            
            st.divider()
            st.subheader("Score Trend Over Time")
            trend = df.sort_values("date").groupby("date")["score"].mean().reset_index()
            trend.columns = ["Date", "Average Score"]
            st.line_chart(data=trend.set_index("Date"))
            
            st.divider()
            st.subheader("All Sessions")
            session_summary = []
            for session in sessions:
                if session.get("completed") and session.get("transcript"):
                    scores = [interview.parse_score(item.get("feedback", "")) for item in session.get("transcript", [])]
                    scores = [s for s in scores if s is not None]
                    avg = sum(scores) / len(scores) if scores else 0
                    session_summary.append({
                        "Date": session.get("timestamp", "").split("T")[0],
                        "Role": session.get("role"),
                        "Avg Score": f"{avg:.1f}",
                        "Questions": len(scores),
                    })
            
            if session_summary:
                st.dataframe(pd.DataFrame(session_summary), use_container_width=True)
        else:
            st.info("No completed sessions with scores yet.")


elif page == "Practice Interview":
    if st.session_state.phase == "role_input":
        st.subheader("What role are you practicing for?")
        role_input = st.text_input("e.g. Software Engineer, Data Analyst, Product Manager", key="role_field")
        
        st.subheader("(Optional) Your Background")
        st.caption("Paste a brief resume or background summary to get tailored questions. Leave blank for generic questions.")
        resume_input = st.text_area("Your background (optional)", key="resume_field", height=100)
        
        if st.button("Start Interview", type="primary", disabled=not role_input.strip()):
            st.session_state.role = role_input.strip()
            st.session_state.resume = resume_input.strip() if resume_input.strip() else None
            st.session_state.categories = interview.assign_categories(interview.NUM_QUESTIONS)
            st.session_state.phase = "interview"
            st.rerun()

    elif st.session_state.phase == "interview":
        role = st.session_state.role
        q_num = st.session_state.question_num
        category = st.session_state.categories[q_num - 1]
        resume = st.session_state.resume

        st.progress((q_num - 1) / interview.NUM_QUESTIONS)
        st.subheader(f"Question {q_num} of {interview.NUM_QUESTIONS} -- {role}")
        st.caption(f"Category: {category}")

        if st.session_state.current_question is None:
            try:
                with st.spinner("Generating question..."):
                    question = interview.generate_question(
                        role, q_num, st.session_state.asked_questions, category, resume
                    )
                st.session_state.current_question = question
                st.session_state.asked_questions.append(question)
            except interview.AIServiceError as e:
                st.session_state.error_message = str(e)
                st.session_state.phase = "error"
                st.rerun()

        st.write(f"**Interviewer:** {st.session_state.current_question}")

        answer = st.text_area("Your answer", key=f"answer_{q_num}", height=150)

        if st.button("Submit Answer", type="primary", disabled=not answer.strip()):
            try:
                with st.spinner("Getting feedback..."):
                    feedback = interview.get_feedback(role, st.session_state.current_question, answer.strip())

                st.session_state.transcript.append({
                    "question": st.session_state.current_question,
                    "answer": answer.strip(),
                    "feedback": feedback,
                    "category": category,
                })

                if q_num >= interview.NUM_QUESTIONS:
                    st.session_state.phase = "generating_summary"
                else:
                    st.session_state.question_num += 1
                    st.session_state.current_question = None

                st.rerun()

            except interview.AIServiceError as e:
                st.session_state.error_message = str(e)
                st.session_state.phase = "error"
                st.rerun()

        if st.session_state.transcript:
            st.divider()
            st.subheader("Feedback so far")
            for i, item in enumerate(reversed(st.session_state.transcript), 1):
                with st.expander(f"Q{len(st.session_state.transcript) - i + 1}: {item['question'][:60]}..."):
                    st.write(f"**Your answer:** {item['answer']}")
                    st.write(item["feedback"])

    elif st.session_state.phase == "generating_summary":
        try:
            with st.spinner("Generating your overall summary..."):
                summary = interview.generate_summary(st.session_state.role, st.session_state.transcript)
            st.session_state.summary = summary

            filepath = interview.save_transcript(
                st.session_state.role,
                st.session_state.transcript,
                summary,
                completed=True,
                resume=st.session_state.resume,
            )
            st.session_state.saved_filepath = filepath
            st.session_state.phase = "summary"
            st.rerun()

        except interview.AIServiceError as e:
            filepath = interview.save_transcript(
                st.session_state.role,
                st.session_state.transcript,
                summary=None,
                completed=False,
                resume=st.session_state.resume,
            )
            st.session_state.saved_filepath = filepath
            st.session_state.error_message = str(e)
            st.session_state.phase = "error"
            st.rerun()

    elif st.session_state.phase == "summary":
        st.success("Interview complete!")
        st.subheader("Overall Summary")
        st.write(st.session_state.summary)

        st.divider()
        st.subheader("Full Transcript")
        for i, item in enumerate(st.session_state.transcript, 1):
            with st.expander(f"Question {i}: {item['question']}"):
                st.write(f"**Your answer:** {item['answer']}")
                st.write(item["feedback"])

        st.caption(f"Session saved to: `{st.session_state.get('saved_filepath', 'sessions/')}`")

        if st.button("Start a New Interview"):
            reset_state()
            st.rerun()

    elif st.session_state.phase == "error":
        st.error(
            "Sorry, the AI service is unavailable right now (it was retried "
            "automatically several times). Your progress so far has been saved."
        )
        if st.session_state.get("saved_filepath"):
            st.caption(f"Partial session saved to: `{st.session_state.saved_filepath}`")

        with st.expander("Technical details"):
            st.code(st.session_state.error_message or "Unknown error")

        if st.button("Try Again"):
            reset_state()
            st.rerun()
