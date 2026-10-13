"""
OpenRouter Client Adapter (Backward-Compatible).
Delegates to the production, TLS-verified LangChain LLM Factory.
"""

from typing import Optional
from fde_agent.llm import ask_ai as _secure_ask_ai


def ask_ai(prompt: str, max_tokens: Optional[int] = None) -> str:
    """
    Execute AI completion through the hardened LangChain OpenRouter client.
    Guarantees TLS verification and credit-exhaustion fallbacks.
    """
    return _secure_ask_ai(prompt, max_tokens=max_tokens)