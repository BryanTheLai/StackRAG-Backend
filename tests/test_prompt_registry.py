import unittest
from src.prompts.prompt_registry import PromptRegistry, DEFAULT_PROMPT_VERSION

class TestPromptRegistry(unittest.TestCase):

    def test_default_prompt_version(self):
        active_vid = PromptRegistry.get_active_version_id()
        self.assertEqual(active_vid, DEFAULT_PROMPT_VERSION)
        self.assertEqual(active_vid, "v1.2.0-financial-rag")

    def test_get_prompt_version_info(self):
        info = PromptRegistry.get_prompt_version_info("v1.2.0-financial-rag")
        self.assertEqual(info["version"], "v1.2.0-financial-rag")
        self.assertIn("template_name", info)

    def test_fallback_prompt_version(self):
        info = PromptRegistry.get_prompt_version_info("non-existent-version")
        self.assertEqual(info["version"], DEFAULT_PROMPT_VERSION)

if __name__ == "__main__":
    unittest.main()

