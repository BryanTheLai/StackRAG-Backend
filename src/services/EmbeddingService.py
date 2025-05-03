# src/services/EmbeddingService.py

from typing import List, Dict, Any, Optional
from src.services.ChunkingService import ChunkData
from src.llm.OpenAIClient import OpenAIClient

class EmbeddingService:
    """
    Generates vector embeddings for text chunks using an embedding model.
    Prepares the text for embedding by augmenting it with relevant metadata.
    Adds the 'embedding' vector and 'embedding_model' to each chunk dictionary.
    """

    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """
        Initialize EmbeddingService with an OpenAI client.
        Uses default OpenAIClient if none provided.
        """
        # Use provided client or create a default one
        self.openai_client = openai_client or OpenAIClient()
        print(f"Initialized EmbeddingService using model: {self.openai_client.embedding_model}")

    def generate_embeddings(self, chunks_data: List[ChunkData]) -> List[ChunkData]:
        """
        Generates embeddings for a list of chunk data dictionaries.
        Augments chunk text with metadata before sending to the embedding model.
        Adds the 'embedding' vector and 'embedding_model' to each chunk dictionary.

        Args:
            chunks_data: A list of ChunkData dictionaries from the ChunkingService.

        Returns:
            The same list of ChunkData dictionaries, now with 'embedding' and
            'embedding_model' keys added to each dictionary.
            Returns the original list if no chunks are provided or on error.
        """
        if not chunks_data:
            print("No chunks provided for embedding.")
            return []

        print(f"Generating embeddings for {len(chunks_data)} chunks using model: {self.openai_client.embedding_model}...")

        # Prepare texts for the embedding model by augmenting with metadata
        texts_to_embed: List[str] = []
        # Store a mapping back to the original chunk_data index
        chunk_indices_map: List[int] = []

        for i, chunk in enumerate(chunks_data):
            # Construct the augmented text string using copied metadata
            # This format helps the embedding capture the context for retrieval
            # Using .get(key, default) to handle cases where metadata might be missing
            augmented_text = (
                f"Document Type: {chunk.get('doc_specific_type', 'Unknown')}. "
                f"Year: {chunk.get('doc_year', 'Unknown')}. "
                f"Quarter: {chunk.get('doc_quarter', 'Unknown')}. " # Use 'Unknown' or similar for None/null placeholder
                f"Company: {chunk.get('company_name', 'Unknown')}. "
                f"Section: {chunk.get('section_heading', 'Unknown Section')}. "
                f"Content: {chunk.get('chunk_text', '')}" # Ensure chunk_text exists, default to empty string
            )
            texts_to_embed.append(augmented_text)
            chunk_indices_map.append(i) # Map the index in texts_to_embed back to the original chunks_data index

        print(f"Prepared {len(texts_to_embed)} augmented texts for embedding.")

        # Get the embeddings from the OpenAI client
        # Bare bones: assume API call succeeds, minimal error handling
        try:
            # Call the get_embeddings method of the OpenAIClient
            embeddings_result = self.openai_client.get_embeddings(texts_to_embed)

            # Basic check: The number of returned embeddings should match the number of texts sent
            if len(embeddings_result) != len(texts_to_embed):
                 print(f"Warning: Embedding API returned {len(embeddings_result)} embeddings for {len(texts_to_embed)} texts. Expected count mismatch.")
                 # For bare-bones, we'll proceed with potentially partial results

            # Add the generated embeddings back to the original chunk data dictionaries
            # Assuming the order of embeddings in the response matches the order of input texts
            # Use min length in case of partial response
            valid_embeddings_count = min(len(embeddings_result), len(texts_to_embed))
            for i in range(valid_embeddings_count):
                original_chunk_index = chunk_indices_map[i]
                chunks_data[original_chunk_index]['embedding'] = embeddings_result[i]
                chunks_data[original_chunk_index]['embedding_model'] = self.openai_client.embedding_model

            print(f"Successfully added embeddings to {valid_embeddings_count} chunks.")
            return chunks_data
        except Exception as e:
             print(f"Error generating embeddings: {e}")
             # In a real system, you would handle this more robustly (e.g., retry, log, return specific error)
             return chunks_data # Return the original list, potentially without new 'embedding' keys