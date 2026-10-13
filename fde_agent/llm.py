"""
Resilient LLM Client Factory powered by LangChain.
Provides TLS-verified, retry-hardened, and fallback-capable chat models.
"""

import logging
import re
from typing import Any, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from fde_agent.config import config

logger = logging.getLogger("fde_agent.llm")


class LLMFactory:
    """Factory for generating and invoking resilient LangChain Chat models."""

    @staticmethod
    def get_chat_model(
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> ChatOpenAI:
        """
        Create a configured LangChain ChatOpenAI instance pointing to OpenRouter/OpenAI.
        Guarantees TLS verification and proper timeouts.
        """
        selected_model = model_name or config.primary_model
        selected_temp = temperature if temperature is not None else config.temperature
        selected_tokens = max_tokens if max_tokens is not None else config.max_tokens
        selected_timeout = timeout if timeout is not None else config.request_timeout

        return ChatOpenAI(
            model=selected_model,
            openai_api_key=config.api_key,
            openai_api_base=config.base_url,
            temperature=selected_temp,
            max_tokens=selected_tokens,
            timeout=selected_timeout,
            max_retries=3,
        )

    @classmethod
    def invoke_with_fallback(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Execute an LLM prompt with automatic credit-exhaustion fallback (402).
        """
        current_model = config.primary_model
        tokens = max_tokens or config.max_tokens
        used_fallback = False

        messages: List[BaseMessage] = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))

        while True:
            try:
                llm = cls.get_chat_model(
                    model_name=current_model,
                    max_tokens=tokens,
                )
                response = llm.invoke(messages)
                content = response.content
                if not content or not str(content).strip():
                    raise ValueError("Model returned an empty response.")
                return str(content)

            except Exception as err:
                err_str = str(err)
                logger.warning("LLM invocation error with %s: %s", current_model, err_str)

                # Handle payment required (402) / insufficient credits
                if "402" in err_str or "credits" in err_str.lower():
                    if not used_fallback and config.fallback_model:
                        logger.warning(
                            "Credit limit reached for %s. Falling back to %s...",
                            current_model,
                            config.fallback_model,
                        )
                        current_model = config.fallback_model
                        used_fallback = True
                        tokens = max_tokens or config.max_tokens
                        continue

                    # Try reducing token window if specified in error
                    match = re.search(r"can only afford (\d+)", err_str)
                    if match:
                        affordable = int(match.group(1))
                        tokens = min(tokens // 2, affordable)
                    else:
                        tokens = tokens // 2

                    if tokens < 256:
                        raise RuntimeError(
                            f"LLM balance insufficient to afford minimum output tokens: {err}"
                        ) from err

                    logger.info("Retrying with reduced max_tokens: %d", tokens)
                    continue

                # Re-raise unexpected exceptions
                raise


def ask_ai(prompt: str, max_tokens: Optional[int] = None) -> str:
    """
    Backward-compatible entry point for legacy modules calling ask_ai().
    Uses TLS-verified, resilient LangChain invocation.
    """
    return LLMFactory.invoke_with_fallback(prompt, max_tokens=max_tokens)

