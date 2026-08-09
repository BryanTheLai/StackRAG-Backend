import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from src.config.openai_config import EMBEDDING_MODEL


class OpenAIClient:
    """Handles interactions with OpenAI API, primarily for embeddings."""

    def __init__(self):
        """Initializes client with API key from environment."""
        load_dotenv()

        self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

        self.base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")

        # Initialize the OpenAI client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url.rstrip("/")

        self.client = OpenAI(**client_kwargs)

        self.embedding_model = os.environ.get("OPENAI_EMBEDDING_MODEL", EMBEDDING_MODEL)



    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Gets embeddings for a list of texts.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors.
        """
        response = self.client.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        embeddings = [data.embedding for data in response.data]

        return embeddings