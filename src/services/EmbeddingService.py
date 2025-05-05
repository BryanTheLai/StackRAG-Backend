# src/services/EmbeddingService.py

from typing import List, Dict, Any
from src.services.ChunkingService import ChunkData
from src.llm.OpenAIClient import OpenAIClient

class EmbeddingService:
    """
    Generates vector embeddings for text chunks.
    """

    def __init__(self, openai_client: OpenAIClient = None):
        """
        Initializes EmbeddingService.
        """
        self.openai_client = openai_client or OpenAIClient()
        print(f"Initialized EmbeddingService using model: {self.openai_client.embedding_model}")

    def generate_embeddings(self, chunks_data: List[ChunkData]) -> List[ChunkData]:
        """
        Generates embeddings for chunk data dictionaries.

        Args:
            chunks_data: List of chunk data.

        Returns:
            List of chunk data with embeddings.
        """
        if not chunks_data:
            print("No chunks provided for embedding.")
            return []

        print(f"Generating embeddings for {len(chunks_data)} chunks using model: {self.openai_client.embedding_model}...")

        texts_to_embed: List[str] = []
        chunk_indices_map: List[int] = []

        for i, chunk in enumerate(chunks_data):
            # Augment chunk text with metadata for better context
            augmented_text = (
                f"Document Type: {chunk.get('doc_specific_type', 'Unknown')}. "
                f"Year: {chunk.get('doc_year', 'Unknown')}. "
                f"Quarter: {chunk.get('doc_quarter', 'Unknown')}. "
                f"Company: {chunk.get('company_name', 'Unknown')}. "
                f"Section: {chunk.get('section_heading', 'Unknown Section')}. "
                f"Content: {chunk.get('chunk_text', '')}"
            )
            texts_to_embed.append(augmented_text)
            chunk_indices_map.append(i)

        print(f"Prepared {len(texts_to_embed)} augmented texts for embedding.")

        try:
            embeddings_result = self.openai_client.get_embeddings(texts_to_embed)

            if len(embeddings_result) != len(texts_to_embed):
                 print(f"Warning: Embedding API returned {len(embeddings_result)} embeddings for {len(texts_to_embed)} texts. Expected count mismatch.")

            valid_embeddings_count = min(len(embeddings_result), len(texts_to_embed))
            for i in range(valid_embeddings_count):
                original_chunk_index = chunk_indices_map[i]
                chunks_data[original_chunk_index]['embedding'] = embeddings_result[i]
                chunks_data[original_chunk_index]['embedding_model'] = self.openai_client.embedding_model

            print(f"Successfully added embeddings to {valid_embeddings_count} chunks.")
            return chunks_data
        except Exception as e:
             print(f"Error generating embeddings: {e}")
             return chunks_data