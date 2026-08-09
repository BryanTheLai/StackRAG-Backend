from typing import Dict, Any, Optional

PROMPT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "v1.0.0": {
        "version": "v1.0.0",
        "description": "Initial legacy prompt template with tag formatting rules.",
        "template_name": "chat_system_prompt.j2",
    },
    "v1.2.0-financial-rag": {
        "version": "v1.2.0-financial-rag",
        "description": "Versioned evidence-first financial prompt with untrusted context isolation and claim-grounded citation rules.",
        "template_name": "chat_system_prompt.j2",
    }
}

DEFAULT_PROMPT_VERSION = "v1.2.0-financial-rag"

class PromptRegistry:
    """
    Registry for versioned system prompts and regression snapshots.
    """

    @staticmethod
    def get_prompt_version_info(version_id: Optional[str] = None) -> Dict[str, Any]:
        vid = version_id or DEFAULT_PROMPT_VERSION
        return PROMPT_REGISTRY.get(vid, PROMPT_REGISTRY[DEFAULT_PROMPT_VERSION])

    @staticmethod
    def get_active_version_id() -> str:
        return DEFAULT_PROMPT_VERSION
