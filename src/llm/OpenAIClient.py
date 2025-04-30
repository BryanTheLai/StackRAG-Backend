# src/llm/OpenAIClient.py

import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI # Assuming you have openai library installed

class OpenAIClient:
    """Client for interacting with OpenAI's API, primarily for embeddings."""

    def __init__(self):
        """Initialize client with API key from environment."""
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
        self.embedding_model = "text-embedding-3-small" # Or "nomic-ai/nomic-embed-text-v1.5" if using Fireworks base_url

        print(f"Initialized OpenAI client with model: {self.embedding_model}")


    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Gets embeddings for a list of texts using the configured model.

        Args:
            texts: A list of strings to embed.

        Returns:
            A list of embedding vectors (list of floats).
        """
        response = self.client.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        embeddings = [data.embedding for data in response.data]

        return embeddings