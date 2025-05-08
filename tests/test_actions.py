import pytest
from unittest.mock import patch, MagicMock
from actions.actions import ActionTopicHandler
import wikipedia


class TestActionTopicHandler:
    def setup_method(self):
        self.dispatcher = MagicMock()
        self.tracker = MagicMock()
        self.domain = {"responses": {}}
        self.action = ActionTopicHandler()

    def test_name(self):
        """Teszteli az action_topic_handler nevét."""
        assert self.action.name() == "action_topic_handler"

    @pytest.mark.asyncio
    @patch('actions.actions.call_llm')
    @patch('actions.actions.logger')
    async def test_run_no_topics_success(self, mock_logger, mock_call_llm):
        """Teszteli a run metódust, ha nincs téma, és az LLM sikeresen válaszol."""
        # Beallitjuk a tracker mockot
        self.tracker.latest_message = {
            'entities': [],  # Nincs topic entitas
            'text': "What is AI?"
        }
        mock_call_llm.return_value = "AI is artificial intelligence."

        # Futtatjuk az akciot
        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        # Ellenorizzuk az eredmenyeket
        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "What is AI?", [])
        mock_logger.info.assert_any_call("LLM response: %s", "AI is artificial intelligence.")
        self.dispatcher.utter_message.assert_any_call(
            text="You're asking about 'What is AI?'. Let me try to answer based on an external source..."
        )
        self.dispatcher.utter_message.assert_any_call(text="AI is artificial intelligence.")
        mock_call_llm.assert_called_once_with("What is AI?")

    @pytest.mark.asyncio
    @patch('actions.actions.call_llm')
    @patch('actions.actions.logger')
    async def test_run_no_topics_empty_response(self, mock_logger, mock_call_llm):
        """Teszteli a run metódust, ha nincs téma, és az LLM üres választ ad."""
        self.tracker.latest_message = {
            'entities': [],
            'text': "What is AI?"
        }
        mock_call_llm.return_value = ""

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "What is AI?", [])
        mock_logger.error.assert_called_once_with(
            "LLM returned empty response for user message: %s", "What is AI?"
        )
        self.dispatcher.utter_message.assert_any_call(
            text="You're asking about 'What is AI?'. Let me try to answer based on an external source..."
        )
        self.dispatcher.utter_message.assert_any_call(text="Sorry, I couldn't generate a useful answer.")
        mock_call_llm.assert_called_once_with("What is AI?")

    @pytest.mark.asyncio
    @patch('actions.actions.call_llm')
    @patch('actions.actions.logger')
    async def test_run_no_topics_llm_error(self, mock_logger, mock_call_llm):
        """Teszteli a run metódust, ha nincs téma, és az LLM hibát dob."""
        self.tracker.latest_message = {
            'entities': [],
            'text': "What is AI?"
        }
        mock_call_llm.side_effect = Exception("LLM failed")

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "What is AI?", [])
        mock_logger.error.assert_called_once_with(
            "LLM error for user message: %s | Error: %s", "What is AI?", "LLM failed"
        )
        self.dispatcher.utter_message.assert_any_call(
            text="You're asking about 'What is AI?'. Let me try to answer based on an external source..."
        )
        self.dispatcher.utter_message.assert_any_call(text="An error occurred while using the AI model.")
        mock_call_llm.assert_called_once_with("What is AI?")

    @pytest.mark.asyncio
    @patch('actions.actions.logger')
    async def test_run_one_topic_with_utter(self, mock_logger):
        """Teszteli a run metódust, ha egy téma van, és van hozzá utter."""
        self.tracker.latest_message = {
            'entities': [{'entity': 'topic', 'value': 'AI'}],
            'text': "Tell me about AI"
        }
        self.domain = {
            "responses": {
                "utter_ai": [{"text": "AI is artificial intelligence."}]
            }
        }

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "Tell me about AI", ['AI'])
        mock_logger.info.assert_any_call("Utter response used: %s", "utter_ai")
        self.dispatcher.utter_message.assert_any_call(text="Let me tell you about AI...")
        self.dispatcher.utter_message.assert_any_call(response="utter_ai")

    @pytest.mark.asyncio
    @patch('wikipedia.summary')
    @patch('actions.actions.logger')
    async def test_run_one_topic_no_utter_wiki_success(self, mock_logger, mock_wiki_summary):
        """Teszteli a run metódust, ha egy téma van, nincs utter, de a Wikipédia sikeres."""
        self.tracker.latest_message = {
            'entities': [{'entity': 'topic', 'value': 'AI'}],
            'text': "Tell me about AI"
        }
        self.domain = {"responses": {}}
        mock_wiki_summary.return_value = "AI is artificial intelligence."

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "Tell me about AI", ['AI'])
        mock_logger.info.assert_any_call("Searching Wikipedia for topic: %s", "AI")
        mock_logger.info.assert_any_call("Wikipedia summary returned for topic: %s", "AI")
        self.dispatcher.utter_message.assert_any_call(text="AI is artificial intelligence.")
        mock_wiki_summary.assert_called_once_with("AI", sentences=2)

    @pytest.mark.asyncio
    @patch('wikipedia.summary')
    @patch('actions.actions.logger')
    async def test_run_one_topic_wiki_disambiguation_error(self, mock_logger, mock_wiki_summary):
        """Teszteli a run metódust, ha egy téma van, és a Wikipédia disambiguation hibát dob."""
        self.tracker.latest_message = {
            'entities': [{'entity': 'topic', 'value': 'AI'}],
            'text': "Tell me about AI"
        }
        self.domain = {"responses": {}}
        mock_wiki_summary.side_effect = wikipedia.exceptions.DisambiguationError("AI", ["option1", "option2"])

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "Tell me about AI", ['AI'])
        mock_logger.info.assert_any_call("Searching Wikipedia for topic: %s", "AI")
        mock_logger.error.assert_called_once_with(
            "Wikipedia DisambiguationError for topic: %s | User message: %s | Error: %s",
            "AI", "Tell me about AI", '"AI" may refer to: \noption1\noption2'
        )
        self.dispatcher.utter_message.assert_any_call(text="That topic is ambiguous. Could you be more specific?")
        mock_wiki_summary.assert_called_once_with("AI", sentences=2)

    @pytest.mark.asyncio
    @patch('wikipedia.summary')
    @patch('actions.actions.logger')
    async def test_run_one_topic_wiki_page_error(self, mock_logger, mock_wiki_summary):
        """Teszteli a run metódust, ha egy téma van, és a Wikipédia page error-t dob."""
        self.tracker.latest_message = {
            'entities': [{'entity': 'topic', 'value': 'NonexistentTopic'}],
            'text': "Tell me about NonexistentTopic"
        }
        self.domain = {"responses": {}}
        mock_wiki_summary.side_effect = wikipedia.exceptions.PageError("NonexistentTopic")

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "Tell me about NonexistentTopic", ['NonexistentTopic'])
        mock_logger.info.assert_any_call("Searching Wikipedia for topic: %s", "NonexistentTopic")
        mock_logger.error.assert_called_once_with(
            "Wikipedia PageError for topic: %s | User message: %s | Error: Page not found",
            "NonexistentTopic", "Tell me about NonexistentTopic"
        )
        self.dispatcher.utter_message.assert_any_call(text="I couldn't find a Wikipedia page for that topic.")
        mock_wiki_summary.assert_called_once_with("NonexistentTopic", sentences=2)

    @pytest.mark.asyncio
    @patch('wikipedia.summary')
    @patch('actions.actions.logger')
    async def test_run_one_topic_wiki_other_error(self, mock_logger, mock_wiki_summary):
        """Teszteli a run metódust, ha egy téma van, és a Wikipédia egyéb hibát dob."""
        self.tracker.latest_message = {
            'entities': [{'entity': 'topic', 'value': 'AI'}],
            'text': "Tell me about AI"
        }
        self.domain = {"responses": {}}
        mock_wiki_summary.side_effect = Exception("Some error")

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "Tell me about AI", ['AI'])
        mock_logger.info.assert_any_call("Searching Wikipedia for topic: %s", "AI")
        mock_logger.error.assert_called_once_with(
            "Wikipedia error for topic: %s | User message: %s | Error: %s",
            "AI", "Tell me about AI", "Some error"
        )
        self.dispatcher.utter_message.assert_any_call(text="An unexpected error occurred while searching Wikipedia.")
        mock_wiki_summary.assert_called_once_with("AI", sentences=2)

    @pytest.mark.asyncio
    @patch('actions.actions.logger')
    async def test_run_multiple_topics_with_utter(self, mock_logger):
        """Teszteli a run metódust, ha több téma van, és van hozzájuk utter."""
        self.tracker.latest_message = {
            'entities': [{'entity': 'topic', 'value': 'AI'}, {'entity': 'topic', 'value': 'ML'}],
            'text': "Tell me about AI and ML"
        }
        self.domain = {
            "responses": {
                "utter_ai_ml": [{"text": "AI and ML are related fields."}]
            }
        }

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "Tell me about AI and ML", ['AI', 'ML'])
        mock_logger.info.assert_any_call("Utter response used: %s", "utter_ai_ml")
        self.dispatcher.utter_message.assert_any_call(response="utter_ai_ml")

    @pytest.mark.asyncio
    @patch('actions.actions.call_llm')
    @patch('actions.actions.logger')
    async def test_run_multiple_topics_no_utter_llm_success(self, mock_logger, mock_call_llm):
        """Teszteli a run metódust, ha több téma van, nincs utter, de az LLM sikeresen válaszol."""
        self.tracker.latest_message = {
            'entities': [{'entity': 'topic', 'value': 'AI'}, {'entity': 'topic', 'value': 'ML'}],
            'text': "Tell me about AI and ML"
        }
        self.domain = {"responses": {}}
        mock_call_llm.return_value = "AI and ML are related fields."

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "Tell me about AI and ML", ['AI', 'ML'])
        mock_logger.info.assert_any_call("LLM response: %s", "AI and ML are related fields.")
        self.dispatcher.utter_message.assert_any_call(
            text="You're asking about AI and ML. Let me try to answer based on an external source..."
        )
        self.dispatcher.utter_message.assert_any_call(text="AI and ML are related fields.")
        mock_call_llm.assert_called_once_with("Tell me about AI and ML")

    @pytest.mark.asyncio
    @patch('actions.actions.call_llm')
    @patch('actions.actions.logger')
    async def test_run_multiple_topics_llm_empty_response(self, mock_logger, mock_call_llm):
        """Teszteli a run metódust, ha több téma van, és az LLM üres választ ad."""
        self.tracker.latest_message = {
            'entities': [{'entity': 'topic', 'value': 'AI'}, {'entity': 'topic', 'value': 'ML'}],
            'text': "Tell me about AI and ML"
        }
        self.domain = {"responses": {}}
        mock_call_llm.return_value = ""

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "Tell me about AI and ML", ['AI', 'ML'])
        mock_logger.error.assert_called_once_with(
            "LLM returned empty response for user message: %s", "Tell me about AI and ML"
        )
        self.dispatcher.utter_message.assert_any_call(
            text="You're asking about AI and ML. Let me try to answer based on an external source..."
        )
        self.dispatcher.utter_message.assert_any_call(text="Sorry, I couldn't generate a useful answer.")
        mock_call_llm.assert_called_once_with("Tell me about AI and ML")

    @pytest.mark.asyncio
    @patch('actions.actions.call_llm')
    @patch('actions.actions.logger')
    async def test_run_multiple_topics_llm_error(self, mock_logger, mock_call_llm):
        """Teszteli a run metódust, ha több téma van, és az LLM hibát dob."""
        self.tracker.latest_message = {
            'entities': [{'entity': 'topic', 'value': 'AI'}, {'entity': 'topic', 'value': 'ML'}],
            'text': "Tell me about AI and ML"
        }
        self.domain = {"responses": {}}
        mock_call_llm.side_effect = Exception("LLM failed")

        result = await self.action.run(self.dispatcher, self.tracker, self.domain)

        assert result == []
        mock_logger.info.assert_any_call("User message: %s | Detected topics: %s", "Tell me about AI and ML", ['AI', 'ML'])
        mock_logger.error.assert_called_once_with(
            "LLM error for user message: %s | Error: %s", "Tell me about AI and ML", "LLM failed"
        )
        self.dispatcher.utter_message.assert_any_call(
            text="You're asking about AI and ML. Let me try to answer based on an external source..."
        )
        self.dispatcher.utter_message.assert_any_call(text="An error occurred while using the AI model.")
        mock_call_llm.assert_called_once_with("Tell me about AI and ML")


if __name__ == '__main__':
    pytest.main([__file__])
