# src/services/EmbeddingService.py

from typing import List
from src.models.ingestion_models import ChunkData
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
                raise ValueError(
                    f"Embedding count mismatch: expected {len(texts_to_embed)}, got {len(embeddings_result)}"
                )

            for i, emb in enumerate(embeddings_result):
                original_chunk_index = chunk_indices_map[i]
                chunks_data[original_chunk_index]['embedding'] = emb
                chunks_data[original_chunk_index]['embedding_model'] = self.openai_client.embedding_model

            print(f"Successfully generated and assigned embeddings for all {len(chunks_data)} chunks.")
            return chunks_data
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            raise RuntimeError(f"Embedding generation failed: {str(e)}") from e