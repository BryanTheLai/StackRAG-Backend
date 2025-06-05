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

        # Initialize the OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            # base_url="https://api.fireworks.ai/inference/v1",
        )

        # Define the default embedding model
        self.embedding_model = EMBEDDING_MODEL # Or "nomic-ai/nomic-embed-text-v1.5" if using Fireworks base_url

        print(f"Initialized OpenAI client with model: {self.embedding_model}")


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