"""
Test suite for the AI Interview Practice Bot.

Run with: pytest
(from the project root, with the venv activated)

These tests avoid making real API calls -- the retry test uses a mocked
client so it runs instantly and does not burn your free-tier quota.
"""

import os
import sys
import json
import shutil
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import interview


class TestParseScore:
    def test_parses_standard_format(self):
        feedback = "Score: 7/10\nFeedback: Good answer overall."
        assert interview.parse_score(feedback) == 7

    def test_parses_double_digit_score(self):
        feedback = "Score: 10/10\nFeedback: Excellent."
        assert interview.parse_score(feedback) == 10

    def test_parses_with_extra_whitespace(self):
        feedback = "Score:   4 / 10  \nFeedback: Needs more detail."
        assert interview.parse_score(feedback) == 4

    def test_case_insensitive(self):
        feedback = "score: 6/10\nfeedback: Decent."
        assert interview.parse_score(feedback) == 6

    def test_returns_none_when_no_score_present(self):
        feedback = "This feedback has no score in it at all."
        assert interview.parse_score(feedback) is None


class TestSaveTranscript:
    def setup_method(self):
        self.original_dir = interview.SESSIONS_DIR
        interview.SESSIONS_DIR = "test_sessions_tmp"
        os.makedirs(interview.SESSIONS_DIR, exist_ok=True)

    def teardown_method(self):
        shutil.rmtree(interview.SESSIONS_DIR, ignore_errors=True)
        interview.SESSIONS_DIR = self.original_dir

    def test_saves_completed_session_correctly(self):
        transcript = [
            {"question": "Tell me about yourself.", "answer": "I am a developer.", "feedback": "Score: 8/10\nFeedback: Solid."}
        ]
        filepath = interview.save_transcript("Software Engineer", transcript, "Great job overall.", completed=True)

        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["role"] == "Software Engineer"
        assert data["completed"] is True
        assert data["num_questions_answered"] == 1
        assert data["summary"] == "Great job overall."
        assert data["transcript"][0]["question"] == "Tell me about yourself."

    def test_saves_partial_session_when_incomplete(self):
        transcript = [
            {"question": "Q1", "answer": "A1", "feedback": "Score: 5/10\nFeedback: OK."}
        ]
        filepath = interview.save_transcript("Data Analyst", transcript, summary=None, completed=False)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["completed"] is False
        assert data["summary"] is None
        assert data["num_questions_answered"] == 1

    def test_filename_includes_role_and_is_safe(self):
        filepath = interview.save_transcript("Product Manager", [], None, completed=False)
        filename = os.path.basename(filepath)
        assert "product-manager" in filename
        assert " " not in filename


class TestAskAiRetries:
    @patch("interview.client")
    @patch("interview.time.sleep", return_value=None)
    def test_succeeds_on_first_try(self, mock_sleep, mock_client):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Here is a question."
        mock_client.chat.completions.create.return_value = mock_response

        result = interview.ask_ai("some prompt")

        assert result == "Here is a question."
        assert mock_client.chat.completions.create.call_count == 1

    @patch("interview.client")
    @patch("interview.time.sleep", return_value=None)
    def test_retries_after_empty_response_then_succeeds(self, mock_sleep, mock_client):
        empty_response = MagicMock()
        empty_response.choices[0].message.content = None

        good_response = MagicMock()
        good_response.choices[0].message.content = "Finally, a real answer."

        mock_client.chat.completions.create.side_effect = [empty_response, good_response]

        result = interview.ask_ai("some prompt")

        assert result == "Finally, a real answer."
        assert mock_client.chat.completions.create.call_count == 2

    @patch("interview.client")
    @patch("interview.time.sleep", return_value=None)
    def test_raises_ai_service_error_after_max_retries(self, mock_sleep, mock_client):
        mock_client.chat.completions.create.side_effect = Exception("Simulated API failure")

        with pytest.raises(interview.AIServiceError):
            interview.ask_ai("some prompt")

        assert mock_client.chat.completions.create.call_count == 4
