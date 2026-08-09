import os
import unittest
from unittest.mock import patch, MagicMock

from src.config.openai_config import DEFAULT_CHAT_MODEL as DEFAULT_OPENAI_MODEL
from src.config.gemini_config import DEFAULT_CHAT_MODEL as DEFAULT_GEMINI_MODEL
from src.llm.OpenAIClient import OpenAIClient
from src.services.FinancialDocParser import FinancialDocParser

class TestVisionAndChatConfig(unittest.TestCase):

    def test_default_chat_model_constants(self):
        self.assertEqual(DEFAULT_OPENAI_MODEL, "gpt-5.6-luna")
        self.assertEqual(DEFAULT_GEMINI_MODEL, "gemini-3.5-lite")

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-dummy-key",
        "OPENAI_BASE_URL": "https://api.fireworks.ai/inference/v1",
        "OPENAI_EMBEDDING_MODEL": "nomic-ai/nomic-embed-text-v1.5"
    })
    @patch("src.llm.OpenAIClient.OpenAI")
    def test_openai_client_custom_base_url(self, mock_openai_cls):
        client = OpenAIClient()
        self.assertEqual(client.base_url, "https://api.fireworks.ai/inference/v1")
        self.assertEqual(client.embedding_model, "nomic-ai/nomic-embed-text-v1.5")
        mock_openai_cls.assert_called_once_with(
            api_key="sk-dummy-key",
            base_url="https://api.fireworks.ai/inference/v1"
        )

    @patch.dict(os.environ, {
        "VISION_PROVIDER": "qwen",
        "VISION_MODEL": "qwen-3.7-plus",
        "VISION_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "VISION_API_KEY": "sk-qwen-key"
    })
    @patch("src.services.FinancialDocParser.OpenAI")
    def test_decoupled_vision_parser_qwen(self, mock_openai_cls):
        parser = FinancialDocParser()
        self.assertEqual(parser.vision_provider, "qwen")
        self.assertEqual(parser.vision_model, "qwen-3.7-plus")
        self.assertEqual(parser.vision_base_url, "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.assertEqual(parser.vision_api_key, "sk-qwen-key")
        mock_openai_cls.assert_called_once_with(
            api_key="sk-qwen-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

if __name__ == "__main__":
    unittest.main()
