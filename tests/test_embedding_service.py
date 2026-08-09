import unittest
from unittest.mock import MagicMock
from src.services.EmbeddingService import EmbeddingService

class TestEmbeddingService(unittest.TestCase):

    def test_embedding_count_mismatch_raises_error(self):
        mock_openai = MagicMock()
        mock_openai.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_openai.embedding_model = "text-embedding-3-small"

        service = EmbeddingService(openai_client=mock_openai)
        chunks = [
            {"chunk_text": "Chunk 1 content"},
            {"chunk_text": "Chunk 2 content"}
        ]

        with self.assertRaises(RuntimeError):
            service.generate_embeddings(chunks)

if __name__ == "__main__":
    unittest.main()

