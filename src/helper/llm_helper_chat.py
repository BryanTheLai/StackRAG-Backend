import json
import traceback

from src.prompts.prompt_manager import PromptManager

# --- HELPER FUNCTION: Serialize conversation history for printing ---
def serialize_conversation_history(history: list) -> list:
    serializable_history = []
    for content_item in history:
        if isinstance(content_item, dict):
            serializable_history.append(content_item)
            continue
        item_dict = {"role": content_item.role, "parts": []}
        if hasattr(content_item, 'parts') and content_item.parts is not None:
            for part_item in content_item.parts:
                part_dict = {}
                if hasattr(part_item, 'text') and part_item.text is not None:
                    part_dict['text'] = part_item.text
                if hasattr(part_item, 'function_call') and part_item.function_call:
                    part_dict['function_call'] = {
                        "name": part_item.function_call.name,
                        "args": dict(part_item.function_call.args) if hasattr(part_item.function_call.args, 'items') else {}
                    }
                if hasattr(part_item, 'function_response') and part_item.function_response:
                    response_data = part_item.function_response.response
                    part_dict['function_response'] = {
                        "name": part_item.function_response.name,
                        "response": response_data
                    }
                if part_dict:
                    item_dict["parts"].append(part_dict)
        serializable_history.append(item_dict)
    return serializable_history

# --- HELPER FUNCTION: Format retrieved chunks for the LLM ---
def format_chunks_for_llm(retrieved_chunks_json: str) -> str:
    try:
        chunks = json.loads(retrieved_chunks_json)
        if not chunks:
            return "No specific information snippets were found to answer the question.\n"
        if isinstance(chunks, dict) and "error" in chunks:
             return f"Could not retrieve information snippets: {chunks['error']}\n"

        formatted_text = "Okay, I have retrieved the following information snippets for you:\n\n"
        for i, chunk_data in enumerate(chunks):
            snippet_num = i + 1
            doc_name = chunk_data.get("document_filename")
            if doc_name is None:
                 doc_name = chunk_data.get("filename", "Unknown Document")
                 print(f"  Warning: 'document_filename' missing from chunk_data, used fallback 'filename': {doc_name}")
            sec_id = chunk_data.get("section_id")
            if sec_id is None:
                 sec_id = chunk_data.get("id", "unknown_section_missing_from_rpc")
                 print(f"  Warning: 'section_id' missing from chunk_data, used fallback 'id': {sec_id}")
            sec_heading = chunk_data.get("section_heading", "N/A")
            chunk_text_content = chunk_data.get("chunk_text", "No content.")

            formatted_text += f"[Snippet {snippet_num}]\n"
            formatted_text += f"Source Document: {doc_name}\n"
            formatted_text += f"Source Section ID: {sec_id}\n"
            formatted_text += f"Source Section Heading: {sec_heading}\n"
            formatted_text += f"Content:\n{chunk_text_content}\n\n"
        return formatted_text
    except json.JSONDecodeError:
        print(f"Error decoding JSON in format_chunks_for_llm: {traceback.format_exc()}")
        return "Error: Could not parse the retrieved information snippets for formatting.\n"
    except Exception as e:
        print(f"An unexpected error occurred in format_chunks_for_llm: {e}\n{traceback.format_exc()}")
        return f"An unexpected error occurred while formatting snippets: {str(e)}\n"
    

# --- HELPER FUNCTION: Print Final Answer ---
def print_final_formatted_answer(answer_text: str):
    """Prints the final answer in a formatted block."""
    print("\n\n****************************************")
    print("--- Final Answer Text from Gemini ---")
    print("****************************************")
    print(answer_text)
    print("****************************************\n")

# --- PROMPT FUNCTION: Craft instructions for final answer + citation links ---
def create_final_answer_instructions(user_original_query: str, formatted_snippets_text: str, YOUR_APP_DOMAIN: str = "www.stackifier.com") -> str:
    instructions = PromptManager.get_prompt(
        "citation_answer", user_original_query = user_original_query,  formatted_snippets_text = formatted_snippets_text, YOUR_APP_DOMAIN = YOUR_APP_DOMAIN
    )
    return instructions