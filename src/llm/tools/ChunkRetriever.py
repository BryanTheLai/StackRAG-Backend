from typing import Dict, Optional
import uuid
import json
import traceback
from src.llm.OpenAIClient import OpenAIClient
from src.storage.SupabaseService import SupabaseService
from src.enums import FinancialDocSpecificType

# Update tool declaration name and staticmethod to align with Pydantic AI expectations
RETRIEVE_CHUNKS_DECLARATION_DATA = {
    "name": "retrieve_chunks",
    "description": "Searches and retrieves relevant text chunks from the user's uploaded financial documents based on their query and optional filters like company name, document type, year range, or quarter. Always use this tool to find information before answering questions about the user's financial documents.",
    "parameters": {
        "type": "object",
        "properties": {
            "query_text": {"type": "string", "description": "The user's original question or a refined search query."},
            "match_count": {"type": "integer", "description": "Max initial chunks to identify relevant sections. Default 50. For broad queries (e.g., full year), a higher count (50-100) helps find diverse sections."},
            "doc_specific_type": {
                "type": "string",
                "description": f"Specific document type. Examples: {', '.join([item.value for item in FinancialDocSpecificType if item != FinancialDocSpecificType.UNKNOWN and item.value is not None])}.",
                "enum": [item.value for item in FinancialDocSpecificType if item != FinancialDocSpecificType.UNKNOWN and item.value is not None]
            },
            "company_name": {"type": "string", "description": "Company name to filter by."},
            "doc_year_start": {"type": "integer", "description": "Starting fiscal year."},
            "doc_year_end": {"type": "integer", "description": "Ending fiscal year."},
            "doc_quarter": {"type": "integer", "description": "Fiscal quarter (1-4)."},
            "report_date": {"type": "string", "description": "Report date filter in YYYY-MM-DD format."}
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
        supabase_service: SupabaseService,
        user_id: str, # This user_id is injected by the calling pipeline
    ):
        """
        Initializes the RetrievalService with necessary clients.

        Args:
            openai_client: An initialized OpenAIClient instance for embeddings.
            supabase_service: An initialized SupabaseService instance for database interaction.
            user_id: The ID of the user making the request.
        """
        if not isinstance(openai_client, OpenAIClient):
            raise TypeError("openai_client must be an instance of OpenAIClient") # Added type check
        if not isinstance(supabase_service, SupabaseService):
            raise TypeError("supabase_service must be an instance of SupabaseService") # Added type check
        self._openai_client = openai_client
        self._supabase_service = supabase_service
        self._user_id = user_id

    @staticmethod
    def get_tool_declaration_data() -> Dict:
        """
        Returns the tool declaration data for the retrieve_chunks tool.
        """
        return RETRIEVE_CHUNKS_DECLARATION_DATA

    def retrieve_chunks(
        self,
        query_text: str,
        match_count: int = 50, # This is now the initial match_count to find relevant sections
        doc_specific_type: Optional[str] = None,
        company_name: Optional[str] = None,
        doc_year_start: Optional[int] = None,
        doc_year_end: Optional[int] = None,
        doc_quarter: Optional[int] = None,
        report_date: Optional[str] = None
    ) -> str:
        """
        Retrieves relevant financial document chunks.
        First, it finds initial relevant chunks based on the query.
        Then, it fetches all chunks from the sections containing these initial chunks.
        """
        print(f"  RetrievalService.retrieve_chunks called with query: '{query_text}'")
        print(f"  User ID for retrieval: {self._user_id}")
        print(f"  Initial match_count for section identification: {match_count}")
        print(f"  Filters: Type={doc_specific_type}, Company={company_name}, YearStart={doc_year_start}, YearEnd={doc_year_end}, Qtr={doc_quarter}, Date={report_date}")

        try:
            # Corrected method name from get_embedding to get_embeddings
            # and adjusted to pass a list and expect a list of embeddings, taking the first one.
            embeddings_list = self._openai_client.get_embeddings([query_text])
            if not embeddings_list:
                raise ValueError("Embedding generation returned an empty list.")
            embedding = embeddings_list[0]
            print("  Query embedding generated.")
        except Exception as e:
            print(f"  Error generating embedding: {e}")
            return json.dumps({"error": "Failed to generate query embedding.", "details": str(e)})

        # Step 1: Call match_chunks to get initial relevant chunks and identify sections
        print(f"  Calling Supabase RPC 'match_chunks' to identify relevant sections with match_count={match_count}...")
        try:
            initial_response = self._supabase_service.client.rpc( # Changed to use self._supabase_service.client.rpc
                "match_chunks",
                {
                    "query_embedding": embedding,
                    "match_count": match_count, # Use the provided match_count for this initial step
                    "user_id": self._user_id,
                    "p_doc_specific_type": doc_specific_type,
                    "p_company_name": company_name,
                    "p_doc_year_start": doc_year_start,
                    "p_doc_year_end": doc_year_end,
                    "p_doc_quarter": doc_quarter,
                    "p_report_date": report_date,
                },
            ).execute()
            initial_chunks_data = initial_response.data
            print(f"  Retrieved {len(initial_chunks_data)} initial chunks for section identification.")
        except Exception as e:
            print(f"  Error calling 'match_chunks' RPC: {e}")
            return json.dumps({"error": "Failed to retrieve initial chunks.", "details": str(e)})

        if not initial_chunks_data:
            return json.dumps([]) # Return empty list if no initial chunks found

        # Step 2: Extract unique section_ids from these initial chunks
        section_ids = list(set(
            chunk['section_id'] for chunk in initial_chunks_data if chunk.get('section_id')
        ))

        if not section_ids:
            print("  No section_ids found in initial chunks. Returning initial chunks directly.")
            # If no section_ids, return the initially fetched chunks (already formatted)
            return json.dumps(initial_chunks_data, default=str)

        print(f"  Identified {len(section_ids)} unique section(s) from initial chunks: {section_ids}")

        # Step 3: Call a new RPC function 'get_chunks_for_sections' to fetch all chunks for these section_ids
        print(f"  Calling Supabase RPC 'get_chunks_for_sections' for {len(section_ids)} section(s)...")
        try:
            sections_response = self._supabase_service.client.rpc( # Changed to use self._supabase_service.client.rpc
                "get_chunks_for_sections",
                {
                    "p_section_ids": section_ids,
                    "p_user_id": self._user_id
                }
            ).execute()
            all_section_chunks_data = sections_response.data
            print(f"  Retrieved {len(all_section_chunks_data)} chunks from {len(section_ids)} identified sections.")
        except Exception as e:
            print(f"  Error calling 'get_chunks_for_sections' RPC: {e}")
            # Fallback: return initial chunks if fetching full sections fails
            print("  Falling back to returning initial chunks due to error.")
            return json.dumps(initial_chunks_data, default=str)

        # Add a null similarity_score to chunks from get_chunks_for_sections for consistency
        # as the original match_chunks provides it.
        for chunk in all_section_chunks_data:
            chunk.setdefault('similarity_score', None) # Or calculate if meaningful

        # Sort the final list of chunks for consistent output
        all_section_chunks_data.sort(key=lambda c: (
            c.get('document_filename', ''),
            c.get('section_id', ''),
            c.get('chunk_index', 0)
        ))
        
        print(f"  Returning {len(all_section_chunks_data)} total chunks as JSON result.")
        return json.dumps(all_section_chunks_data, default=str)