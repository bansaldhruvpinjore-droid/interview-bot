"""
AI Interview Practice Bot -- Web UI (Version 2)
-------------------------------------------------
A Streamlit web interface wrapping the same core logic as interview.py
(question generation, feedback, scoring, transcript saving, retry/error
handling). Run with:

    streamlit run app.py
"""

import streamlit as st
import interview

st.set_page_config(page_title="AI Interview Practice Bot", page_icon=":microphone:", layout="centered")


def init_state():
    defaults = {
        "phase": "role_input",
        "role": "",
        "question_num": 1,
        "current_question": None,
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


if st.session_state.phase == "role_input":
    st.subheader("What role are you practicing for?")
    role_input = st.text_input("e.g. Software Engineer, Data Analyst, Product Manager", key="role_field")

    if st.button("Start Interview", type="primary", disabled=not role_input.strip()):
        st.session_state.role = role_input.strip()
        st.session_state.phase = "interview"
        st.rerun()


elif st.session_state.phase == "interview":
    role = st.session_state.role
    q_num = st.session_state.question_num

    st.progress((q_num - 1) / interview.NUM_QUESTIONS)
    st.subheader(f"Question {q_num} of {interview.NUM_QUESTIONS} -- {role}")

    if st.session_state.current_question is None:
        try:
            with st.spinner("Generating question..."):
                question = interview.generate_question(
                    role, q_num, st.session_state.asked_questions
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
