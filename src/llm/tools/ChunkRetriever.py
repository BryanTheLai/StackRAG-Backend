import uuid
import json
import traceback
from src.llm.OpenAIClient import OpenAIClient
from src.storage.SupabaseService import SupabaseService
from src.enums import FinancialDocSpecificType
from google.genai import types 

RETRIEVE_CHUNKS_DECLARATION_DATA = {
    "name": "retrieve_financial_chunks",
    "description": "Searches and retrieves relevant text chunks from the user's uploaded financial documents based on their query and optional filters like company name, document type, year range, or quarter. Always use this tool to find information before answering questions about the user's financial documents.",
    "parameters": {
        "type": "object",
        "properties": {
            "query_text": {"type": "string", "description": "The user's original question or a refined search query."},
            "match_count": {"type": "integer", "description": "Max chunks to return. Default 5."},
            "doc_specific_type": {
                "type": "string", 
                "description": f"Specific document type. Examples: {', '.join([item.value for item in FinancialDocSpecificType if item != FinancialDocSpecificType.UNKNOWN and item.value is not None])}.",
                "enum": [item.value for item in FinancialDocSpecificType if item != FinancialDocSpecificType.UNKNOWN and item.value is not None]
                },
            "company_name": {"type": "string", "description": "Company name to filter by."},
            "doc_year_start": {"type": "integer", "description": "Starting fiscal year."},
            "doc_year_end": {"type": "integer", "description": "Ending fiscal year."},
            "doc_quarter": {
                "type": "integer", 
                "description": "Fiscal quarter (1-4).",
                },
        },
        "required": ["query_text"]
    },
}

class RetrievalService:
    """
    Service responsible for retrieving relevant financial document chunks.
    Handles query embedding, Supabase RPC call, and result processing.
    """
    def __init__(
        self,
        openai_client: OpenAIClient,
        supabase_service: SupabaseService
    ):
        """
        Initializes the RetrievalService with necessary clients.

        Args:
            openai_client: An initialized OpenAIClient instance for embeddings.
            supabase_service: An initialized SupabaseService instance for database interaction.
        """
        if not isinstance(openai_client, OpenAIClient):
             raise TypeError("openai_client must be an instance of OpenAIClient")
        if not isinstance(supabase_service, SupabaseService):
             raise TypeError("supabase_service must be an instance of SupabaseService")
             
        self._openai_client = openai_client
        self._supabase_service = supabase_service

    @staticmethod
    def get_tool_declaration() -> types.Tool:
        """
        Returns the Gemini tool declaration for the retrieve_financial_chunks function.
        """
        return RETRIEVE_CHUNKS_DECLARATION_DATA

    def retrieve_chunks(
        self,
        query_text: str,
        user_id: str, # This user_id is injected by the calling pipeline
        match_count: int = 5,
        doc_specific_type: str = None,
        company_name: str = None,
        doc_year_start: int = None,
        doc_year_end: int = None,
        doc_quarter: int = None
    ) -> str:
        """
        Generates an embedding for the query and calls the Supabase RPC
        to find relevant chunks based on similarity and filters.

        Args:
            query_text: The user's question or search query.
            user_id: The authenticated user's ID (UUID string).
            match_count: The maximum number of chunks to return.
            doc_specific_type: Filter by specific document type.
            company_name: Filter by company name.
            doc_year_start: Filter by fiscal year start.
            doc_year_end: Filter by fiscal year end.
            doc_quarter: Filter by fiscal quarter (1-4).

        Returns:
            A JSON string representing the list of retrieved chunks, or an error JSON string.
            Returns JSON string to match the expected output format for Gemini tool calls.
        """
        print(f"\n--- Executing RetrievalService.retrieve_chunks ---")
        print(f"  Query: '{query_text}'")
        print(f"  User ID for retrieval: {user_id}")
        print(f"  Filters: Type={doc_specific_type}, Company={company_name}, Year={doc_year_start}-{doc_year_end}, Qtr={doc_quarter}")

        try:
            # 1. Generate Embedding for the query
            query_embedding_list = self._openai_client.get_embeddings([query_text])
            if not query_embedding_list:
                print(f"  Error: Failed to generate query embedding.")
                return json.dumps({"error": "Failed to generate query embedding."})
            query_embedding = query_embedding_list[0]
            print(f"  Query embedding generated.")

            # 2. Call Supabase RPC 'match_chunks'
            print(f"  Calling Supabase RPC 'match_chunks'...")
            # Use the supabase_client directly from the SupabaseService instance
            response = self._supabase_service.client.rpc(
                'match_chunks',
                {
                    'query_embedding': query_embedding,
                    'match_count': match_count,
                    'user_id': user_id, # Pass the authenticated user_id to the RPC
                    'p_doc_specific_type': doc_specific_type,
                    'p_company_name': company_name,
                    'p_doc_year_start': doc_year_start,
                    'p_doc_year_end': doc_year_end,
                    'p_doc_quarter': doc_quarter
                }
            ).execute()

            # 3. Process RPC Response
            if response.data is not None:
                print(f"  Retrieved {len(response.data)} chunks from Supabase.")
                processed_data = []
                for chunk_dict in response.data:
                    processed_chunk = {}
                    for key, value in chunk_dict.items():
                        if isinstance(value, uuid.UUID):
                            processed_chunk[key] = str(value)
                        else:
                            processed_chunk[key] = value
                    # Ensure expected keys are present, adding defaults if missing
                    processed_chunk['document_filename'] = processed_chunk.get('document_filename', 'RPC_Missing_Doc_Name')
                    # Use chunk id as fallback for section_id if missing
                    processed_chunk['section_id'] = processed_chunk.get('section_id', str(processed_chunk.get('id', 'RPC_Missing_Section_ID')))
                    processed_chunk['chunk_text'] = processed_chunk.get('chunk_text', 'Chunk text missing from RPC.')
                    processed_chunk['section_heading'] = processed_chunk.get('section_heading', 'Section heading missing from RPC.')
                    
                    processed_data.append(processed_chunk)

                result_json_string = json.dumps(processed_data, indent=2)
                print(f"  Returning JSON result ({len(result_json_string)} chars, first 500 for brevity):\n{result_json_string[:500]}...")
                return result_json_string
            elif hasattr(response, 'error') and response.error:
                 error_msg = f"Supabase RPC 'match_chunks' error: {response.error.message if hasattr(response.error, 'message') else response.error}"
                 print(f"  Error: {error_msg}")
                 return json.dumps({"error": error_msg})
            else:
                # Handle cases where data is None and there's no explicit error object
                print("  Received unexpected empty/none response structure from Supabase RPC 'match_chunks'.")
                return json.dumps({"error": "Unexpected empty response from Supabase RPC."})

        except Exception as e:
            # Catch any other unexpected errors during the process
            print(f"An unexpected error occurred during chunk retrieval: {str(e)}\n{traceback.format_exc()}")
            return json.dumps({"error": f"An unexpected error occurred during chunk retrieval: {str(e)}"})